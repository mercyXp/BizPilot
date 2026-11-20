from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas import WarehouseIn, WarehouseOut
from app.core.context import TenantContext
from app.core.db import get_db
from app.modules.authorization.deps import get_tenant_context, require_permission
from app.modules.tenancy.service import create_warehouse, list_warehouses

router = APIRouter(prefix="/warehouses", tags=["warehouses"])


def _out(row) -> WarehouseOut:
    return WarehouseOut(
        id=row.id,
        branch_id=row.branch_id,
        code=row.code,
        name=row.name,
        is_default=row.is_default,
        is_active=row.is_active,
    )


@router.post("", response_model=WarehouseOut, status_code=201)
async def create(
    body: WarehouseIn,
    ctx: TenantContext = Depends(require_permission("branches.manage")),
    session: AsyncSession = Depends(get_db),
) -> WarehouseOut:
    row = await create_warehouse(
        session,
        ctx,
        branch_id=body.branch_id,
        code=body.code,
        name=body.name,
        is_default=body.is_default,
    )
    return _out(row)


@router.get("", response_model=list[WarehouseOut])
async def list_all(
    branch_id: str | None = None,
    ctx: TenantContext = Depends(get_tenant_context),
    session: AsyncSession = Depends(get_db),
) -> list[WarehouseOut]:
    from uuid import UUID

    parsed = UUID(branch_id) if branch_id else None
    return [_out(row) for row in await list_warehouses(session, ctx, branch_id=parsed)]
