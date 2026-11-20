from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.ids import new_uuid
from app.core.rls import set_request_context
from app.core.security import hash_password
from app.models.audit import AuditLog
from app.models.organization import Organization, OrganizationMembership
from app.models.user import User
from app.modules.accounting.models import (
    AccountingDocumentMap,
    AccountingPeriod,
    Expense,
    ExpenseLine,
    JournalEntry,
    JournalLine,
)
from app.modules.accounting.service import seed_books
from app.modules.audit.models import OutboxEvent
from app.modules.authorization.catalog import build_role_seed
from app.modules.authorization.models import Permission, UserPermissionOverride
from app.modules.authorization.service import add_membership, assign_role
from app.modules.catalogue.models import Product, ProductCategory, ProductPrice, ProductVariant
from app.modules.catalogue.models import UnitOfMeasure
from app.modules.crm.models import Customer
from app.modules.demo.constants import (
    BRANCHES,
    CATEGORIES,
    DEMO_LEGAL_NAME,
    DEMO_MONTHLY_EXPENSES,
    DEMO_MONTHLY_REVENUE,
    DEMO_ORG_NAME,
    DEMO_ROLES,
    DEMO_SLUG,
    SCALE_COMPACT,
    SCALE_FULL,
)
from app.modules.inventory.models import StockBalance, StockMovement
from app.modules.payroll.models import Employee
from app.modules.purchasing.models import PurchaseOrder, PurchaseOrderItem, Supplier
from app.modules.sales.models import Payment, Sale, SaleItem
from app.modules.tenancy.models import OrganizationSettings, Warehouse
from app.modules.tenancy.service import create_branch, create_organization, list_warehouses
from app.core.context import TenantContext


def _scale(compact: bool) -> dict[str, int]:
    return dict(SCALE_COMPACT if compact else SCALE_FULL)


def _money(value: int | float | Decimal) -> Decimal:
    return Decimal(str(value)).quantize(Decimal("0.0001"))


def _owner_ctx(user_id: UUID, org_id: UUID, membership_id: UUID) -> TenantContext:
    return TenantContext(
        user_id=user_id,
        organization_id=org_id,
        membership_id=membership_id,
        branch_id=None,
        permissions=frozenset({"users.manage", "branches.manage", "org.settings"}),
        is_platform_admin=False,
        access_all_branches=True,
        branch_ids=frozenset(),
        is_owner=True,
    )


async def find_demo_org(session: AsyncSession, *, owner_id: UUID | None = None) -> Organization | None:
    if owner_id is not None:
        await set_request_context(session, user_id=owner_id, organization_id=None)
        return await session.scalar(
            select(Organization)
            .join(
                OrganizationMembership,
                OrganizationMembership.organization_id == Organization.id,
            )
            .where(
                Organization.name == DEMO_ORG_NAME,
                OrganizationMembership.user_id == owner_id,
                OrganizationMembership.status == "active",
            )
            .order_by(Organization.created_at.desc())
        )
    row = await session.scalar(
        select(Organization)
        .join(OrganizationSettings, OrganizationSettings.organization_id == Organization.id)
        .where(OrganizationSettings.settings.contains({"demo_key": DEMO_SLUG}))
    )
    return row


async def ensure_demo_users(session: AsyncSession) -> dict[str, User]:
    password_hash = hash_password("demo-local-only-not-for-login")
    now = datetime.now(UTC)
    users: dict[str, User] = {}
    for spec in DEMO_ROLES:
        user = await session.scalar(select(User).where(User.email == spec["email"]))
        if user is None:
            user = User(
                id=new_uuid(),
                email=spec["email"],
                password_hash=password_hash,
                full_name=spec["full_name"],
                email_verified_at=now,
                is_active=True,
            )
            session.add(user)
            await session.flush()
        else:
            user.full_name = spec["full_name"]
            user.email_verified_at = user.email_verified_at or now
            user.is_active = True
        users[spec["key"]] = user
    return users


async def wipe_demo_org(session: AsyncSession, org: Organization, actor_id: UUID) -> None:
    await set_request_context(session, user_id=actor_id, organization_id=org.id)
    await session.execute(delete(AuditLog).where(AuditLog.organization_id == org.id))
    await session.execute(delete(Organization).where(Organization.id == org.id))
    await session.flush()
    await set_request_context(session, user_id=actor_id, organization_id=None)


async def seed_mwamba(session: AsyncSession, *, compact: bool, reset: bool = False) -> Organization:
    users = await ensure_demo_users(session)
    owner = users["owner"]
    existing = await find_demo_org(session, owner_id=owner.id)
    if existing is not None and not reset:
        return existing
    if existing is not None and reset:
        await wipe_demo_org(session, existing, owner.id)

    await set_request_context(session, user_id=owner.id, organization_id=None)
    org, membership, first_branch, _warehouse = await create_organization(
        session,
        owner,
        name=DEMO_ORG_NAME,
        legal_name=DEMO_LEGAL_NAME,
        roles_payload=build_role_seed(),
        industry_code="general",
        timezone="Africa/Lusaka",
        base_currency_code="ZMW",
        country_code="ZM",
        first_branch={"code": BRANCHES[0][0], "name": BRANCHES[0][1]},
        first_warehouse={"code": f"{BRANCHES[0][0]}-WH", "name": f"{BRANCHES[0][1]} warehouse"},
    )
    if first_branch is None:
        raise RuntimeError("Demo organisation is missing a home branch")
    ctx = TenantContext(
        user_id=owner.id,
        organization_id=org.id,
        membership_id=membership.id,
        branch_id=first_branch.id,
        permissions=frozenset({"users.manage", "branches.manage", "org.settings", "org.manage"}),
        is_platform_admin=False,
        access_all_branches=True,
        branch_ids=frozenset(),
        is_owner=True,
    )
    await seed_books(session, ctx, currency="ZMW")
    settings_row = await session.scalar(
        select(OrganizationSettings).where(OrganizationSettings.organization_id == org.id)
    )
    payload = dict(settings_row.settings) if settings_row and isinstance(settings_row.settings, dict) else {}
    payload.update(
        {
            "demo_key": DEMO_SLUG,
            "is_demo": True,
            "demo_access": {"roles_explored": [], "modules_visited": []},
        }
    )
    if settings_row is None:
        session.add(OrganizationSettings(organization_id=org.id, settings=payload))
    else:
        settings_row.settings = payload

    branches = [first_branch]
    for code, name, _city in BRANCHES[1:]:
        branch = await create_branch(
            session, ctx, code=code, name=name, phone=None, create_default_warehouse=True
        )
        branches.append(branch)

    for spec in DEMO_ROLES:
        if spec["key"] == "owner":
            continue
        view = await add_membership(
            session,
            ctx,
            email=spec["email"],
            role_code=spec["role_codes"][0],
            access_all_branches=True,
            branch_ids=[],
        )
        for extra_role in spec["role_codes"][1:]:
            await assign_role(session, ctx, view.id, extra_role)
        for code in spec["extra_allows"]:
            permission = await session.scalar(select(Permission).where(Permission.code == code))
            if permission is None:
                continue
            session.add(
                UserPermissionOverride(
                    organization_id=org.id,
                    membership_id=view.id,
                    permission_id=permission.id,
                    effect="allow",
                )
            )

    await _seed_operational(session, org.id, owner.id, branches, compact=compact)
    await session.flush()
    return org


async def _seed_operational(
    session: AsyncSession,
    org_id: UUID,
    actor_id: UUID,
    branches: list,
    *,
    compact: bool,
) -> None:
    counts = _scale(compact)
    uom = await session.scalar(select(UnitOfMeasure).where(UnitOfMeasure.organization_id == org_id))
    if uom is None:
        raise RuntimeError("Demo organisation is missing a unit of measure")
    warehouses = list(
        await session.scalars(select(Warehouse).where(Warehouse.organization_id == org_id))
    )
    if not warehouses:
        warehouses = []
        for branch in branches:
            warehouses.extend(await list_warehouses(session, _owner_ctx(actor_id, org_id, new_uuid()), branch_id=branch.id))

    period = await session.scalar(
        select(AccountingPeriod)
        .where(AccountingPeriod.organization_id == org_id)
        .order_by(AccountingPeriod.starts_on.desc())
    )
    accounts = {
        row.map_key: row.account_id
        for row in await session.scalars(
            select(AccountingDocumentMap).where(AccountingDocumentMap.organization_id == org_id)
        )
    }
    cash_id = accounts["cash"]
    revenue_id = accounts["revenue"]
    opex_id = accounts["expense"]
    inventory_id = accounts["inventory"]
    cogs_id = accounts["cogs"]
    if period is None:
        raise RuntimeError("Demo organisation is missing an accounting period")

    categories: list[ProductCategory] = []
    for name in CATEGORIES:
        row = ProductCategory(
            id=new_uuid(),
            organization_id=org_id,
            name=name,
            path=f"/{name.lower().replace(' ', '-')}",
            is_active=True,
        )
        categories.append(row)
    session.add_all(categories)
    await session.flush()

    products: list[Product] = []
    variants: list[ProductVariant] = []
    prices: list[ProductPrice] = []
    n_products = counts["products"]
    for index in range(n_products):
        category = categories[index % len(categories)]
        product_id = new_uuid()
        variant_id = new_uuid()
        sku = f"MRG-{index + 1:04d}"
        name = f"{category.name} {index + 1}"
        unit_price = _money(12 + (index % 80) + (index % 7) * 0.5)
        products.append(
            Product(
                id=product_id,
                organization_id=org_id,
                category_id=category.id,
                type="goods",
                name=name,
                sku=sku,
                uom_id=uom.id,
                track_inventory=True,
                is_active=True,
            )
        )
        variants.append(
            ProductVariant(
                id=variant_id,
                organization_id=org_id,
                product_id=product_id,
                sku=sku,
                name=name,
                is_active=True,
            )
        )
        prices.append(
            ProductPrice(
                id=new_uuid(),
                organization_id=org_id,
                variant_id=variant_id,
                price_list_code="retail",
                amount=unit_price,
                currency_code="ZMW",
            )
        )
    session.add_all(products)
    await session.flush()
    session.add_all(variants)
    await session.flush()
    session.add_all(prices)
    await session.flush()

    customers: list[Customer] = []
    first_names = ("Mwape", "Natasha", "Joseph", "Grace", "Patrick", "Memory", "David", "Ruth")
    last_names = ("Banda", "Phiri", "Zulu", "Tembo", "Mulenga", "Ngoma", "Sakala", "Daka")
    for index in range(counts["customers"]):
        customers.append(
            Customer(
                id=new_uuid(),
                organization_id=org_id,
                code=f"CUS-{index + 1:04d}",
                name=f"{first_names[index % 8]} {last_names[(index // 8) % 8]}",
                phone=f"+26097{index:07d}"[:16],
                is_active=True,
            )
        )
    session.add_all(customers)
    await session.flush()

    suppliers: list[Supplier] = []
    for index in range(counts["suppliers"]):
        suppliers.append(
            Supplier(
                id=new_uuid(),
                organization_id=org_id,
                code=f"SUP-{index + 1:03d}",
                name=f"Zam Wholesale {index + 1}",
                payment_terms_days=14,
                is_active=True,
            )
        )
    session.add_all(suppliers)
    await session.flush()


    opening_qty = Decimal("80")
    unit_cost = _money(8)
    balances: list[StockBalance] = []
    for variant in variants:
        for warehouse in warehouses:
            balances.append(
                StockBalance(
                    id=new_uuid(),
                    organization_id=org_id,
                    warehouse_id=warehouse.id,
                    variant_id=variant.id,
                    qty_on_hand=opening_qty,
                    qty_reserved=Decimal("0"),
                    avg_unit_cost=unit_cost,
                )
            )
    session.add_all(balances)
    await session.flush()

    movements: list[StockMovement] = []
    n_moves = min(counts["stock_movements"], len(variants) * max(len(warehouses), 1))
    for index in range(n_moves):
        variant = variants[index % len(variants)]
        warehouse = warehouses[index % len(warehouses)]
        branch = next((item for item in branches if item.id == warehouse.branch_id), branches[0])
        movements.append(
            StockMovement(
                id=new_uuid(),
                organization_id=org_id,
                warehouse_id=warehouse.id,
                branch_id=branch.id,
                variant_id=variant.id,
                qty_delta=_money(20 + index % 15),
                unit_cost=unit_cost,
                movement_type="purchase_receipt",
                source_type="purchase_receipt",
                source_id=new_uuid(),
                created_by_user_id=actor_id,
            )
        )
    session.add_all(movements)
    await session.flush()

    n_sales = counts["sales"]
    base = DEMO_MONTHLY_REVENUE // n_sales
    remainder = DEMO_MONTHLY_REVENUE - base * n_sales
    sales: list[Sale] = []
    items: list[SaleItem] = []
    payments: list[Payment] = []
    journals: list[JournalEntry] = []
    lines: list[JournalLine] = []
    now = datetime.now(UTC)
    for index in range(n_sales):
        total = _money(base + (1 if index < remainder else 0))
        sale_id = new_uuid()
        variant = variants[index % len(variants)]
        branch = branches[index % len(branches)]
        qty = Decimal("1")
        sales.append(
            Sale(
                id=sale_id,
                organization_id=org_id,
                branch_id=branch.id,
                customer_id=customers[index % len(customers)].id if customers else None,
                document_number=f"SAL-{index + 1:05d}",
                status="completed",
                sale_type="pos",
                subtotal=total,
                discount_total=_money(0),
                tax_total=_money(0),
                total=total,
                currency_code="ZMW",
                completed_at=now - timedelta(days=index % 28),
            )
        )
        items.append(
            SaleItem(
                id=new_uuid(),
                organization_id=org_id,
                sale_id=sale_id,
                variant_id=variant.id,
                description=variant.name,
                qty=qty,
                uom_id=uom.id,
                unit_price=total,
                discount_amount=_money(0),
                tax_amount=_money(0),
                line_total=total,
            )
        )
        payments.append(
            Payment(
                id=new_uuid(),
                organization_id=org_id,
                sale_id=sale_id,
                customer_id=customers[index % len(customers)].id if customers else None,
                method="cash" if index % 3 else "mobile_money",
                status="completed",
                amount=total,
                received_at=now - timedelta(days=index % 28),
            )
        )
        journal_id = new_uuid()
        journals.append(
            JournalEntry(
                id=journal_id,
                organization_id=org_id,
                period_id=period.id,
                entry_number=f"JE-S-{index + 1:05d}",
                status="posted",
                source_type="sale",
                source_id=sale_id,
                description=f"POS sale SAL-{index + 1:05d}",
                posted_at=now - timedelta(days=index % 28),
            )
        )
        lines.append(
            JournalLine(
                id=new_uuid(),
                organization_id=org_id,
                journal_id=journal_id,
                account_id=cash_id,
                branch_id=branch.id,
                debit=total,
                credit=_money(0),
                memo="Cash / mobile money",
            )
        )
        lines.append(
            JournalLine(
                id=new_uuid(),
                organization_id=org_id,
                journal_id=journal_id,
                account_id=revenue_id,
                branch_id=branch.id,
                debit=_money(0),
                credit=total,
                memo="Sales revenue",
            )
        )
        cogs = unit_cost
        cogs_journal = new_uuid()
        journals.append(
            JournalEntry(
                id=cogs_journal,
                organization_id=org_id,
                period_id=period.id,
                entry_number=f"JE-C-{index + 1:05d}",
                status="posted",
                source_type="cogs",
                source_id=sale_id,
                description=f"COGS SAL-{index + 1:05d}",
                posted_at=now - timedelta(days=index % 28),
            )
        )
        lines.append(
            JournalLine(
                id=new_uuid(),
                organization_id=org_id,
                journal_id=cogs_journal,
                account_id=cogs_id,
                branch_id=branch.id,
                debit=cogs,
                credit=_money(0),
            )
        )
        lines.append(
            JournalLine(
                id=new_uuid(),
                organization_id=org_id,
                journal_id=cogs_journal,
                account_id=inventory_id,
                branch_id=branch.id,
                debit=_money(0),
                credit=cogs,
            )
        )

    n_expenses = counts["expenses"]
    exp_base = DEMO_MONTHLY_EXPENSES // n_expenses
    exp_remainder = DEMO_MONTHLY_EXPENSES - exp_base * n_expenses
    expenses: list[Expense] = []
    expense_lines: list[ExpenseLine] = []
    vendors = ("ZESCO", "Lusaka Water", "Airtel Zambia", "Shop rent Chelstone", "Fuel Fill Up")
    for index in range(n_expenses):
        amount = _money(exp_base + (1 if index < exp_remainder else 0))
        expense_id = new_uuid()
        branch = branches[index % len(branches)]
        expenses.append(
            Expense(
                id=expense_id,
                organization_id=org_id,
                branch_id=branch.id,
                vendor_name=vendors[index % len(vendors)],
                amount=amount,
                tax_amount=_money(0),
                status="posted",
                incurred_on=date.today() - timedelta(days=index % 30),
                payment_method="cash",
                document_number=f"EX-{index + 1:05d}",
            )
        )
        expense_lines.append(
            ExpenseLine(
                id=new_uuid(),
                organization_id=org_id,
                expense_id=expense_id,
                account_id=opex_id,
                amount=amount,
            )
        )
        journal_id = new_uuid()
        journals.append(
            JournalEntry(
                id=journal_id,
                organization_id=org_id,
                period_id=period.id,
                entry_number=f"JE-E-{index + 1:05d}",
                status="posted",
                source_type="expense",
                source_id=expense_id,
                description=f"Operating expense EX-{index + 1:05d}",
                posted_at=now - timedelta(days=index % 30),
            )
        )
        lines.append(
            JournalLine(
                id=new_uuid(),
                organization_id=org_id,
                journal_id=journal_id,
                account_id=opex_id,
                branch_id=branch.id,
                debit=amount,
                credit=_money(0),
                memo=vendors[index % len(vendors)],
            )
        )
        lines.append(
            JournalLine(
                id=new_uuid(),
                organization_id=org_id,
                journal_id=journal_id,
                account_id=cash_id,
                branch_id=branch.id,
                debit=_money(0),
                credit=amount,
                memo="Cash payment",
            )
        )

    session.add_all(sales)
    await session.flush()
    session.add_all(items)
    session.add_all(payments)
    session.add_all(expenses)
    await session.flush()
    session.add_all(expense_lines)
    session.add_all(journals)
    await session.flush()
    session.add_all(lines)

    pos: list[PurchaseOrder] = []
    po_items: list[PurchaseOrderItem] = []
    for index in range(counts["purchase_orders"]):
        po_id = new_uuid()
        supplier = suppliers[index % len(suppliers)]
        variant = variants[index % len(variants)]
        pos.append(
            PurchaseOrder(
                id=po_id,
                organization_id=org_id,
                branch_id=branches[index % len(branches)].id,
                supplier_id=supplier.id,
                status="approved",
                document_number=f"PO-{index + 1:05d}",
                ordered_at=now - timedelta(days=index % 40),
            )
        )
        po_items.append(
            PurchaseOrderItem(
                id=new_uuid(),
                organization_id=org_id,
                purchase_order_id=po_id,
                variant_id=variant.id,
                qty_ordered=_money(24),
                qty_received=_money(24),
                unit_cost=unit_cost,
            )
        )
    session.add_all(pos)
    await session.flush()
    session.add_all(po_items)

    extra_staff = [
        "Grace Mulenga",
        "Patrick Sakala",
        "Memory Daka",
        "Joseph Ngoma",
        "Ruth Banda",
        "David Phiri",
        "Natasha Zulu",
        "Mwape Tembo",
        "Chola Musonda",
    ]
    employees: list[Employee] = []
    demo_names = [spec["full_name"] for spec in DEMO_ROLES]
    for index, name in enumerate(demo_names + extra_staff):
        if index >= counts["employees"]:
            break
        employees.append(
            Employee(
                id=new_uuid(),
                organization_id=org_id,
                branch_id=branches[index % len(branches)].id,
                employee_number=f"EMP-{index + 1:03d}",
                full_name=name,
                hire_on=date(2024, 1, 8),
                status="active",
                job_title="Team member",
                base_salary=_money(4500 + index * 250),
            )
        )
    session.add_all(employees)

    notices: list[OutboxEvent] = []
    for index in range(counts["notifications"]):
        notices.append(
            OutboxEvent(
                id=new_uuid(),
                organization_id=org_id,
                event_type="demo.notification",
                payload_json={
                    "title": "Low stock on maize meal" if index % 2 == 0 else "Shift closed at Lusaka Central",
                    "body": "Sample operational alert for the live demo.",
                },
                status="delivered",
            )
        )
    session.add_all(notices)

    audits: list[AuditLog] = []
    actions = (
        "sale.complete",
        "inventory.receive",
        "expense.create",
        "membership.view",
        "report.view",
    )
    for index in range(counts["audit_logs"]):
        audits.append(
            AuditLog(
                id=new_uuid(),
                organization_id=org_id,
                actor_user_id=actor_id,
                action=actions[index % len(actions)],
                entity_type="demo",
                entity_id=str(index + 1),
                after_json={"source": "seed"},
            )
        )
    session.add_all(audits)

    await session.flush()
