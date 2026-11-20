import json
from uuid import UUID

from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import TenantContext
from app.core.errors import AppError
from app.core.ids import new_uuid
from app.core.rls import set_request_context
from app.modules.identity.models import User
from app.modules.tenancy.models import Branch, Organization, OrganizationMembership


async def create_organization(
    session: AsyncSession,
    user: User,
    *,
    name: str,
    legal_name: str | None,
    roles_payload: list[dict[str, object]],
) -> tuple[Organization, OrganizationMembership]:
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
                CAST(:roles AS jsonb)
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
        },
    )
    await set_request_context(session, user_id=user.id, organization_id=org_id)
    org = await session.get(Organization, org_id)
    membership = await session.get(OrganizationMembership, membership_id)
    if org is None or membership is None:
        raise AppError(500, "Organization bootstrap did not persist", code="internal_error")
    return org, membership


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


async def create_branch(
    session: AsyncSession,
    ctx: TenantContext,
    *,
    code: str,
    name: str,
    phone: str | None,
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
