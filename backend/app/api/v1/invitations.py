from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas import InvitationAcceptIn, InvitationIn, InvitationOut, MembershipOut
from app.core.context import TenantContext
from app.core.db import get_db
from app.modules.authorization.deps import get_current_user, require_permission
from app.modules.authorization.service import list_memberships
from app.modules.identity.models import User
from app.modules.identity.service import expose_dev_token
from app.modules.tenancy.service import accept_invitation, create_invitation, list_invitations

router = APIRouter(tags=["invitations"])


@router.post("/invitations", response_model=InvitationOut, status_code=201)
async def create(
    body: InvitationIn,
    ctx: TenantContext = Depends(require_permission("users.invite")),
    session: AsyncSession = Depends(get_db),
) -> InvitationOut:
    invitation, token = await create_invitation(
        session,
        ctx,
        email=body.email,
        role_codes=body.role_codes,
        branch_ids=body.branch_ids,
        access_all_branches=body.access_all_branches,
    )
    return InvitationOut(
        id=invitation.id,
        email=invitation.email,
        access_all_branches=invitation.access_all_branches,
        accepted=invitation.accepted_at is not None,
        token=expose_dev_token(token),
    )


@router.get("/invitations", response_model=list[InvitationOut])
async def list_all(
    ctx: TenantContext = Depends(require_permission("users.invite")),
    session: AsyncSession = Depends(get_db),
) -> list[InvitationOut]:
    rows = await list_invitations(session, ctx)
    return [
        InvitationOut(
            id=row.id,
            email=row.email,
            access_all_branches=row.access_all_branches,
            accepted=row.accepted_at is not None,
        )
        for row in rows
    ]


@router.post("/invitations/accept", response_model=MembershipOut)
async def accept(
    body: InvitationAcceptIn,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> MembershipOut:
    membership_id = await accept_invitation(session, user, body.token)
    from app.core.rls import set_request_context
    from app.modules.tenancy.models import OrganizationMembership

    membership = await session.get(OrganizationMembership, membership_id)
    if membership is None:
        from app.core.errors import AppError

        raise AppError(500, "Invitation acceptance did not persist", code="internal_error")
    await set_request_context(session, user_id=user.id, organization_id=membership.organization_id)
    ctx = TenantContext(
        user_id=user.id,
        organization_id=membership.organization_id,
        membership_id=membership.id,
        branch_id=None,
        permissions=frozenset(),
        is_platform_admin=False,
        access_all_branches=membership.access_all_branches,
        branch_ids=frozenset(),
    )
    views = await list_memberships(session, ctx)
    view = next(item for item in views if item.id == membership.id)
    return MembershipOut(
        id=view.id,
        user_id=view.user_id,
        email=view.email,
        full_name=view.full_name,
        status=view.status,
        access_all_branches=view.access_all_branches,
        role_codes=view.role_codes,
        branch_ids=view.branch_ids,
    )
