from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas import (
    AdjustmentIn,
    BalanceOut,
    BatchIn,
    BatchOut,
    CountIn,
    CountOut,
    MovementOut,
    TransferIn,
    TransferOut,
    TransferReceiveIn,
)
from app.core.context import TenantContext
from app.core.db import get_db
from app.modules.authorization.deps import require_permission
from app.modules.inventory.models import StockTransferItem
from app.modules.inventory.service import (
    adjust,
    create_batch,
    create_count,
    create_transfer,
    dispatch_transfer,
    list_balances,
    post_count,
    receive,
    receive_transfer,
)
from sqlalchemy import select

router = APIRouter(tags=["inventory"])


def _movement(row) -> MovementOut:
    return MovementOut(
        id=row.id,
        warehouse_id=row.warehouse_id,
        variant_id=row.variant_id,
        qty_delta=float(row.qty_delta),
        unit_cost=float(row.unit_cost),
        movement_type=row.movement_type,
        source_type=row.source_type,
    )


def _transfer(row) -> TransferOut:
    return TransferOut(
        id=row.id,
        document_number=row.document_number,
        status=row.status,
        source_warehouse_id=row.source_warehouse_id,
        dest_warehouse_id=row.dest_warehouse_id,
    )


@router.post("/inventory/adjustments", response_model=MovementOut, status_code=201)
async def create_adjustment(
    body: AdjustmentIn,
    ctx: TenantContext = Depends(require_permission("inventory.adjust", branch_scoped=True)),
    session: AsyncSession = Depends(get_db),
) -> MovementOut:
    if body.source_type != "adjustment":
        row = await receive(
            session,
            ctx,
            warehouse_id=body.warehouse_id,
            variant_id=body.variant_id,
            qty=Decimal(str(body.qty_delta)),
            unit_cost=Decimal(str(body.unit_cost)),
            source_type=body.source_type,
            source_id=None,
            batch_id=body.batch_id,
        )
        return _movement(row)
    row = await adjust(
        session,
        ctx,
        warehouse_id=body.warehouse_id,
        variant_id=body.variant_id,
        qty_delta=Decimal(str(body.qty_delta)),
        unit_cost=Decimal(str(body.unit_cost)),
        batch_id=body.batch_id,
    )
    return _movement(row)


@router.get("/stock-balances", response_model=list[BalanceOut])
async def balances(
    warehouse_id: UUID | None = None,
    ctx: TenantContext = Depends(require_permission("inventory.view")),
    session: AsyncSession = Depends(get_db),
) -> list[BalanceOut]:
    rows = await list_balances(session, ctx, warehouse_id=warehouse_id)
    return [
        BalanceOut(
            warehouse_id=row.warehouse_id,
            variant_id=row.variant_id,
            batch_id=row.batch_id,
            qty_on_hand=float(row.qty_on_hand),
            avg_unit_cost=float(row.avg_unit_cost),
        )
        for row in rows
    ]


@router.post("/product-batches", response_model=BatchOut, status_code=201)
async def add_batch(
    body: BatchIn,
    ctx: TenantContext = Depends(require_permission("catalogue.manage")),
    session: AsyncSession = Depends(get_db),
) -> BatchOut:
    row = await create_batch(
        session,
        ctx,
        variant_id=body.variant_id,
        batch_number=body.batch_number,
        expires_on=None,
        manufactured_on=None,
    )
    return BatchOut(id=row.id, variant_id=row.variant_id, batch_number=row.batch_number)


@router.post("/stock-transfers", response_model=TransferOut, status_code=201)
async def add_transfer(
    body: TransferIn,
    ctx: TenantContext = Depends(require_permission("inventory.transfer")),
    session: AsyncSession = Depends(get_db),
) -> TransferOut:
    row = await create_transfer(
        session,
        ctx,
        source_warehouse_id=body.source_warehouse_id,
        dest_warehouse_id=body.dest_warehouse_id,
        items=[item.model_dump() for item in body.items],
    )
    return _transfer(row)


@router.post("/stock-transfers/{transfer_id}/dispatch", response_model=TransferOut)
async def dispatch(
    transfer_id: UUID,
    ctx: TenantContext = Depends(require_permission("inventory.transfer")),
    session: AsyncSession = Depends(get_db),
) -> TransferOut:
    return _transfer(await dispatch_transfer(session, ctx, transfer_id))


@router.post("/stock-transfers/{transfer_id}/receive", response_model=TransferOut)
async def receive_items(
    transfer_id: UUID,
    body: TransferReceiveIn,
    ctx: TenantContext = Depends(require_permission("inventory.transfer")),
    session: AsyncSession = Depends(get_db),
) -> TransferOut:
    return _transfer(
        await receive_transfer(
            session,
            ctx,
            transfer_id,
            [item.model_dump() for item in body.items],
        )
    )


@router.get("/stock-transfers/{transfer_id}/items")
async def transfer_items(
    transfer_id: UUID,
    ctx: TenantContext = Depends(require_permission("inventory.transfer")),
    session: AsyncSession = Depends(get_db),
) -> list[dict]:
    rows = await session.scalars(
        select(StockTransferItem).where(StockTransferItem.transfer_id == transfer_id)
    )
    return [
        {
            "id": str(row.id),
            "variant_id": str(row.variant_id),
            "qty_sent": float(row.qty_sent),
            "qty_received": float(row.qty_received),
        }
        for row in rows
    ]


@router.post("/stock-counts", response_model=CountOut, status_code=201)
async def add_count(
    body: CountIn,
    ctx: TenantContext = Depends(require_permission("inventory.count")),
    session: AsyncSession = Depends(get_db),
) -> CountOut:
    row = await create_count(
        session,
        ctx,
        warehouse_id=body.warehouse_id,
        items=[item.model_dump() for item in body.items],
    )
    return CountOut(id=row.id, warehouse_id=row.warehouse_id, status=row.status)


@router.post("/stock-counts/{count_id}/post", response_model=CountOut)
async def finish_count(
    count_id: UUID,
    ctx: TenantContext = Depends(require_permission("inventory.count")),
    session: AsyncSession = Depends(get_db),
) -> CountOut:
    row = await post_count(session, ctx, count_id)
    return CountOut(id=row.id, warehouse_id=row.warehouse_id, status=row.status)
