import json
import logging
from uuid import UUID

from sqlalchemy import select, text
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import TenantContext
from app.core.errors import ApiError, AppError
from app.core.ids import new_uuid
from app.core.rls import set_request_context
from app.core.security import hash_token
from app.core.security import new_url_token as new_action_token
from app.modules.identity.models import User
from app.modules.identity.service import require_verified_email
from app.modules.industry.packs import default_settings_for
from app.modules.tenancy.models import (
    Branch,
    Industry,
    Invitation,
    Organization,
    OrganizationLocale,
    OrganizationMembership,
    OrganizationSettings,
    Warehouse,
)

logger = logging.getLogger(__name__)

INVITE_TTL_DAYS = 7


async def create_organization(
    session: AsyncSession,
    user: User,
    *,
    name: str,
    legal_name: str | None,
    roles_payload: list[dict[str, object]],
    industry_code: str = "general",
    timezone: str = "Africa/Lusaka",
    base_currency_code: str = "ZMW",
    country_code: str = "ZM",
    first_branch: dict | None = None,
    first_warehouse: dict | None = None,
) -> tuple[Organization, OrganizationMembership, Branch | None, Warehouse | None]:
    require_verified_email(user)
    industry = await session.scalar(
        select(Industry).where(Industry.code == industry_code, Industry.is_active.is_(True))
    )
    if industry is None:
        raise AppError(422, "Unknown industry", code="validation_error")

    org_id = new_uuid()
    membership_id = new_uuid()
    owner_role_link_id = new_uuid()
    await set_request_context(session, user_id=user.id, organization_id=None)
    await session.execute(
        text(
            """
            SELECT app_bootstrap_organization(
                CAST(:org_id AS uuid),
                CAST(:membership_id AS uuid),
                CAST(:owner_role_link_id AS uuid),
                :name,
                :legal_name,
                CAST(:roles AS jsonb),
                :industry_code,
                :timezone,
                :currency,
                :country
            )
            """
        ),
        {
            "org_id": str(org_id),
            "membership_id": str(membership_id),
            "owner_role_link_id": str(owner_role_link_id),
            "name": name.strip(),
            "legal_name": legal_name.strip() if legal_name else None,
            "roles": json.dumps(roles_payload),
            "industry_code": industry.code,
            "timezone": timezone,
            "currency": base_currency_code,
            "country": country_code,
        },
    )
    await set_request_context(session, user_id=user.id, organization_id=org_id)
    org = await session.get(Organization, org_id)
    membership = await session.get(OrganizationMembership, membership_id)
    if org is None or membership is None:
        raise AppError(500, "Organization bootstrap did not persist", code="internal_error")
    membership.is_owner = True

    settings = default_settings_for({"default_settings": industry.default_settings})
    session.add(OrganizationSettings(organization_id=org.id, settings=settings))
    session.add(
        OrganizationLocale(organization_id=org.id, default_locale="en", enabled_locales=["en"])
    )
    await _ensure_each_uom(session, org.id)

    branch = None
    warehouse = None
    ctx = TenantContext(
        user_id=user.id,
        organization_id=org.id,
        membership_id=membership.id,
        branch_id=None,
        permissions=frozenset(),
        is_platform_admin=False,
        access_all_branches=True,
        branch_ids=frozenset(),
    )
    if first_branch:
        branch = await create_branch(
            session,
            ctx,
            code=first_branch["code"],
            name=first_branch["name"],
            phone=first_branch.get("phone"),
            create_default_warehouse=first_warehouse is None,
        )
        if first_warehouse:
            warehouse = await create_warehouse(
                session,
                ctx,
                branch_id=branch.id,
                code=first_warehouse["code"],
                name=first_warehouse["name"],
                is_default=True,
            )
        else:
            warehouses = await list_warehouses(session, ctx, branch_id=branch.id)
            warehouse = warehouses[0] if warehouses else None
    await session.flush()
    return org, membership, branch, warehouse


async def list_organizations(session: AsyncSession, user: User) -> list[Organization]:
    await set_request_context(session, user_id=user.id, organization_id=None)
    rows = await session.scalars(
        select(Organization)
        .join(OrganizationMembership, OrganizationMembership.organization_id == Organization.id)
        .where(
            OrganizationMembership.user_id == user.id,
            OrganizationMembership.status == "active",
            Organization.status == "active",
        )
        .order_by(Organization.name)
    )
    return list(rows)


async def update_organization(
    session: AsyncSession,
    ctx: TenantContext,
    *,
    name: str | None,
    legal_name: str | None,
    timezone: str | None,
    base_currency_code: str | None,
    industry_code: str | None,
) -> Organization:
    org = await session.get(Organization, ctx.organization_id)
    if org is None:
        raise AppError(404, "Organization not found", code="not_found")
    if name is not None:
        org.name = name.strip()
    if legal_name is not None:
        org.legal_name = legal_name.strip() or None
    if timezone is not None:
        org.timezone = timezone
    if base_currency_code is not None:
        org.base_currency_code = base_currency_code
    if industry_code is not None:
        industry = await session.scalar(
            select(Industry).where(Industry.code == industry_code, Industry.is_active.is_(True))
        )
        if industry is None:
            raise AppError(422, "Unknown industry", code="validation_error")
        org.industry_id = industry.id
    await session.flush()
    return org


async def get_settings(session: AsyncSession, ctx: TenantContext) -> OrganizationSettings:
    row = await session.scalar(
        select(OrganizationSettings).where(
            OrganizationSettings.organization_id == ctx.organization_id
        )
    )
    if row is None:
        row = OrganizationSettings(organization_id=ctx.organization_id, settings={})
        session.add(row)
        await session.flush()
    return row


async def put_settings(session: AsyncSession, ctx: TenantContext, settings: dict) -> OrganizationSettings:
    row = await get_settings(session, ctx)
    row.settings = settings
    await session.flush()
    return row


async def create_branch(
    session: AsyncSession,
    ctx: TenantContext,
    *,
    code: str,
    name: str,
    phone: str | None,
    create_default_warehouse: bool = True,
) -> Branch:
    branch = Branch(
        organization_id=ctx.organization_id,
        code=code.strip().upper(),
        name=name.strip(),
        phone=phone.strip() if phone else None,
        is_active=True,
    )
    session.add(branch)
    try:
        await session.flush()
    except IntegrityError as exc:
        raise AppError(409, "Branch code already exists", code="conflict") from exc
    if create_default_warehouse:
        await create_warehouse(
            session,
            ctx,
            branch_id=branch.id,
            code=f"{branch.code}-WH",
            name=f"{branch.name} warehouse",
            is_default=True,
        )
    return branch


async def list_branches(session: AsyncSession, ctx: TenantContext) -> list[Branch]:
    statement = select(Branch).where(Branch.organization_id == ctx.organization_id)
    if not ctx.access_all_branches:
        if not ctx.branch_ids:
            return []
        statement = statement.where(Branch.id.in_(ctx.branch_ids))
    rows = await session.scalars(statement.order_by(Branch.code))
    return list(rows)


async def get_branch(session: AsyncSession, ctx: TenantContext, branch_id: UUID) -> Branch:
    branch = await session.get(Branch, branch_id)
    if branch is None:
        raise AppError(404, "Branch not found", code="not_found")
    if not ctx.can_access_branch(branch.id):
        raise AppError(403, "Branch is not granted to this membership", code="permission_denied")
    return branch


async def create_warehouse(
    session: AsyncSession,
    ctx: TenantContext,
    *,
    branch_id: UUID,
    code: str,
    name: str,
    is_default: bool,
) -> Warehouse:
    branch = await get_branch(session, ctx, branch_id)
    if is_default:
        existing = await session.scalars(
            select(Warehouse).where(
                Warehouse.branch_id == branch.id,
                Warehouse.is_default.is_(True),
            )
        )
        for row in existing:
            row.is_default = False
    warehouse = Warehouse(
        organization_id=ctx.organization_id,
        branch_id=branch.id,
        code=code.strip().upper(),
        name=name.strip(),
        is_default=is_default,
        is_active=True,
    )
    session.add(warehouse)
    try:
        await session.flush()
    except IntegrityError as exc:
        raise AppError(409, "Warehouse code already exists", code="conflict") from exc
    return warehouse


async def list_warehouses(
    session: AsyncSession,
    ctx: TenantContext,
    branch_id: UUID | None = None,
) -> list[Warehouse]:
    statement = select(Warehouse).where(Warehouse.organization_id == ctx.organization_id)
    if branch_id is not None:
        await get_branch(session, ctx, branch_id)
        statement = statement.where(Warehouse.branch_id == branch_id)
    elif not ctx.access_all_branches:
        if not ctx.branch_ids:
            return []
        statement = statement.where(Warehouse.branch_id.in_(ctx.branch_ids))
    rows = await session.scalars(statement.order_by(Warehouse.code))
    return list(rows)


async def get_warehouse(session: AsyncSession, ctx: TenantContext, warehouse_id: UUID) -> Warehouse:
    warehouse = await session.get(Warehouse, warehouse_id)
    if warehouse is None:
        raise AppError(404, "Warehouse not found", code="not_found")
    if not ctx.can_access_branch(warehouse.branch_id):
        raise AppError(403, "Branch is not granted to this membership", code="permission_denied")
    return warehouse


async def list_industries(session: AsyncSession) -> list[Industry]:
    rows = await session.scalars(
        select(Industry).where(Industry.is_active.is_(True)).order_by(Industry.name)
    )
    return list(rows)


async def create_invitation(
    session: AsyncSession,
    ctx: TenantContext,
    *,
    email: str,
    role_codes: list[str],
    branch_ids: list[UUID],
    access_all_branches: bool,
) -> tuple[Invitation, str]:
    from app.modules.authorization.models import Role

    email_norm = email.strip().lower()
    roles = list(
        await session.scalars(
            select(Role).where(
                Role.organization_id == ctx.organization_id,
                Role.code.in_(role_codes),
            )
        )
    )
    if len(roles) != len(set(role_codes)):
        raise AppError(422, "Unknown role", code="validation_error")
    if any(role.code == "owner" for role in roles) and "org.manage" not in ctx.permissions:
        raise AppError(403, "Only an owner can assign the owner role", code="permission_denied")
    for branch_id in branch_ids:
        await get_branch(session, ctx, branch_id)

    raw = new_action_token()
    invitation = Invitation(
        organization_id=ctx.organization_id,
        email=email_norm,
        role_ids=[role.id for role in roles],
        branch_ids=list(dict.fromkeys(branch_ids)),
        access_all_branches=access_all_branches,
        token_hash=hash_token(raw),
        expires_at=_invite_expiry(),
        invited_by_user_id=ctx.user_id,
    )
    session.add(invitation)
    await session.flush()
    from app.core.config import get_settings
    from app.core.email import send_email

    settings = get_settings()
    organization = await session.get(Organization, ctx.organization_id)
    org_name = organization.name if organization is not None else "BizPilot"
    accept_url = f"{settings.public_app_url.rstrip('/')}/accept-invite?token={raw}"
    await send_email(
        session,
        to_email=email_norm,
        template="organization_invite",
        payload={
            "accept_url": accept_url,
            "token": raw,
            "organization_name": org_name,
        },
        organization_id=ctx.organization_id,
        settings=settings,
    )
    logger.info("email_event invitation queued", extra={"email": email_norm})
    return invitation, raw


async def list_invitations(session: AsyncSession, ctx: TenantContext) -> list[Invitation]:
    rows = await session.scalars(
        select(Invitation)
        .where(Invitation.organization_id == ctx.organization_id)
        .order_by(Invitation.created_at.desc())
    )
    return list(rows)


async def accept_invitation(session: AsyncSession, user: User, raw_token: str) -> UUID:
    await set_request_context(session, user_id=user.id, organization_id=None)
    membership_id = new_uuid()
    try:
        result = await session.execute(
            text(
                """
                SELECT app_accept_invitation(
                    :token_hash,
                    CAST(:membership_id AS uuid)
                )
                """
            ),
            {"token_hash": hash_token(raw_token), "membership_id": str(membership_id)},
        )
        result.scalar_one()
    except DBAPIError as exc:
        _raise_invitation_error(exc)
    return membership_id


def allow_negative_stock(settings: dict) -> bool:
    inventory = settings.get("inventory") if isinstance(settings, dict) else None
    if not isinstance(inventory, dict):
        return False
    return bool(inventory.get("allow_negative_stock"))


async def _ensure_each_uom(session: AsyncSession, organization_id: UUID) -> None:
    await session.execute(
        text(
            """
            INSERT INTO units_of_measure (id, organization_id, code, name, is_integer)
            VALUES (CAST(:id AS uuid), CAST(:org AS uuid), 'EA', 'Each', true)
            ON CONFLICT (organization_id, code) DO NOTHING
            """
        ),
        {"id": str(new_uuid()), "org": str(organization_id)},
    )


def _invite_expiry():
    from datetime import UTC, datetime, timedelta

    return datetime.now(UTC) + timedelta(days=INVITE_TTL_DAYS)


def _raise_invitation_error(exc: DBAPIError) -> None:
    orig = exc.orig
    state = getattr(orig, "sqlstate", None)
    if state == "P0002":
        raise AppError(404, "Invitation not found", code="not_found") from exc
    if state == "22023":
        raise AppError(400, "Invitation is expired or already used", code="validation_error") from exc
    if state == "42501":
        raise AppError(403, "Invitation does not match this account", code="permission_denied") from exc
    if state == "23505":
        raise AppError(409, "User is already a member", code="conflict") from exc
    raise AppError(400, "Invitation could not be accepted", code="validation_error") from exc


async def list_memberships(
    session: AsyncSession, user: User
) -> list[tuple[OrganizationMembership, Organization]]:
    await set_request_context(session, user_id=user.id, organization_id=None)
    rows = await session.execute(
        select(OrganizationMembership, Organization)
        .join(Organization, Organization.id == OrganizationMembership.organization_id)
        .where(
            OrganizationMembership.user_id == user.id,
            OrganizationMembership.status == "active",
        )
        .order_by(Organization.created_at.asc())
    )
    return list(rows.all())


async def get_active_membership(
    session: AsyncSession, user: User, organization_id: UUID
) -> OrganizationMembership:
    await set_request_context(session, user_id=user.id, organization_id=organization_id)
    membership = await session.scalar(
        select(OrganizationMembership).where(
            OrganizationMembership.user_id == user.id,
            OrganizationMembership.organization_id == organization_id,
            OrganizationMembership.status == "active",
        )
    )
    if membership is None:
        raise ApiError(403, "permission_denied", "You do not have access to this organization")
    return membership


async def get_organization(session: AsyncSession, organization_id: UUID) -> Organization:
    org = await session.get(Organization, organization_id)
    if org is None or org.status != "active":
        raise ApiError(404, "not_found", "Organization not found")
    return org


async def create_owner_invitation(
    session: AsyncSession,
    settings,
    *,
    user: User,
    membership: OrganizationMembership,
    organization: Organization,
    email: str,
):
    from datetime import UTC, datetime, timedelta

    from app.core.email import send_email
    from app.models.audit import AuditLog

    if not membership.is_owner:
        raise ApiError(403, "permission_denied", "Only organization owners can invite members")

    email_norm = email.strip().lower()
    if email_norm == user.email:
        raise ApiError(400, "validation_error", "You already belong to this organization")

    pending = await session.scalar(
        select(Invitation).where(
            Invitation.organization_id == organization.id,
            Invitation.email == email_norm,
            Invitation.accepted_at.is_(None),
            Invitation.expires_at > datetime.now(UTC),
        )
    )
    if pending is not None:
        raise ApiError(409, "conflict", "An invitation is already pending for that email")

    raw_token = new_action_token()
    invitation = Invitation(
        id=new_uuid(),
        organization_id=organization.id,
        email=email_norm,
        role_ids=[],
        branch_ids=[],
        access_all_branches=True,
        token_hash=hash_token(raw_token),
        invited_by_user_id=user.id,
        expires_at=datetime.now(UTC) + timedelta(days=settings.invitation_days),
    )
    session.add(invitation)
    await session.flush()
    accept_url = f"{settings.public_app_url.rstrip('/')}/accept-invite?token={raw_token}"
    await send_email(
        session,
        to_email=email_norm,
        template="organization_invite",
        payload={
            "accept_url": accept_url,
            "token": raw_token,
            "organization_name": organization.name,
        },
        organization_id=organization.id,
        settings=settings,
    )
    session.add(
        AuditLog(
            id=new_uuid(),
            organization_id=organization.id,
            actor_user_id=user.id,
            action="organization.invite",
            entity_type="invitation",
            entity_id=str(invitation.id),
        )
    )
    return invitation, raw_token


async def lookup_invitation(session: AsyncSession, token: str) -> Invitation | None:
    result = await session.execute(
        text(
            "SELECT id, organization_id, email, token_hash, invited_by_user_id, "
            "expires_at, accepted_at, created_at "
            "FROM lookup_invitation_by_hash(:token_hash)"
        ),
        {"token_hash": hash_token(token)},
    )
    row = result.mappings().first()
    if row is None or row["id"] is None:
        return None
    return Invitation(
        id=row["id"],
        organization_id=row["organization_id"],
        email=row["email"],
        token_hash=row["token_hash"],
        invited_by_user_id=row["invited_by_user_id"],
        expires_at=row["expires_at"],
        accepted_at=row["accepted_at"],
        created_at=row["created_at"],
        role_ids=[],
        branch_ids=[],
        access_all_branches=True,
    )
