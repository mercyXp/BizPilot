from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.context import TenantContext
from app.core.errors import AppError
from app.core.rls import set_request_context
from app.models.audit import AuditLog
from app.models.user import User
from app.modules.accounting.models import Expense, JournalEntry
from app.modules.catalogue.models import Product, ProductPrice, ProductVariant
from app.modules.demo.catalog import public_centre, business_by_slug
from app.modules.demo.constants import (
    DEMO_EMAIL_DOMAIN,
    DEMO_ROLES,
    DEMO_SLUG,
    demo_email,
    role_by_key,
)
from app.modules.demo.seed import seed_demo_business
from app.modules.identity import service as identity
from app.modules.inventory.models import StockBalance
from app.modules.sales.models import Sale
from app.modules.tenancy.models import Branch, OrganizationSettings


def demo_compact(settings: Settings) -> bool:
    return settings.app_env == "test" or settings.demo_compact


def assert_demo_enabled(settings: Settings) -> None:
    if settings.is_production and not settings.demo_enabled:
        raise AppError(404, "Live demo is not available", code="not_found")
    if not settings.demo_enabled:
        raise AppError(404, "Live demo is not available", code="not_found")


def is_demo_user(user: User) -> bool:
    return user.email.endswith(f"@{DEMO_EMAIL_DOMAIN}")


def public_roles() -> list[dict]:
    return [
        {
            "key": spec["key"],
            "title": spec["title"],
            "summary": spec["summary"],
            "full_name": spec["full_name"],
        }
        for spec in DEMO_ROLES
    ]


async def enter_role(
    session: AsyncSession,
    settings: Settings,
    *,
    role_key: str,
    user_agent: str | None,
    ip: str | None,
    reset: bool = False,
    business: str = DEMO_SLUG,
    branch_code: str | None = None,
) -> tuple[User, str, str, str, dict]:
    assert_demo_enabled(settings)
    try:
        spec = role_by_key(role_key)
        biz = business_by_slug(business)
    except KeyError as exc:
        raise AppError(422, "Unknown demo role or business", code="validation_error") from exc

    org = await seed_demo_business(
        session, slug=biz["slug"], compact=demo_compact(settings), reset=reset
    )
    user = await session.scalar(select(User).where(User.email == demo_email(biz["slug"], spec["key"])))
    if user is None:
        raise AppError(500, "Demo account is missing", code="internal_error")
    issued = await identity.issue_session(
        session, settings, user=user, user_agent=user_agent, ip=ip
    )
    _user, _db_session, access, refresh, csrf = issued
    await track_event(session, org.id, user.id, role=spec["key"], module="entry", action="enter")
    snapshot = await snapshot_for(
        session,
        org.id,
        user_id=user.id,
        email=user.email,
        preferred_branch_code=branch_code,
    )
    return user, access, refresh, csrf, snapshot


async def switch_role(
    session: AsyncSession,
    settings: Settings,
    *,
    current: User,
    role_key: str,
    user_agent: str | None,
    ip: str | None,
) -> tuple[User, str, str, str, dict]:
    if not is_demo_user(current):
        raise AppError(403, "Role switching is only available in the demo", code="permission_denied")
    slug = current.email.split("@")[0].rsplit(".", 1)[0] if "." in current.email.split("@")[0] else DEMO_SLUG
    return await enter_role(
        session,
        settings,
        role_key=role_key,
        user_agent=user_agent,
        ip=ip,
        reset=False,
        business=slug,
    )


async def reset_demo(
    session: AsyncSession,
    settings: Settings,
    *,
    current: User,
    role_key: str,
    user_agent: str | None,
    ip: str | None,
) -> tuple[User, str, str, str, dict]:
    if not is_demo_user(current):
        raise AppError(403, "Demo reset is only available in the demo", code="permission_denied")
    slug = current.email.split("@")[0].rsplit(".", 1)[0] if "." in current.email.split("@")[0] else DEMO_SLUG
    return await enter_role(
        session,
        settings,
        role_key=role_key,
        user_agent=user_agent,
        ip=ip,
        reset=True,
        business=slug,
    )


async def track_event(
    session: AsyncSession,
    organization_id: UUID,
    actor_id: UUID,
    *,
    role: str | None,
    module: str,
    action: str,
) -> None:
    session.add(
        AuditLog(
            organization_id=organization_id,
            actor_user_id=actor_id,
            action=f"demo.{action}",
            entity_type="demo_visit",
            entity_id=module[:64],
            after_json={"role": role, "module": module, "privacy": "no_personal_data"},
        )
    )
    settings_row = await session.scalar(
        select(OrganizationSettings).where(OrganizationSettings.organization_id == organization_id)
    )
    if settings_row is None:
        return
    payload = dict(settings_row.settings) if isinstance(settings_row.settings, dict) else {}
    access = payload.get("demo_access") if isinstance(payload.get("demo_access"), dict) else {}
    roles = list(access.get("roles_explored") or [])
    modules = list(access.get("modules_visited") or [])
    if role and role not in roles:
        roles.append(role)
    if module and module not in modules:
        modules.append(module)
    payload["demo_access"] = {
        "roles_explored": roles[-20:],
        "modules_visited": modules[-50:],
        "updated_at": datetime.now(UTC).isoformat(),
    }
    settings_row.settings = payload


async def snapshot_for(
    session: AsyncSession,
    organization_id: UUID,
    *,
    user_id: UUID,
    email: str,
    preferred_branch_code: str | None = None,
) -> dict:
    await set_request_context(session, user_id=user_id, organization_id=organization_id)
    revenue = await session.scalar(
        select(func.coalesce(func.sum(Sale.total), 0)).where(
            Sale.organization_id == organization_id, Sale.status == "completed"
        )
    )
    expenses = await session.scalar(
        select(func.coalesce(func.sum(Expense.amount), 0)).where(
            Expense.organization_id == organization_id
        )
    )
    products = await session.scalar(
        select(func.count()).select_from(Product).where(Product.organization_id == organization_id)
    )
    branches = list(
        await session.scalars(select(Branch).where(Branch.organization_id == organization_id).order_by(Branch.code))
    )
    journals = await session.scalar(
        select(func.count()).select_from(JournalEntry).where(JournalEntry.organization_id == organization_id)
    )
    settings_row = await session.scalar(
        select(OrganizationSettings).where(OrganizationSettings.organization_id == organization_id)
    )
    access = {}
    if settings_row and isinstance(settings_row.settings, dict):
        access = settings_row.settings.get("demo_access") or {}
    demo_key = DEMO_SLUG
    if settings_row and isinstance(settings_row.settings, dict):
        demo_key = str(settings_row.settings.get("demo_key") or DEMO_SLUG)
    try:
        biz = business_by_slug(demo_key)
    except KeyError:
        biz = business_by_slug(DEMO_SLUG)
    local = email.split("@")[0]
    role_key = local.rsplit(".", 1)[-1] if "." in local else None
    spec = next((item for item in DEMO_ROLES if item["key"] == role_key), None)
    preferred = None
    if preferred_branch_code:
        preferred = next((row for row in branches if row.code == preferred_branch_code), None)
    return {
        "organization": {
            "id": str(organization_id),
            "name": biz["name"],
            "legal_name": biz["legal_name"],
            "industry": biz["size_label"],
            "location": f"{biz['branches'][0]['city']}, Zambia",
            "currency": "ZMW",
            "demo_key": biz["slug"],
        },
        "access_all_branches": bool(spec["access_all_branches"] if spec else True),
        "preferred_branch_id": str(preferred.id) if preferred else None,
        "kpis": {
            "monthly_revenue": float(revenue or 0),
            "monthly_expenses": float(expenses or 0),
            "products": int(products or 0),
            "branches": len(branches),
            "journals": int(journals or 0),
        },
        "branches": [{"id": str(row.id), "code": row.code, "name": row.name} for row in branches],
        "role": spec["key"] if spec else None,
        "role_title": spec["title"] if spec else None,
        "is_demo": True,
        "access": access,
    }


async def catalog(session: AsyncSession, ctx: TenantContext, limit: int = 80) -> list[dict]:
    rows = await session.execute(
        select(Product, ProductVariant, ProductPrice, StockBalance)
        .join(ProductVariant, ProductVariant.product_id == Product.id)
        .join(ProductPrice, ProductPrice.variant_id == ProductVariant.id)
        .outerjoin(StockBalance, StockBalance.variant_id == ProductVariant.id)
        .where(Product.organization_id == ctx.organization_id, Product.deleted_at.is_(None))
        .order_by(Product.name)
        .limit(limit)
    )
    seen: set[UUID] = set()
    items: list[dict] = []
    for product, variant, price, balance in rows.all():
        if variant.id in seen:
            continue
        seen.add(variant.id)
        items.append(
            {
                "product_id": str(product.id),
                "variant_id": str(variant.id),
                "name": product.name,
                "sku": product.sku,
                "price": float(price.amount),
                "qty_on_hand": float(balance.qty_on_hand) if balance is not None else 0,
            }
        )
    return items


async def list_audit(session: AsyncSession, ctx: TenantContext, limit: int = 50) -> list[dict]:
    rows = await session.scalars(
        select(AuditLog)
        .where(AuditLog.organization_id == ctx.organization_id)
        .order_by(AuditLog.created_at.desc())
        .limit(limit)
    )
    return [
        {
            "id": str(row.id),
            "action": row.action,
            "entity_type": row.entity_type,
            "entity_id": row.entity_id,
            "created_at": row.created_at.isoformat() if row.created_at else None,
        }
        for row in rows
    ]


async def list_expenses(session: AsyncSession, ctx: TenantContext, limit: int = 50) -> list[dict]:
    rows = await session.scalars(
        select(Expense)
        .where(Expense.organization_id == ctx.organization_id)
        .order_by(Expense.incurred_on.desc())
        .limit(limit)
    )
    return [
        {
            "id": str(row.id),
            "document_number": row.document_number,
            "vendor_name": row.vendor_name,
            "amount": float(row.amount),
            "status": row.status,
            "incurred_on": row.incurred_on.isoformat(),
        }
        for row in rows
    ]


async def answer_question(session: AsyncSession, ctx: TenantContext, question: str) -> str:
    user = await session.get(User, ctx.user_id)
    snap = await snapshot_for(
        session,
        ctx.organization_id,
        user_id=ctx.user_id,
        email=user.email if user else "",
    )
    kpis = snap["kpis"]
    q = question.lower()
    if "expense" in q:
        return (
            f"{snap['organization']['name']} recorded ZMW {kpis['monthly_expenses']:,.0f} in operating expenses "
            "this period. Rent, ZESCO and restocking are the largest posted costs."
        )
    if "stock" in q or "inventory" in q:
        return (
            f"The catalogue has {kpis['products']} products across {kpis['branches']} branches. "
            "Lusaka Central holds the deepest opening stock; Chelstone and Kitwe follow."
        )
    if "branch" in q:
        names = ", ".join(row["name"] for row in snap["branches"])
        return f"The group trades from {names}. Compare branch sales from the owner dashboard."
    return (
        f"This month this demo business posted about ZMW {kpis['monthly_revenue']:,.0f} in completed sales "
        f"against ZMW {kpis['monthly_expenses']:,.0f} expenses, with {kpis['journals']} journal entries "
        "tying POS, stock and the ledger together."
    )


async def require_demo_org(session: AsyncSession, ctx: TenantContext) -> None:
    await set_request_context(session, user_id=ctx.user_id, organization_id=ctx.organization_id)
    from app.models.organization import Organization

    from app.modules.tenancy.models import OrganizationSettings as OrgSettings

    org = await session.get(Organization, ctx.organization_id)
    settings_row = await session.scalar(
        select(OrgSettings).where(OrgSettings.organization_id == ctx.organization_id)
    )
    is_demo = bool(
        settings_row
        and isinstance(settings_row.settings, dict)
        and settings_row.settings.get("is_demo")
    )
    if org is None or not is_demo:
        raise AppError(403, "This action is limited to the demo tenant", code="permission_denied")
