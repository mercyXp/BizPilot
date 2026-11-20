from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas import BranchIn, BranchOut
from app.core.context import TenantContext
from app.core.db import get_db
from app.modules.authorization.deps import get_tenant_context, require_permission
from app.modules.tenancy.service import create_branch, get_branch, list_branches

router = APIRouter(prefix="/branches", tags=["branches"])


def _out(branch) -> BranchOut:
    return BranchOut(id=branch.id, code=branch.code, name=branch.name, is_active=branch.is_active)


@router.post("", response_model=BranchOut, status_code=201)
async def create(
    body: BranchIn,
    ctx: TenantContext = Depends(require_permission("branches.manage")),
    session: AsyncSession = Depends(get_db),
) -> BranchOut:
    branch = await create_branch(session, ctx, code=body.code, name=body.name, phone=body.phone)
    return _out(branch)


@router.get("", response_model=list[BranchOut])
async def list_all(
    ctx: TenantContext = Depends(get_tenant_context),
    session: AsyncSession = Depends(get_db),
) -> list[BranchOut]:
    return [_out(branch) for branch in await list_branches(session, ctx)]


@router.get("/{branch_id}", response_model=BranchOut)
async def get_one(
    branch_id: UUID,
    ctx: TenantContext = Depends(get_tenant_context),
    session: AsyncSession = Depends(get_db),
) -> BranchOut:
    return _out(await get_branch(session, ctx, branch_id))
