from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import TenantContext
from app.core.errors import AppError
from app.core.ids import new_uuid
from app.modules.catalogue.models import Product, ProductVariant
from app.modules.inventory.models import (
    DocumentSequence,
    ProductBatch,
    StockBalance,
    StockCount,
    StockCountItem,
    StockMovement,
    StockTransfer,
    StockTransferItem,
)
from app.modules.tenancy.models import Warehouse
from app.modules.tenancy.service import get_settings, get_warehouse

ZERO = Decimal("0")
PO_SOURCES = {"purchase_order", "po"}


async def apply_movement(
    session: AsyncSession,
    ctx: TenantContext,
    *,
    warehouse_id: UUID,
    variant_id: UUID,
    qty_delta: Decimal,
    unit_cost: Decimal,
    movement_type: str,
    source_type: str,
    source_id: UUID,
    batch_id: UUID | None = None,
) -> StockMovement:
    if source_type in PO_SOURCES:
        raise AppError(
            422,
            "Purchase orders do not receive stock. Record a goods receipt instead.",
            code="validation_error",
        )
    if qty_delta == ZERO:
        raise AppError(422, "Movement quantity cannot be zero", code="validation_error")

    warehouse = await get_warehouse(session, ctx, warehouse_id)
    if ctx.branch_id is not None and warehouse.branch_id != ctx.branch_id:
        raise AppError(403, "Warehouse is not in the selected branch", code="permission_denied")
    variant = await session.get(ProductVariant, variant_id)
    if variant is None:
        raise AppError(404, "Variant not found", code="not_found")
    product = await session.get(Product, variant.product_id)
    if product is None or not product.track_inventory:
        raise AppError(422, "This item does not track inventory", code="validation_error")
    if product.track_batches and batch_id is None:
        raise AppError(422, "A batch is required for this product", code="validation_error")
    if batch_id is not None:
        batch = await session.get(ProductBatch, batch_id)
        if batch is None or batch.variant_id != variant.id:
            raise AppError(422, "Batch not found", code="validation_error")

    balance = await _locked_balance(session, ctx, warehouse.id, variant.id, batch_id)
    new_qty = balance.qty_on_hand + qty_delta
    if qty_delta > ZERO:
        total = balance.qty_on_hand * balance.avg_unit_cost + qty_delta * unit_cost
        balance.avg_unit_cost = (total / new_qty) if new_qty else unit_cost
        cost = unit_cost
    else:
        cost = balance.avg_unit_cost
        if new_qty < ZERO:
            settings = (await get_settings(session, ctx)).settings
            inventory = settings.get("inventory") if isinstance(settings, dict) else {}
            allow = bool(inventory.get("allow_negative_stock")) if isinstance(inventory, dict) else False
            if not allow:
                raise AppError(409, "Negative stock is not allowed", code="conflict")
    balance.qty_on_hand = new_qty

    movement = StockMovement(
        organization_id=ctx.organization_id,
        warehouse_id=warehouse.id,
        branch_id=warehouse.branch_id,
        variant_id=variant.id,
        batch_id=batch_id,
        qty_delta=qty_delta,
        unit_cost=cost,
        movement_type=movement_type,
        source_type=source_type,
        source_id=source_id,
        created_by_user_id=ctx.user_id,
    )
    session.add(movement)
    try:
        await session.flush()
    except DBAPIError as exc:
        raise AppError(409, "Stock movement was rejected", code="conflict") from exc
    return movement


async def adjust(
    session: AsyncSession,
    ctx: TenantContext,
    *,
    warehouse_id: UUID,
    variant_id: UUID,
    qty_delta: Decimal,
    unit_cost: Decimal,
    batch_id: UUID | None,
) -> StockMovement:
    return await apply_movement(
        session,
        ctx,
        warehouse_id=warehouse_id,
        variant_id=variant_id,
        qty_delta=qty_delta,
        unit_cost=unit_cost,
        movement_type="adjustment",
        source_type="adjustment",
        source_id=new_uuid(),
        batch_id=batch_id,
    )


async def receive(
    session: AsyncSession,
    ctx: TenantContext,
    *,
    warehouse_id: UUID,
    variant_id: UUID,
    qty: Decimal,
    unit_cost: Decimal,
    source_type: str,
    source_id: UUID | None,
    batch_id: UUID | None,
) -> StockMovement:
    if qty <= ZERO:
        raise AppError(422, "Receipt quantity must be positive", code="validation_error")
    return await apply_movement(
        session,
        ctx,
        warehouse_id=warehouse_id,
        variant_id=variant_id,
        qty_delta=qty,
        unit_cost=unit_cost,
        movement_type="purchase_receipt" if source_type == "purchase_receipt" else source_type,
        source_type=source_type,
        source_id=source_id or new_uuid(),
        batch_id=batch_id,
    )


async def list_balances(
    session: AsyncSession,
    ctx: TenantContext,
    warehouse_id: UUID | None = None,
) -> list[StockBalance]:
    statement = (
        select(StockBalance)
        .join(Warehouse, Warehouse.id == StockBalance.warehouse_id)
        .where(StockBalance.organization_id == ctx.organization_id)
    )
    if warehouse_id is not None:
        await get_warehouse(session, ctx, warehouse_id)
        statement = statement.where(StockBalance.warehouse_id == warehouse_id)
    elif not ctx.access_all_branches:
        if not ctx.branch_ids:
            return []
        statement = statement.where(Warehouse.branch_id.in_(ctx.branch_ids))
    rows = await session.scalars(statement.order_by(StockBalance.updated_at.desc()))
    return list(rows)


async def movement_sum(
    session: AsyncSession, ctx: TenantContext, *, warehouse_id: UUID, variant_id: UUID
) -> Decimal:
    total = await session.scalar(
        select(func.coalesce(func.sum(StockMovement.qty_delta), 0)).where(
            StockMovement.organization_id == ctx.organization_id,
            StockMovement.warehouse_id == warehouse_id,
            StockMovement.variant_id == variant_id,
        )
    )
    return Decimal(total)


async def create_batch(
    session: AsyncSession,
    ctx: TenantContext,
    *,
    variant_id: UUID,
    batch_number: str,
    expires_on,
    manufactured_on,
) -> ProductBatch:
    variant = await session.get(ProductVariant, variant_id)
    if variant is None:
        raise AppError(404, "Variant not found", code="not_found")
    row = ProductBatch(
        organization_id=ctx.organization_id,
        variant_id=variant_id,
        batch_number=batch_number.strip(),
        expires_on=expires_on,
        manufactured_on=manufactured_on,
    )
    session.add(row)
    try:
        await session.flush()
    except IntegrityError as exc:
        raise AppError(409, "Batch number already exists", code="conflict") from exc
    return row


async def next_document_number(
    session: AsyncSession,
    ctx: TenantContext,
    *,
    document_type: str,
    prefix: str,
) -> str:
    row = await session.scalar(
        select(DocumentSequence)
        .where(
            DocumentSequence.organization_id == ctx.organization_id,
            DocumentSequence.branch_id.is_(None),
            DocumentSequence.document_type == document_type,
        )
        .with_for_update()
    )
    if row is None:
        row = DocumentSequence(
            organization_id=ctx.organization_id,
            branch_id=None,
            document_type=document_type,
            prefix=prefix,
            next_value=1,
        )
        session.add(row)
        await session.flush()
    value = row.next_value
    row.next_value = value + 1
    await session.flush()
    return f"{row.prefix}-{value:04d}"


async def create_transfer(
    session: AsyncSession,
    ctx: TenantContext,
    *,
    source_warehouse_id: UUID,
    dest_warehouse_id: UUID,
    items: list[dict],
) -> StockTransfer:
    source = await get_warehouse(session, ctx, source_warehouse_id)
    dest = await get_warehouse(session, ctx, dest_warehouse_id)
    if source.id == dest.id:
        raise AppError(422, "Source and destination warehouses must differ", code="validation_error")
    number = await next_document_number(session, ctx, document_type="stock_transfer", prefix="TR")
    transfer = StockTransfer(
        organization_id=ctx.organization_id,
        source_warehouse_id=source.id,
        dest_warehouse_id=dest.id,
        status="draft",
        document_number=number,
    )
    session.add(transfer)
    await session.flush()
    for item in items:
        qty = Decimal(str(item["qty"]))
        if qty <= ZERO:
            raise AppError(422, "Transfer quantity must be positive", code="validation_error")
        session.add(
            StockTransferItem(
                organization_id=ctx.organization_id,
                transfer_id=transfer.id,
                variant_id=item["variant_id"],
                batch_id=item.get("batch_id"),
                qty_sent=qty,
                qty_received=ZERO,
            )
        )
    await session.flush()
    return transfer


async def approve_transfer(
    session: AsyncSession, ctx: TenantContext, transfer_id: UUID
) -> StockTransfer:
    transfer = await _transfer(session, transfer_id)
    if transfer.status != "draft":
        raise AppError(409, "Only a draft transfer can be approved", code="conflict")
    transfer.status = "approved"
    await session.flush()
    return transfer


async def dispatch_transfer(
    session: AsyncSession, ctx: TenantContext, transfer_id: UUID
) -> StockTransfer:
    transfer = await _transfer(session, transfer_id)
    if transfer.status not in {"draft", "approved"}:
        raise AppError(409, "Transfer cannot be dispatched", code="conflict")
    items = await _transfer_items(session, transfer.id)
    for item in items:
        await apply_movement(
            session,
            ctx,
            warehouse_id=transfer.source_warehouse_id,
            variant_id=item.variant_id,
            qty_delta=-item.qty_sent,
            unit_cost=ZERO,
            movement_type="transfer_out",
            source_type="stock_transfer",
            source_id=transfer.id,
            batch_id=item.batch_id,
        )
    transfer.status = "dispatched"
    transfer.shipped_at = datetime.now(UTC)
    await session.flush()
    return transfer


async def receive_transfer(
    session: AsyncSession,
    ctx: TenantContext,
    transfer_id: UUID,
    receipts: list[dict],
) -> StockTransfer:
    transfer = await _transfer(session, transfer_id)
    if transfer.status not in {"dispatched", "partially_received"}:
        raise AppError(409, "Transfer is not awaiting receipt", code="conflict")
    items = {item.id: item for item in await _transfer_items(session, transfer.id)}
    for receipt in receipts:
        item = items.get(receipt["item_id"])
        if item is None:
            raise AppError(422, "Transfer item not found", code="validation_error")
        qty = Decimal(str(receipt["qty"]))
        remaining = item.qty_sent - item.qty_received
        if qty <= ZERO or qty > remaining:
            raise AppError(422, "Receipt quantity is not valid", code="validation_error")
        await apply_movement(
            session,
            ctx,
            warehouse_id=transfer.dest_warehouse_id,
            variant_id=item.variant_id,
            qty_delta=qty,
            unit_cost=ZERO,
            movement_type="transfer_in",
            source_type="stock_transfer",
            source_id=transfer.id,
            batch_id=item.batch_id,
        )
        item.qty_received += qty
    await session.flush()
    remaining_total = sum((item.qty_sent - item.qty_received) for item in items.values())
    if remaining_total == ZERO:
        transfer.status = "completed"
        transfer.received_at = datetime.now(UTC)
    else:
        transfer.status = "partially_received"
    await session.flush()
    return transfer


async def create_count(
    session: AsyncSession,
    ctx: TenantContext,
    *,
    warehouse_id: UUID,
    items: list[dict],
) -> StockCount:
    warehouse = await get_warehouse(session, ctx, warehouse_id)
    count = StockCount(
        organization_id=ctx.organization_id,
        warehouse_id=warehouse.id,
        status="in_progress",
    )
    session.add(count)
    await session.flush()
    for item in items:
        variant_id = item["variant_id"]
        batch_id = item.get("batch_id")
        balance = await session.scalar(
            select(StockBalance).where(
                StockBalance.organization_id == ctx.organization_id,
                StockBalance.warehouse_id == warehouse.id,
                StockBalance.variant_id == variant_id,
                StockBalance.batch_id.is_(batch_id) if batch_id is None else StockBalance.batch_id == batch_id,
            )
        )
        system_qty = balance.qty_on_hand if balance is not None else ZERO
        counted = item.get("counted_qty")
        session.add(
            StockCountItem(
                organization_id=ctx.organization_id,
                count_id=count.id,
                variant_id=variant_id,
                batch_id=batch_id,
                system_qty=system_qty,
                counted_qty=None if counted is None else Decimal(str(counted)),
            )
        )
    await session.flush()
    return count


async def post_count(session: AsyncSession, ctx: TenantContext, count_id: UUID) -> StockCount:
    count = await session.get(StockCount, count_id)
    if count is None:
        raise AppError(404, "Stock count not found", code="not_found")
    if count.status != "in_progress":
        raise AppError(409, "Count is not in progress", code="conflict")
    items = list(
        await session.scalars(select(StockCountItem).where(StockCountItem.count_id == count.id))
    )
    for item in items:
        if item.counted_qty is None:
            raise AppError(422, "Every count line needs a counted quantity", code="validation_error")
        variance = item.counted_qty - item.system_qty
        if variance == ZERO:
            continue
        await apply_movement(
            session,
            ctx,
            warehouse_id=count.warehouse_id,
            variant_id=item.variant_id,
            qty_delta=variance,
            unit_cost=ZERO,
            movement_type="count_variance",
            source_type="stock_count",
            source_id=count.id,
            batch_id=item.batch_id,
        )
    count.status = "posted"
    count.counted_at = datetime.now(UTC)
    await session.flush()
    return count


async def _locked_balance(
    session: AsyncSession,
    ctx: TenantContext,
    warehouse_id: UUID,
    variant_id: UUID,
    batch_id: UUID | None,
) -> StockBalance:
    if batch_id is None:
        statement = select(StockBalance).where(
            StockBalance.organization_id == ctx.organization_id,
            StockBalance.warehouse_id == warehouse_id,
            StockBalance.variant_id == variant_id,
            StockBalance.batch_id.is_(None),
        )
    else:
        statement = select(StockBalance).where(
            StockBalance.organization_id == ctx.organization_id,
            StockBalance.warehouse_id == warehouse_id,
            StockBalance.variant_id == variant_id,
            StockBalance.batch_id == batch_id,
        )
    row = await session.scalar(statement.with_for_update())
    if row is None:
        row = StockBalance(
            organization_id=ctx.organization_id,
            warehouse_id=warehouse_id,
            variant_id=variant_id,
            batch_id=batch_id,
            qty_on_hand=ZERO,
            qty_reserved=ZERO,
            avg_unit_cost=ZERO,
        )
        session.add(row)
        await session.flush()
        return await _locked_balance(session, ctx, warehouse_id, variant_id, batch_id)
    return row


async def _transfer(session: AsyncSession, transfer_id: UUID) -> StockTransfer:
    transfer = await session.get(StockTransfer, transfer_id)
    if transfer is None:
        raise AppError(404, "Transfer not found", code="not_found")
    return transfer


async def _transfer_items(session: AsyncSession, transfer_id: UUID) -> list[StockTransferItem]:
    return list(
        await session.scalars(
            select(StockTransferItem).where(StockTransferItem.transfer_id == transfer_id)
        )
    )


