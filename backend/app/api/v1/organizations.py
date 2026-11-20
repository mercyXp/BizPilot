from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas import (
    IndustryOut,
    OnboardingIn,
    OrganizationIn,
    OrganizationOut,
    SettingsIn,
    SettingsOut,
)
from app.core.context import TenantContext
from app.core.db import get_db
from app.modules.authorization.catalog import build_role_seed
from app.modules.authorization.deps import get_current_user, get_tenant_context, require_permission
from app.modules.identity.models import User
from app.modules.tenancy.models import Industry, Organization
from app.modules.tenancy.service import (
    create_organization,
    get_settings,
    list_industries,
    list_organizations,
    put_settings,
    update_organization,
)

router = APIRouter(tags=["organizations"])


def _org_out(
    organization: Organization,
    *,
    membership_id=None,
    industry: Industry | None = None,
    branch_id=None,
    warehouse_id=None,
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
    )


@router.post("/organizations", response_model=OrganizationOut, status_code=201)
async def create_org(
    body: OrganizationIn,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> OrganizationOut:
    organization, membership, _branch, _warehouse = await create_organization(
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
    return _org_out(organization, membership_id=membership.id)


@router.post("/organizations/onboarding", response_model=OrganizationOut, status_code=201)
async def onboard(
    body: OnboardingIn,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> OrganizationOut:
    organization, membership, branch, warehouse = await create_organization(
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
    return _org_out(
        organization,
        membership_id=membership.id,
        branch_id=branch.id if branch else None,
        warehouse_id=warehouse.id if warehouse else None,
    )


@router.get("/organizations", response_model=list[OrganizationOut])
async def list_orgs(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> list[OrganizationOut]:
    rows = await list_organizations(session, user)
    return [_org_out(row) for row in rows]


@router.get("/organizations/current", response_model=OrganizationOut)
async def current_org(
    ctx: TenantContext = Depends(get_tenant_context),
    session: AsyncSession = Depends(get_db),
) -> OrganizationOut:
    organization = await session.get(Organization, ctx.organization_id)
    industry = await session.get(Industry, organization.industry_id) if organization else None
    if organization is None:
        from app.core.errors import AppError

        raise AppError(404, "Organization not found", code="not_found")
    return _org_out(organization, membership_id=ctx.membership_id, industry=industry)


@router.patch("/organizations/current", response_model=OrganizationOut)
async def patch_org(
    body: OrganizationIn,
    ctx: TenantContext = Depends(require_permission("org.settings")),
    session: AsyncSession = Depends(get_db),
) -> OrganizationOut:
    organization = await update_organization(
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
    row = await get_settings(session, ctx)
    return SettingsOut(organization_id=row.organization_id, settings=row.settings)


@router.put("/organization-settings", response_model=SettingsOut)
async def write_settings(
    body: SettingsIn,
    ctx: TenantContext = Depends(require_permission("org.settings")),
    session: AsyncSession = Depends(get_db),
) -> SettingsOut:
    row = await put_settings(session, ctx, body.settings)
    return SettingsOut(organization_id=row.organization_id, settings=row.settings)


@router.get("/industries", response_model=list[IndustryOut])
async def industries(session: AsyncSession = Depends(get_db)) -> list[IndustryOut]:
    rows = await list_industries(session)
    return [
        IndustryOut(
            id=row.id,
            code=row.code,
            name=row.name,
            default_modules=row.default_modules,
            default_settings=row.default_settings,
        )
        for row in rows
    ]
