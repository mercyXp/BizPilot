from datetime import UTC, date, datetime, time
from decimal import Decimal
from uuid import UUID

from sqlalchemy import Select, func, literal_column, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.tenancy import TenantContext
from app.modules.accounting.models import Expense
from app.modules.catalogue.models import ProductVariant
from app.modules.crm.models import Customer, CustomerCreditAccount
from app.modules.inventory.models import StockBalance, StockMovement
from app.modules.purchasing.models import PurchaseOrder, PurchaseOrderItem, Supplier
from app.modules.sales.models import PosSession, Sale, SaleItem
from app.modules.tenancy.models import Branch, Warehouse

KINDS = (
    "sales",
    "inventory",
    "movement",
    "purchases",
    "expenses",
    "customers",
    "shifts",
    "tax",
)


def _range(from_date: date | None, to_date: date | None) -> tuple[datetime, datetime]:
    today = date.today()
    start = from_date or date(today.year, today.month, 1)
    end = to_date or today
    return (
        datetime.combine(start, time.min, tzinfo=UTC),
        datetime.combine(end, time.max, tzinfo=UTC),
    )


def _branch_ids(ctx: TenantContext) -> list[UUID] | None:
    if ctx.branch_id is not None:
        return [ctx.branch_id]
    if ctx.access_all_branches:
        return None
    return list(ctx.branch_ids)


def _sale_clauses(ctx: TenantContext, start: datetime, end: datetime) -> list:
    clauses = [
        Sale.organization_id == ctx.organization_id,
        Sale.status == "completed",
        Sale.completed_at.is_not(None),
        Sale.completed_at >= start,
        Sale.completed_at <= end,
    ]
    branches = _branch_ids(ctx)
    if branches is not None:
        clauses.append(Sale.branch_id.in_(branches) if branches else Sale.branch_id.is_(None))
    return clauses


async def sales_report(
    session: AsyncSession, ctx: TenantContext, *, from_date: date | None, to_date: date | None
) -> dict:
    start, end = _range(from_date, to_date)
    clauses = _sale_clauses(ctx, start, end)
    totals_row = (
        await session.execute(
            select(
                func.count(Sale.id),
                func.coalesce(func.sum(Sale.total), 0),
                func.coalesce(func.sum(Sale.tax_total), 0),
            ).where(*clauses)
        )
    ).one()
    by_branch = (
        await session.execute(
            select(
                Branch.id,
                Branch.name,
                func.coalesce(func.sum(Sale.total), 0),
                func.count(Sale.id),
            )
            .join(Sale, Sale.branch_id == Branch.id)
            .where(*clauses)
            .group_by(Branch.id, Branch.name)
            .order_by(Branch.name)
        )
    ).all()
    top_items = (
        await session.execute(
            select(
                SaleItem.description,
                func.coalesce(func.sum(SaleItem.qty), 0),
                func.coalesce(func.sum(SaleItem.line_total), 0),
            )
            .join(Sale, Sale.id == SaleItem.sale_id)
            .where(*clauses)
            .group_by(SaleItem.description)
            .order_by(func.sum(SaleItem.line_total).desc())
            .limit(20)
        )
    ).all()
    day = func.date_trunc(literal_column("'day'"), Sale.completed_at)
    trend = (
        await session.execute(
            select(day, func.coalesce(func.sum(Sale.total), 0))
            .where(*clauses)
            .group_by(day)
            .order_by(day)
        )
    ).all()
    return {
        "kind": "sales",
        "from": start.date().isoformat(),
        "to": end.date().isoformat(),
        "currency": "ZMW",
        "totals": {
            "sales_count": int(totals_row[0] or 0),
            "revenue": float(totals_row[1] or 0),
            "tax": float(totals_row[2] or 0),
        },
        "by_branch": [
            {
                "branch_id": str(row[0]),
                "branch_name": row[1],
                "revenue": float(row[2]),
                "sales_count": int(row[3]),
            }
            for row in by_branch
        ],
        "lines": [
            {"name": row[0], "qty": float(row[1]), "revenue": float(row[2])} for row in top_items
        ],
        "trend": [
            {"date": row[0].date().isoformat() if row[0] else None, "revenue": float(row[1])}
            for row in trend
        ],
    }


async def inventory_report(session: AsyncSession, ctx: TenantContext) -> dict:
    statement: Select = (
        select(
            ProductVariant.name,
            Warehouse.name,
            StockBalance.qty_on_hand,
            StockBalance.avg_unit_cost,
            StockBalance.qty_on_hand * StockBalance.avg_unit_cost,
        )
        .join(ProductVariant, ProductVariant.id == StockBalance.variant_id)
        .join(Warehouse, Warehouse.id == StockBalance.warehouse_id)
        .where(StockBalance.organization_id == ctx.organization_id)
        .order_by(ProductVariant.name)
    )
    branches = _branch_ids(ctx)
    if branches is not None:
        statement = statement.where(Warehouse.branch_id.in_(branches or [UUID(int=0)]))
    rows = (await session.execute(statement)).all()
    value = sum((row[4] or Decimal("0") for row in rows), Decimal("0"))
    return {
        "kind": "inventory",
        "currency": "ZMW",
        "totals": {
            "lines": len(rows),
            "stock_value": float(value),
            "low_stock": sum(1 for row in rows if (row[2] or 0) < 10),
        },
        "lines": [
            {
                "product": row[0],
                "warehouse": row[1],
                "qty_on_hand": float(row[2] or 0),
                "avg_unit_cost": float(row[3] or 0),
                "value": float(row[4] or 0),
            }
            for row in rows[:200]
        ],
    }


async def movement_report(
    session: AsyncSession, ctx: TenantContext, *, from_date: date | None, to_date: date | None
) -> dict:
    start, end = _range(from_date, to_date)
    statement = (
        select(
            StockMovement.occurred_at,
            StockMovement.movement_type,
            ProductVariant.name,
            Warehouse.name,
            StockMovement.qty_delta,
            StockMovement.unit_cost,
        )
        .join(ProductVariant, ProductVariant.id == StockMovement.variant_id)
        .join(Warehouse, Warehouse.id == StockMovement.warehouse_id)
        .where(
            StockMovement.organization_id == ctx.organization_id,
            StockMovement.occurred_at >= start,
            StockMovement.occurred_at <= end,
        )
        .order_by(StockMovement.occurred_at.desc())
        .limit(200)
    )
    branches = _branch_ids(ctx)
    if branches is not None:
        statement = statement.where(StockMovement.branch_id.in_(branches or [UUID(int=0)]))
    rows = (await session.execute(statement)).all()
    inbound = sum((row[4] for row in rows if row[4] > 0), Decimal("0"))
    outbound = sum((row[4] for row in rows if row[4] < 0), Decimal("0"))
    return {
        "kind": "movement",
        "from": start.date().isoformat(),
        "to": end.date().isoformat(),
        "totals": {"inbound_qty": float(inbound), "outbound_qty": float(outbound), "lines": len(rows)},
        "lines": [
            {
                "occurred_at": row[0].isoformat() if row[0] else None,
                "type": row[1],
                "product": row[2],
                "warehouse": row[3],
                "qty_delta": float(row[4]),
                "unit_cost": float(row[5]),
            }
            for row in rows
        ],
    }


async def purchases_report(
    session: AsyncSession, ctx: TenantContext, *, from_date: date | None, to_date: date | None
) -> dict:
    start, end = _range(from_date, to_date)
    rows = (
        await session.execute(
            select(
                PurchaseOrder.document_number,
                PurchaseOrder.status,
                Supplier.name,
                func.coalesce(func.sum(PurchaseOrderItem.qty_ordered * PurchaseOrderItem.unit_cost), 0),
            )
            .join(Supplier, Supplier.id == PurchaseOrder.supplier_id)
            .outerjoin(PurchaseOrderItem, PurchaseOrderItem.purchase_order_id == PurchaseOrder.id)
            .where(PurchaseOrder.organization_id == ctx.organization_id)
            .group_by(PurchaseOrder.id, PurchaseOrder.document_number, PurchaseOrder.status, Supplier.name)
            .order_by(PurchaseOrder.document_number)
        )
    ).all()
    total = sum((row[3] or Decimal("0") for row in rows), Decimal("0"))
    return {
        "kind": "purchases",
        "from": start.date().isoformat(),
        "to": end.date().isoformat(),
        "currency": "ZMW",
        "totals": {"orders": len(rows), "ordered_value": float(total)},
        "lines": [
            {
                "document_number": row[0],
                "status": row[1],
                "supplier": row[2],
                "ordered_value": float(row[3] or 0),
            }
            for row in rows
        ],
    }


async def expenses_report(
    session: AsyncSession, ctx: TenantContext, *, from_date: date | None, to_date: date | None
) -> dict:
    start, end = _range(from_date, to_date)
    statement = select(Expense).where(
        Expense.organization_id == ctx.organization_id,
        Expense.incurred_on >= start.date(),
        Expense.incurred_on <= end.date(),
    )
    branches = _branch_ids(ctx)
    if branches is not None:
        statement = statement.where(Expense.branch_id.in_(branches or [UUID(int=0)]))
    rows = list(await session.scalars(statement.order_by(Expense.incurred_on.desc())))
    total = sum((row.amount for row in rows), Decimal("0"))
    return {
        "kind": "expenses",
        "from": start.date().isoformat(),
        "to": end.date().isoformat(),
        "currency": "ZMW",
        "totals": {"count": len(rows), "amount": float(total)},
        "lines": [
            {
                "document_number": row.document_number,
                "vendor_name": row.vendor_name,
                "amount": float(row.amount),
                "status": row.status,
                "incurred_on": row.incurred_on.isoformat(),
            }
            for row in rows
        ],
    }


async def customer_report(session: AsyncSession, ctx: TenantContext) -> dict:
    debts = (
        await session.execute(
            select(
                Customer.name,
                Customer.code,
                CustomerCreditAccount.balance,
                CustomerCreditAccount.credit_limit,
            )
            .join(CustomerCreditAccount, CustomerCreditAccount.customer_id == Customer.id)
            .where(
                Customer.organization_id == ctx.organization_id,
                CustomerCreditAccount.balance > 0,
            )
            .order_by(CustomerCreditAccount.balance.desc())
        )
    ).all()
    spend = (
        await session.execute(
            select(Customer.name, func.coalesce(func.sum(Sale.total), 0))
            .join(Sale, Sale.customer_id == Customer.id)
            .where(Customer.organization_id == ctx.organization_id, Sale.status == "completed")
            .group_by(Customer.id, Customer.name)
            .order_by(func.sum(Sale.total).desc())
            .limit(20)
        )
    ).all()
    owed = sum((row[2] or Decimal("0") for row in debts), Decimal("0"))
    return {
        "kind": "customers",
        "currency": "ZMW",
        "totals": {"owed": float(owed), "debtors": len(debts)},
        "lines": [
            {
                "customer": row[0],
                "code": row[1],
                "balance": float(row[2]),
                "credit_limit": float(row[3]),
            }
            for row in debts
        ],
        "top_customers": [{"customer": row[0], "revenue": float(row[1])} for row in spend],
    }


async def shifts_report(
    session: AsyncSession, ctx: TenantContext, *, from_date: date | None, to_date: date | None
) -> dict:
    start, end = _range(from_date, to_date)
    statement = select(PosSession).where(
        PosSession.organization_id == ctx.organization_id,
        PosSession.opened_at >= start,
        PosSession.opened_at <= end,
    )
    branches = _branch_ids(ctx)
    if branches is not None:
        statement = statement.where(PosSession.branch_id.in_(branches or [UUID(int=0)]))
    rows = list(await session.scalars(statement.order_by(PosSession.opened_at.desc())))
    lines = []
    variance_count = 0
    for row in rows:
        counted = float(row.closing_counted_cash) if row.closing_counted_cash is not None else None
        opening = float(row.opening_float or 0)
        variance = None if counted is None else counted - opening
        if variance not in (None, 0):
            variance_count += 1
        lines.append(
            {
                "id": str(row.id),
                "status": row.status,
                "opening_float": opening,
                "closing_counted_cash": counted,
                "variance": variance,
                "opened_at": row.opened_at.isoformat() if row.opened_at else None,
            }
        )
    return {
        "kind": "shifts",
        "from": start.date().isoformat(),
        "to": end.date().isoformat(),
        "totals": {"sessions": len(rows), "with_variance": variance_count},
        "lines": lines,
    }


async def tax_report(
    session: AsyncSession, ctx: TenantContext, *, from_date: date | None, to_date: date | None
) -> dict:
    sales = await sales_report(session, ctx, from_date=from_date, to_date=to_date)
    return {
        "kind": "tax",
        "from": sales["from"],
        "to": sales["to"],
        "currency": "ZMW",
        "disclaimer": "DEV_ONLY placeholder. Not an official ZRA filing.",
        "totals": {"output_tax": sales["totals"]["tax"], "sales_revenue": sales["totals"]["revenue"]},
        "lines": [
            {
                "label": "Output tax from completed sales",
                "amount": sales["totals"]["tax"],
            }
        ],
    }


async def summary(session: AsyncSession, ctx: TenantContext) -> dict:
    today = date.today()
    month_start = date(today.year, today.month, 1)
    month = await sales_report(session, ctx, from_date=month_start, to_date=today)
    today_sales = await sales_report(session, ctx, from_date=today, to_date=today)
    stock = await inventory_report(session, ctx)
    expenses = await expenses_report(session, ctx, from_date=month_start, to_date=today)
    return {
        "kind": "summary",
        "currency": "ZMW",
        "today_revenue": today_sales["totals"]["revenue"],
        "month_revenue": month["totals"]["revenue"],
        "month_expenses": expenses["totals"]["amount"],
        "month_profit": month["totals"]["revenue"] - expenses["totals"]["amount"],
        "low_stock": stock["totals"]["low_stock"],
        "stock_value": stock["totals"]["stock_value"],
        "by_branch": month["by_branch"],
        "trend": month["trend"],
        "totals": {
            "month_revenue": month["totals"]["revenue"],
            "month_expenses": expenses["totals"]["amount"],
        },
    }


async def run_report(
    session: AsyncSession,
    ctx: TenantContext,
    kind: str,
    *,
    from_date: date | None,
    to_date: date | None,
) -> dict:
    if kind == "inventory":
        return await inventory_report(session, ctx)
    if kind == "customers":
        return await customer_report(session, ctx)
    if kind == "sales":
        return await sales_report(session, ctx, from_date=from_date, to_date=to_date)
    if kind == "movement":
        return await movement_report(session, ctx, from_date=from_date, to_date=to_date)
    if kind == "purchases":
        return await purchases_report(session, ctx, from_date=from_date, to_date=to_date)
    if kind == "expenses":
        return await expenses_report(session, ctx, from_date=from_date, to_date=to_date)
    if kind == "shifts":
        return await shifts_report(session, ctx, from_date=from_date, to_date=to_date)
    if kind == "tax":
        return await tax_report(session, ctx, from_date=from_date, to_date=to_date)
    raise KeyError(kind)


def csv_from_report(payload: dict) -> str:
    lines = payload.get("lines") or []
    if not lines:
        totals = payload.get("totals") or {}
        if not totals:
            return "message\nNo rows\n"
        return ",".join(totals.keys()) + "\n" + ",".join(str(value) for value in totals.values()) + "\n"
    keys = list(lines[0].keys())
    rows = [",".join(keys)]
    for line in lines:
        rows.append(",".join(str(line.get(key, "")).replace(",", " ") for key in keys))
    return "\n".join(rows) + "\n"
