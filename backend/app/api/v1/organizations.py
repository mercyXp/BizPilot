from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user, get_tenant_context
from app.core.config import Settings, get_settings
from app.core.db import get_db
from app.core.tenancy import TenantContext
from app.models.user import User
from app.modules.tenancy import service as tenancy
from app.modules.tenancy.schemas import (
    AcceptInvitationRequest,
    CreateInvitationRequest,
    CreateOrganizationRequest,
    InvitationPublic,
    OrganizationPublic,
)

router = APIRouter(tags=["organizations"])


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


@router.post("/organizations", status_code=201, response_model=OrganizationPublic)
async def create_organization(
    payload: CreateOrganizationRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> OrganizationPublic:
    org, membership = await tenancy.create_organization(
        db, user, name=payload.name, legal_name=payload.legal_name
    )
    return _org_public(org, membership)


@router.get("/me/memberships", response_model=list[OrganizationPublic])
async def my_memberships(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[OrganizationPublic]:
    rows = await tenancy.list_memberships(db, user)
    return [_org_public(org, membership) for membership, org in rows]


@router.get("/organizations/current", response_model=OrganizationPublic)
async def current_organization(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
    tenant: TenantContext = Depends(get_tenant_context),
) -> OrganizationPublic:
    org = await tenancy.get_organization(db, tenant.organization_id)
    membership = await tenancy.get_active_membership(db, user, org.id)
    return _org_public(org, membership)


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
    invitation, _token = await tenancy.create_invitation(
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


@router.post("/invitations/accept", response_model=OrganizationPublic)
async def accept_invitation(
    payload: AcceptInvitationRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> OrganizationPublic:
    org, membership = await tenancy.accept_invitation(db, user, payload.token)
    return _org_public(org, membership)
