from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import TenantContext
from app.core.errors import AppError
from app.core.money import ZERO, money
from app.modules.accounting.posting import post_grn, post_supplier_invoice, post_supplier_payment
from app.modules.audit.service import get_idempotent, request_hash, store_idempotent, write_audit
from app.modules.catalogue.service import get_variant
from app.modules.inventory.service import next_document_number, receive
from app.modules.purchasing.models import (
    GoodsReceivedItem,
    GoodsReceivedNote,
    PurchaseOrder,
    PurchaseOrderItem,
    PurchaseRequisition,
    PurchaseRequisitionItem,
    Supplier,
    SupplierInvoice,
    SupplierPayment,
)
from app.modules.tenancy.service import get_warehouse


async def create_supplier(
    session: AsyncSession,
    ctx: TenantContext,
    *,
    name: str,
    code: str | None,
    payment_terms_days: int,
) -> Supplier:
    number = code.strip().upper() if code else await next_document_number(
        session, ctx, document_type="supplier", prefix="SUP"
    )
    row = Supplier(
        organization_id=ctx.organization_id,
        code=number,
        name=name.strip(),
        payment_terms_days=payment_terms_days,
        is_active=True,
    )
    session.add(row)
    try:
        await session.flush()
    except IntegrityError as exc:
        raise AppError(409, "Supplier code already exists", code="conflict") from exc
    return row


async def list_suppliers(session: AsyncSession, ctx: TenantContext) -> list[Supplier]:
    rows = await session.scalars(
        select(Supplier).where(Supplier.organization_id == ctx.organization_id).order_by(Supplier.name)
    )
    return list(rows)


async def create_requisition(
    session: AsyncSession, ctx: TenantContext, items: list[dict]
) -> PurchaseRequisition:
    number = await next_document_number(session, ctx, document_type="purchase_requisition", prefix="PR")
    row = PurchaseRequisition(
        organization_id=ctx.organization_id,
        branch_id=ctx.branch_id,
        status="draft",
        requested_by=ctx.user_id,
        document_number=number,
    )
    session.add(row)
    await session.flush()
    for item in items:
        await get_variant(session, ctx, item["variant_id"])
        session.add(
            PurchaseRequisitionItem(
                organization_id=ctx.organization_id,
                requisition_id=row.id,
                variant_id=item["variant_id"],
                qty=money(item["qty"]),
            )
        )
    await session.flush()
    return row


async def create_purchase_order(
    session: AsyncSession,
    ctx: TenantContext,
    *,
    supplier_id: UUID,
    items: list[dict],
) -> PurchaseOrder:
    supplier = await session.get(Supplier, supplier_id)
    if supplier is None:
        raise AppError(404, "Supplier not found", code="not_found")
    number = await next_document_number(session, ctx, document_type="purchase_order", prefix="PO")
    order = PurchaseOrder(
        organization_id=ctx.organization_id,
        branch_id=ctx.branch_id,
        supplier_id=supplier.id,
        status="draft",
        document_number=number,
    )
    session.add(order)
    await session.flush()
    for item in items:
        await get_variant(session, ctx, item["variant_id"])
        session.add(
            PurchaseOrderItem(
                organization_id=ctx.organization_id,
                purchase_order_id=order.id,
                variant_id=item["variant_id"],
                qty_ordered=money(item["qty"]),
                qty_received=ZERO,
                unit_cost=money(item["unit_cost"]),
            )
        )
    await session.flush()
    await write_audit(
        session, ctx, action="purchases.create", entity_type="purchase_order", entity_id=order.id
    )
    return order


async def submit_purchase_order(session: AsyncSession, ctx: TenantContext, order_id: UUID) -> PurchaseOrder:
    order = await _order(session, order_id)
    if order.status != "draft":
        raise AppError(409, "Only a draft purchase order can be submitted", code="conflict")
    order.status = "pending_approval"
    await session.flush()
    return order


async def approve_purchase_order(session: AsyncSession, ctx: TenantContext, order_id: UUID) -> PurchaseOrder:
    order = await _order(session, order_id)
    if order.status not in {"draft", "pending_approval"}:
        raise AppError(409, "Purchase order cannot be approved", code="conflict")
    order.status = "approved"
    order.ordered_at = datetime.now(UTC)
    await session.flush()
    await write_audit(
        session, ctx, action="purchases.approve", entity_type="purchase_order", entity_id=order.id
    )
    return order


async def post_goods_receipt(
    session: AsyncSession,
    ctx: TenantContext,
    *,
    purchase_order_id: UUID,
    warehouse_id: UUID,
    items: list[dict],
    idempotency_key: str,
) -> GoodsReceivedNote:
    digest = request_hash({"po": str(purchase_order_id), "items": items, "warehouse_id": str(warehouse_id)})
    cached = await get_idempotent(session, ctx, idempotency_key, digest)
    if cached:
        existing = await session.get(GoodsReceivedNote, UUID(cached["id"]))
        if existing is not None:
            return existing
    order = await _order(session, purchase_order_id)
    if order.status not in {"approved", "sent", "partial"}:
        raise AppError(409, "Purchase order is not approved for receiving", code="conflict")
    warehouse = await get_warehouse(session, ctx, warehouse_id)
    number = await next_document_number(session, ctx, document_type="grn", prefix="GRN")
    grn = GoodsReceivedNote(
        organization_id=ctx.organization_id,
        purchase_order_id=order.id,
        warehouse_id=warehouse.id,
        status="posted",
        document_number=number,
        received_at=datetime.now(UTC),
    )
    session.add(grn)
    await session.flush()
    inventory_value = ZERO
    for raw in items:
        po_item = await session.get(PurchaseOrderItem, raw["purchase_order_item_id"])
        if po_item is None or po_item.purchase_order_id != order.id:
            raise AppError(422, "Purchase order item not found", code="validation_error")
        accepted = money(raw["qty_accepted"])
        rejected = money(raw.get("qty_rejected") or 0)
        if accepted < ZERO or rejected < ZERO:
            raise AppError(422, "Quantities cannot be negative", code="validation_error")
        if po_item.qty_received + accepted > po_item.qty_ordered:
            raise AppError(409, "Over-receive is not allowed", code="conflict")
        po_item.qty_received = money(po_item.qty_received + accepted)
        session.add(
            GoodsReceivedItem(
                organization_id=ctx.organization_id,
                grn_id=grn.id,
                purchase_order_item_id=po_item.id,
                qty_accepted=accepted,
                qty_rejected=rejected,
            )
        )
        if accepted > ZERO:
            await receive(
                session,
                ctx,
                warehouse_id=warehouse.id,
                variant_id=po_item.variant_id,
                qty=accepted,
                unit_cost=po_item.unit_cost,
                source_type="purchase_receipt",
                source_id=grn.id,
                batch_id=raw.get("batch_id"),
            )
            inventory_value += money(accepted * po_item.unit_cost)
    po_items = list(
        await session.scalars(
            select(PurchaseOrderItem).where(PurchaseOrderItem.purchase_order_id == order.id)
        )
    )
    if all(item.qty_received >= item.qty_ordered for item in po_items):
        order.status = "received"
    else:
        order.status = "partial"
    await post_grn(
        session,
        ctx,
        grn_id=grn.id,
        branch_id=warehouse.branch_id,
        inventory_value=inventory_value,
    )
    await session.flush()
    await store_idempotent(
        session, ctx, idempotency_key, digest, {"id": str(grn.id), "document_number": grn.document_number}
    )
    return grn


async def create_supplier_invoice(
    session: AsyncSession,
    ctx: TenantContext,
    *,
    supplier_id: UUID,
    purchase_order_id: UUID | None,
    subtotal: Decimal,
    tax_total: Decimal,
    document_number: str | None,
) -> SupplierInvoice:
    supplier = await session.get(Supplier, supplier_id)
    if supplier is None:
        raise AppError(404, "Supplier not found", code="not_found")
    number = document_number or await next_document_number(
        session, ctx, document_type="supplier_invoice", prefix="SINV"
    )
    invoice = SupplierInvoice(
        organization_id=ctx.organization_id,
        supplier_id=supplier.id,
        purchase_order_id=purchase_order_id,
        document_number=number,
        status="posted",
        subtotal=money(subtotal),
        tax_total=money(tax_total),
        total=money(subtotal) + money(tax_total),
    )
    session.add(invoice)
    await session.flush()
    await post_supplier_invoice(
        session,
        ctx,
        invoice_id=invoice.id,
        supplier_id=supplier.id,
        subtotal=invoice.subtotal,
        tax=invoice.tax_total,
        total=invoice.total,
    )
    return invoice


async def pay_supplier(
    session: AsyncSession,
    ctx: TenantContext,
    *,
    supplier_id: UUID,
    invoice_id: UUID | None,
    amount: Decimal,
    method: str,
) -> SupplierPayment:
    supplier = await session.get(Supplier, supplier_id)
    if supplier is None:
        raise AppError(404, "Supplier not found", code="not_found")
    payment = SupplierPayment(
        organization_id=ctx.organization_id,
        supplier_id=supplier.id,
        invoice_id=invoice_id,
        amount=money(amount),
        status="completed",
        method=method,
        paid_at=datetime.now(UTC),
    )
    session.add(payment)
    await session.flush()
    if invoice_id:
        invoice = await session.get(SupplierInvoice, invoice_id)
        if invoice is not None:
            invoice.status = "paid"
    await post_supplier_payment(
        session,
        ctx,
        payment_id=payment.id,
        supplier_id=supplier.id,
        amount=payment.amount,
        method=method,
    )
    return payment


async def po_items(session: AsyncSession, order_id: UUID) -> list[PurchaseOrderItem]:
    return list(
        await session.scalars(
            select(PurchaseOrderItem).where(PurchaseOrderItem.purchase_order_id == order_id)
        )
    )


async def _order(session: AsyncSession, order_id: UUID) -> PurchaseOrder:
    order = await session.get(PurchaseOrder, order_id)
    if order is None:
        raise AppError(404, "Purchase order not found", code="not_found")
    return order
