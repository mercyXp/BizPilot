from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user, get_tenant_context
from app.api.v1.schemas import (
    IndustryOut,
    OnboardingIn,
    OrganizationIn,
    OrganizationOut,
    SettingsIn,
    SettingsOut,
)
from app.core.config import Settings, get_settings
from app.core.db import get_db
from app.core.tenancy import TenantContext
from app.models.user import User
from app.modules.accounting.service import seed_books
from app.modules.authorization.catalog import build_role_seed
from app.modules.authorization.deps import require_permission
from app.modules.tenancy import service as tenancy
from app.modules.tenancy.models import Industry, Organization
from app.modules.tenancy.schemas import (
    CreateInvitationRequest,
    InvitationPublic,
    OrganizationPublic,
)

router = APIRouter(tags=["organizations"])


async def _seed_ledger(session, user, organization, membership) -> None:
    ctx = TenantContext(
        user_id=user.id,
        organization_id=organization.id,
        membership_id=membership.id,
        branch_id=None,
        permissions=frozenset(),
        is_platform_admin=False,
        access_all_branches=True,
        branch_ids=frozenset(),
    )
    await seed_books(session, ctx, currency=organization.base_currency_code)


def _org_out(
    organization: Organization,
    *,
    membership_id=None,
    industry: Industry | None = None,
    branch_id=None,
    warehouse_id=None,
    is_owner: bool | None = None,
) -> OrganizationOut:
    return OrganizationOut(
        id=organization.id,
        name=organization.name,
        legal_name=organization.legal_name,
        status=organization.status,
        industry_code=industry.code if industry else None,
        timezone=organization.timezone,
        base_currency_code=organization.base_currency_code,
        country_code=organization.country_code,
        membership_id=membership_id,
        branch_id=branch_id,
        warehouse_id=warehouse_id,
        is_owner=is_owner,
        created_at=organization.created_at,
    )


def _org_public(org, membership) -> OrganizationPublic:
    return OrganizationPublic(
        id=org.id,
        name=org.name,
        legal_name=org.legal_name,
        country_code=org.country_code,
        base_currency_code=org.base_currency_code,
        timezone=org.timezone,
        status=org.status,
        is_owner=membership.is_owner,
        membership_id=membership.id,
        created_at=org.created_at,
    )


@router.post("/organizations", response_model=OrganizationOut, status_code=201)
async def create_org(
    body: OrganizationIn,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> OrganizationOut:
    organization, membership, _branch, _warehouse = await tenancy.create_organization(
        session,
        user,
        name=body.name,
        legal_name=body.legal_name,
        roles_payload=build_role_seed(),
        industry_code=body.industry_code,
        timezone=body.timezone,
        base_currency_code=body.base_currency_code,
        country_code=body.country_code,
    )
    await _seed_ledger(session, user, organization, membership)
    return _org_out(organization, membership_id=membership.id, is_owner=membership.is_owner)


@router.post("/organizations/onboarding", response_model=OrganizationOut, status_code=201)
async def onboard(
    body: OnboardingIn,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> OrganizationOut:
    organization, membership, branch, warehouse = await tenancy.create_organization(
        session,
        user,
        name=body.name,
        legal_name=body.legal_name,
        roles_payload=build_role_seed(),
        industry_code=body.industry_code,
        timezone=body.timezone,
        base_currency_code=body.base_currency_code,
        country_code=body.country_code,
        first_branch=body.branch.model_dump(),
        first_warehouse=body.warehouse.model_dump() if body.warehouse else None,
    )
    await _seed_ledger(session, user, organization, membership)
    return _org_out(
        organization,
        membership_id=membership.id,
        branch_id=branch.id if branch else None,
        warehouse_id=warehouse.id if warehouse else None,
        is_owner=membership.is_owner,
    )


@router.get("/organizations", response_model=list[OrganizationOut])
async def list_orgs(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> list[OrganizationOut]:
    rows = await tenancy.list_organizations(session, user)
    return [_org_out(row) for row in rows]


@router.get("/me/memberships", response_model=list[OrganizationPublic])
async def my_memberships(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[OrganizationPublic]:
    rows = await tenancy.list_memberships(db, user)
    return [_org_public(org, membership) for membership, org in rows]


@router.get("/organizations/current", response_model=OrganizationOut)
async def current_org(
    ctx: TenantContext = Depends(get_tenant_context),
    session: AsyncSession = Depends(get_db),
) -> OrganizationOut:
    organization = await session.get(Organization, ctx.organization_id)
    if organization is None:
        from app.core.errors import AppError

        raise AppError(404, "Organization not found", code="not_found")
    industry = await session.get(Industry, organization.industry_id) if organization.industry_id else None
    return _org_out(
        organization,
        membership_id=ctx.membership_id,
        industry=industry,
        is_owner=ctx.is_owner,
    )


@router.patch("/organizations/current", response_model=OrganizationOut)
async def patch_org(
    body: OrganizationIn,
    ctx: TenantContext = Depends(require_permission("org.settings")),
    session: AsyncSession = Depends(get_db),
) -> OrganizationOut:
    organization = await tenancy.update_organization(
        session,
        ctx,
        name=body.name,
        legal_name=body.legal_name,
        timezone=body.timezone,
        base_currency_code=body.base_currency_code,
        industry_code=body.industry_code,
    )
    return _org_out(organization, membership_id=ctx.membership_id)


@router.get("/organization-settings", response_model=SettingsOut)
async def read_settings(
    ctx: TenantContext = Depends(get_tenant_context),
    session: AsyncSession = Depends(get_db),
) -> SettingsOut:
    row = await tenancy.get_settings(session, ctx)
    return SettingsOut(organization_id=row.organization_id, settings=row.settings)


@router.put("/organization-settings", response_model=SettingsOut)
async def write_settings(
    body: SettingsIn,
    ctx: TenantContext = Depends(require_permission("org.settings")),
    session: AsyncSession = Depends(get_db),
) -> SettingsOut:
    row = await tenancy.put_settings(session, ctx, body.settings)
    return SettingsOut(organization_id=row.organization_id, settings=row.settings)


@router.get("/industries", response_model=list[IndustryOut])
async def industries(session: AsyncSession = Depends(get_db)) -> list[IndustryOut]:
    rows = await tenancy.list_industries(session)
    return [
        IndustryOut(
            id=row.id,
            code=row.code,
            name=row.name,
            config_schema=row.config_schema,
            default_modules=row.default_modules,
            default_settings=row.default_settings,
        )
        for row in rows
    ]


@router.post("/organizations/invitations", status_code=201, response_model=InvitationPublic)
async def invite_member(
    payload: CreateInvitationRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
    tenant: TenantContext = Depends(get_tenant_context),
    settings: Settings = Depends(get_settings),
) -> InvitationPublic:
    org = await tenancy.get_organization(db, tenant.organization_id)
    membership = await tenancy.get_active_membership(db, user, org.id)
    invitation, _token = await tenancy.create_owner_invitation(
        db, settings, user=user, membership=membership, organization=org, email=payload.email
    )
    return InvitationPublic(
        id=invitation.id,
        email=invitation.email,
        organization_id=invitation.organization_id,
        organization_name=org.name,
        expires_at=invitation.expires_at,
        accepted=invitation.accepted_at is not None,
    )


@router.get("/invitations/preview", response_model=InvitationPublic)
async def preview_invitation(
    token: str,
    db: AsyncSession = Depends(get_db),
) -> InvitationPublic:
    from app.core.errors import ApiError

    invitation = await tenancy.lookup_invitation(db, token)
    if invitation is None or invitation.accepted_at is not None:
        raise ApiError(400, "invalid_token", "This invitation is invalid or has expired")
    return InvitationPublic(
        id=invitation.id,
        email=invitation.email,
        organization_id=invitation.organization_id,
        expires_at=invitation.expires_at,
        accepted=False,
    )
