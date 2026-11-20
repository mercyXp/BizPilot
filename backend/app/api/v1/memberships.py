from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas import (
    BranchGrantsIn,
    MembershipIn,
    MembershipOut,
    MembershipStatusIn,
    OverrideIn,
    RoleAssignIn,
)
from app.core.context import TenantContext
from app.core.db import get_db
from app.modules.authorization.deps import require_permission
from app.modules.authorization.service import (
    MembershipView,
    add_membership,
    assign_role,
    clear_override,
    list_memberships,
    remove_role,
    replace_branch_grants,
    set_override,
    update_membership_status,
)

router = APIRouter(prefix="/memberships", tags=["memberships"])


def _out(view: MembershipView) -> MembershipOut:
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


@router.get("", response_model=list[MembershipOut])
async def list_all(
    ctx: TenantContext = Depends(require_permission("users.manage")),
    session: AsyncSession = Depends(get_db),
) -> list[MembershipOut]:
    return [_out(view) for view in await list_memberships(session, ctx)]


@router.post("", response_model=MembershipOut, status_code=201)
async def create(
    body: MembershipIn,
    ctx: TenantContext = Depends(require_permission("users.manage")),
    session: AsyncSession = Depends(get_db),
) -> MembershipOut:
    view = await add_membership(
        session,
        ctx,
        email=body.email,
        role_code=body.role_code,
        access_all_branches=body.access_all_branches,
        branch_ids=body.branch_ids,
    )
    return _out(view)


@router.patch("/{membership_id}", response_model=MembershipOut)
async def update_status(
    membership_id: UUID,
    body: MembershipStatusIn,
    ctx: TenantContext = Depends(require_permission("users.manage")),
    session: AsyncSession = Depends(get_db),
) -> MembershipOut:
    return _out(await update_membership_status(session, ctx, membership_id, body.status))


@router.post("/{membership_id}/roles", response_model=MembershipOut)
async def add_role(
    membership_id: UUID,
    body: RoleAssignIn,
    ctx: TenantContext = Depends(require_permission("users.manage")),
    session: AsyncSession = Depends(get_db),
) -> MembershipOut:
    return _out(await assign_role(session, ctx, membership_id, body.role_code))


@router.delete("/{membership_id}/roles/{role_code}", response_model=MembershipOut)
async def delete_role(
    membership_id: UUID,
    role_code: str,
    ctx: TenantContext = Depends(require_permission("users.manage")),
    session: AsyncSession = Depends(get_db),
) -> MembershipOut:
    return _out(await remove_role(session, ctx, membership_id, role_code))


@router.put("/{membership_id}/overrides", response_model=MembershipOut)
async def put_override(
    membership_id: UUID,
    body: OverrideIn,
    ctx: TenantContext = Depends(require_permission("users.manage")),
    session: AsyncSession = Depends(get_db),
) -> MembershipOut:
    return _out(
        await set_override(
            session,
            ctx,
            membership_id,
            permission_code=body.permission_code,
            effect=body.effect,
        )
    )


@router.delete("/{membership_id}/overrides/{permission_code}", response_model=MembershipOut)
async def delete_override(
    membership_id: UUID,
    permission_code: str,
    ctx: TenantContext = Depends(require_permission("users.manage")),
    session: AsyncSession = Depends(get_db),
) -> MembershipOut:
    return _out(await clear_override(session, ctx, membership_id, permission_code))


@router.put("/{membership_id}/branches", response_model=MembershipOut)
async def put_branches(
    membership_id: UUID,
    body: BranchGrantsIn,
    ctx: TenantContext = Depends(require_permission("users.manage")),
    session: AsyncSession = Depends(get_db),
) -> MembershipOut:
    return _out(
        await replace_branch_grants(
            session,
            ctx,
            membership_id,
            access_all_branches=body.access_all_branches,
            branch_ids=body.branch_ids,
        )
    )
