from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import TenantContext
from app.core.errors import AppError
from app.core.rls import set_request_context
from app.modules.authorization.catalog import apply_overrides
from app.modules.authorization.models import (
    MembershipBranch,
    MembershipRole,
    Permission,
    Role,
    RolePermission,
    UserPermissionOverride,
)
from app.modules.identity.models import User
from app.modules.tenancy.models import Branch, Organization, OrganizationMembership


@dataclass(frozen=True)
class MembershipView:
    id: UUID
    user_id: UUID
    email: str
    full_name: str
    status: str
    access_all_branches: bool
    role_codes: list[str]
    branch_ids: list[UUID]


async def load_tenant_context(
    session: AsyncSession,
    user: User,
    *,
    organization_id: UUID,
    branch_id: UUID | None,
) -> TenantContext:
    await set_request_context(session, user_id=user.id, organization_id=organization_id)
    membership = await session.scalar(
        select(OrganizationMembership).where(
            OrganizationMembership.organization_id == organization_id,
            OrganizationMembership.user_id == user.id,
            OrganizationMembership.status == "active",
        )
    )
    if membership is None:
        raise AppError(
            403,
            "You are not an active member of this organization",
            code="permission_denied",
        )

    organization = await session.get(Organization, organization_id)
    if organization is None or organization.status != "active":
        raise AppError(403, "Organization is not active", code="permission_denied")

    permissions = await permission_codes(session, membership.id)
    branch_ids = await granted_branch_ids(session, membership.id)
    if branch_id is not None:
        branch = await session.get(Branch, branch_id)
        if branch is None:
            raise AppError(404, "Branch not found", code="not_found")
        if not membership.access_all_branches and branch.id not in branch_ids:
            raise AppError(
                403,
                "Branch is not granted to this membership",
                code="permission_denied",
            )

    return TenantContext(
        user_id=user.id,
        organization_id=organization_id,
        membership_id=membership.id,
        branch_id=branch_id,
        permissions=permissions,
        is_platform_admin=user.platform_role == "super_admin",
        access_all_branches=membership.access_all_branches,
        branch_ids=branch_ids,
    )


async def permission_codes(session: AsyncSession, membership_id: UUID) -> frozenset[str]:
    role_rows = await session.scalars(
        select(Permission.code)
        .join(RolePermission, RolePermission.permission_id == Permission.id)
        .join(MembershipRole, MembershipRole.role_id == RolePermission.role_id)
        .where(MembershipRole.membership_id == membership_id)
    )
    override_rows = await session.execute(
        select(Permission.code, UserPermissionOverride.effect)
        .join(Permission, Permission.id == UserPermissionOverride.permission_id)
        .where(UserPermissionOverride.membership_id == membership_id)
    )
    return apply_overrides(set(role_rows), [(code, effect) for code, effect in override_rows.all()])


async def granted_branch_ids(session: AsyncSession, membership_id: UUID) -> frozenset[UUID]:
    rows = await session.scalars(
        select(MembershipBranch.branch_id).where(MembershipBranch.membership_id == membership_id)
    )
    return frozenset(rows)


async def list_memberships(session: AsyncSession, ctx: TenantContext) -> list[MembershipView]:
    memberships = list(
        await session.scalars(
            select(OrganizationMembership)
            .where(OrganizationMembership.organization_id == ctx.organization_id)
            .order_by(OrganizationMembership.created_at)
        )
    )
    return await _views(session, ctx.organization_id, memberships)


async def add_membership(
    session: AsyncSession,
    ctx: TenantContext,
    *,
    email: str,
    role_code: str,
    access_all_branches: bool,
    branch_ids: list[UUID],
) -> MembershipView:
    user = await session.scalar(select(User).where(User.email == email.strip().lower()))
    if user is None or not user.is_active:
        raise AppError(404, "User not found", code="not_found")
    existing = await session.scalar(
        select(OrganizationMembership).where(
            OrganizationMembership.organization_id == ctx.organization_id,
            OrganizationMembership.user_id == user.id,
        )
    )
    if existing is not None:
        raise AppError(409, "User is already a member", code="conflict")

    role = await _role(session, ctx.organization_id, role_code)
    _assert_can_assign(ctx, role)
    await _assert_branches_exist(session, ctx.organization_id, branch_ids)

    membership = OrganizationMembership(
        organization_id=ctx.organization_id,
        user_id=user.id,
        status="active",
        access_all_branches=access_all_branches,
    )
    session.add(membership)
    await session.flush()
    session.add(
        MembershipRole(
            organization_id=ctx.organization_id,
            membership_id=membership.id,
            role_id=role.id,
        )
    )
    for branch_id in dict.fromkeys(branch_ids):
        session.add(
            MembershipBranch(
                organization_id=ctx.organization_id,
                membership_id=membership.id,
                branch_id=branch_id,
            )
        )
    await session.flush()
    return (await _views(session, ctx.organization_id, [membership]))[0]


async def update_membership_status(
    session: AsyncSession,
    ctx: TenantContext,
    membership_id: UUID,
    status: str,
) -> MembershipView:
    membership = await _membership(session, ctx, membership_id)
    await _assert_can_edit(session, ctx, membership)
    if status != "active" and await _is_owner(session, membership.id):
        if await _active_owner_count(session, ctx.organization_id) <= 1:
            raise AppError(409, "The last owner cannot be suspended", code="conflict")
    membership.status = status
    await session.flush()
    return (await _views(session, ctx.organization_id, [membership]))[0]


async def assign_role(
    session: AsyncSession,
    ctx: TenantContext,
    membership_id: UUID,
    role_code: str,
) -> MembershipView:
    membership = await _membership(session, ctx, membership_id)
    await _assert_can_edit(session, ctx, membership)
    role = await _role(session, ctx.organization_id, role_code)
    _assert_can_assign(ctx, role)
    already = await session.scalar(
        select(MembershipRole).where(
            MembershipRole.membership_id == membership.id,
            MembershipRole.role_id == role.id,
        )
    )
    if already is None:
        session.add(
            MembershipRole(
                organization_id=ctx.organization_id,
                membership_id=membership.id,
                role_id=role.id,
            )
        )
        await session.flush()
    return (await _views(session, ctx.organization_id, [membership]))[0]


async def remove_role(
    session: AsyncSession,
    ctx: TenantContext,
    membership_id: UUID,
    role_code: str,
) -> MembershipView:
    membership = await _membership(session, ctx, membership_id)
    await _assert_can_edit(session, ctx, membership)
    role = await _role(session, ctx.organization_id, role_code)
    if role.code == "owner" and await _active_owner_count(session, ctx.organization_id) <= 1:
        raise AppError(409, "The last owner role cannot be removed", code="conflict")
    await session.execute(
        delete(MembershipRole).where(
            MembershipRole.membership_id == membership.id,
            MembershipRole.role_id == role.id,
        )
    )
    await session.flush()
    return (await _views(session, ctx.organization_id, [membership]))[0]


async def set_override(
    session: AsyncSession,
    ctx: TenantContext,
    membership_id: UUID,
    *,
    permission_code: str,
    effect: str,
) -> MembershipView:
    membership = await _membership(session, ctx, membership_id)
    await _assert_can_edit(session, ctx, membership)
    permission = await _permission(session, permission_code)
    existing = await session.scalar(
        select(UserPermissionOverride).where(
            UserPermissionOverride.membership_id == membership.id,
            UserPermissionOverride.permission_id == permission.id,
        )
    )
    if existing is None:
        session.add(
            UserPermissionOverride(
                organization_id=ctx.organization_id,
                membership_id=membership.id,
                permission_id=permission.id,
                effect=effect,
            )
        )
    else:
        existing.effect = effect
    await session.flush()
    return (await _views(session, ctx.organization_id, [membership]))[0]


async def clear_override(
    session: AsyncSession,
    ctx: TenantContext,
    membership_id: UUID,
    permission_code: str,
) -> MembershipView:
    membership = await _membership(session, ctx, membership_id)
    await _assert_can_edit(session, ctx, membership)
    permission = await _permission(session, permission_code)
    await session.execute(
        delete(UserPermissionOverride).where(
            UserPermissionOverride.membership_id == membership.id,
            UserPermissionOverride.permission_id == permission.id,
        )
    )
    await session.flush()
    return (await _views(session, ctx.organization_id, [membership]))[0]


async def replace_branch_grants(
    session: AsyncSession,
    ctx: TenantContext,
    membership_id: UUID,
    *,
    access_all_branches: bool,
    branch_ids: list[UUID],
) -> MembershipView:
    membership = await _membership(session, ctx, membership_id)
    await _assert_can_edit(session, ctx, membership)
    unique_ids = list(dict.fromkeys(branch_ids))
    await _assert_branches_exist(session, ctx.organization_id, unique_ids)
    membership.access_all_branches = access_all_branches
    await session.execute(
        delete(MembershipBranch).where(MembershipBranch.membership_id == membership.id)
    )
    for branch_id in unique_ids:
        session.add(
            MembershipBranch(
                organization_id=ctx.organization_id,
                membership_id=membership.id,
                branch_id=branch_id,
            )
        )
    await session.flush()
    return (await _views(session, ctx.organization_id, [membership]))[0]


async def _views(
    session: AsyncSession,
    _organization_id: UUID,
    memberships: list[OrganizationMembership],
) -> list[MembershipView]:
    if not memberships:
        return []
    ids = [item.id for item in memberships]
    users = {
        user.id: user
        for user in await session.scalars(select(User).where(User.id.in_([item.user_id for item in memberships])))
    }
    role_rows = await session.execute(
        select(MembershipRole.membership_id, Role.code)
        .join(Role, Role.id == MembershipRole.role_id)
        .where(MembershipRole.membership_id.in_(ids))
    )
    roles: dict[UUID, list[str]] = {item_id: [] for item_id in ids}
    for membership_id, code in role_rows.all():
        roles[membership_id].append(code)
    branch_rows = await session.execute(
        select(MembershipBranch.membership_id, MembershipBranch.branch_id).where(
            MembershipBranch.membership_id.in_(ids)
        )
    )
    branches: dict[UUID, list[UUID]] = {item_id: [] for item_id in ids}
    for membership_id, branch_id in branch_rows.all():
        branches[membership_id].append(branch_id)
    views: list[MembershipView] = []
    for membership in memberships:
        user = users[membership.user_id]
        views.append(
            MembershipView(
                id=membership.id,
                user_id=user.id,
                email=user.email,
                full_name=user.full_name,
                status=membership.status,
                access_all_branches=membership.access_all_branches,
                role_codes=sorted(roles.get(membership.id, [])),
                branch_ids=sorted(branches.get(membership.id, []), key=str),
            )
        )
    return views


async def _membership(
    session: AsyncSession,
    ctx: TenantContext,
    membership_id: UUID,
) -> OrganizationMembership:
    membership = await session.get(OrganizationMembership, membership_id)
    if membership is None or membership.organization_id != ctx.organization_id:
        raise AppError(404, "Membership not found", code="not_found")
    return membership


async def _role(session: AsyncSession, organization_id: UUID, code: str) -> Role:
    role = await session.scalar(
        select(Role).where(Role.organization_id == organization_id, Role.code == code)
    )
    if role is None:
        raise AppError(422, "Unknown role", code="validation_error")
    return role


async def _permission(session: AsyncSession, code: str) -> Permission:
    permission = await session.scalar(select(Permission).where(Permission.code == code))
    if permission is None:
        raise AppError(422, "Unknown permission", code="validation_error")
    if permission.module == "platform":
        raise AppError(
            403,
            "Platform permissions cannot be granted in an organization",
            code="permission_denied",
        )
    return permission


def _assert_can_assign(ctx: TenantContext, role: Role) -> None:
    if role.code == "owner" and "org.manage" not in ctx.permissions:
        raise AppError(403, "Only an owner can assign the owner role", code="permission_denied")


async def _assert_can_edit(
    session: AsyncSession,
    ctx: TenantContext,
    membership: OrganizationMembership,
) -> None:
    if await _is_owner(session, membership.id) and "org.manage" not in ctx.permissions:
        raise AppError(
            403,
            "Only an owner can change an owner membership",
            code="permission_denied",
        )


async def _is_owner(session: AsyncSession, membership_id: UUID) -> bool:
    row = await session.scalar(
        select(MembershipRole.id)
        .join(Role, Role.id == MembershipRole.role_id)
        .where(MembershipRole.membership_id == membership_id, Role.code == "owner")
    )
    return row is not None


async def _active_owner_count(session: AsyncSession, organization_id: UUID) -> int:
    count = await session.scalar(
        select(func.count(MembershipRole.id))
        .join(Role, Role.id == MembershipRole.role_id)
        .join(OrganizationMembership, OrganizationMembership.id == MembershipRole.membership_id)
        .where(
            Role.organization_id == organization_id,
            Role.code == "owner",
            OrganizationMembership.status == "active",
        )
    )
    return int(count or 0)


async def _assert_branches_exist(
    session: AsyncSession,
    organization_id: UUID,
    branch_ids: list[UUID],
) -> None:
    if not branch_ids:
        return
    found = set(
        await session.scalars(
            select(Branch.id).where(
                Branch.organization_id == organization_id,
                Branch.id.in_(branch_ids),
            )
        )
    )
    missing = [str(branch_id) for branch_id in branch_ids if branch_id not in found]
    if missing:
        raise AppError(422, "One or more branches were not found", code="validation_error")
