from uuid import UUID

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.ops_schemas import (
    DocumentOut,
    GrnIn,
    PurchaseOrderIn,
    RequisitionIn,
    SupplierIn,
    SupplierInvoiceIn,
    SupplierOut,
    SupplierPaymentIn,
)
from app.core.context import TenantContext
from app.core.db import get_db
from app.modules.audit.service import require_idempotency_key
from app.modules.authorization.deps import require_permission
from app.modules.purchasing.service import (
    approve_purchase_order,
    create_purchase_order,
    create_requisition,
    create_supplier,
    create_supplier_invoice,
    list_suppliers,
    pay_supplier,
    po_items,
    post_goods_receipt,
    submit_purchase_order,
)

router = APIRouter(tags=["purchasing"])


@router.post("/suppliers", response_model=SupplierOut, status_code=201)
async def add_supplier(
    body: SupplierIn,
    ctx: TenantContext = Depends(require_permission("purchases.create")),
    session: AsyncSession = Depends(get_db),
) -> SupplierOut:
    row = await create_supplier(
        session, ctx, name=body.name, code=body.code, payment_terms_days=body.payment_terms_days
    )
    return SupplierOut(id=row.id, code=row.code, name=row.name)


@router.get("/suppliers", response_model=list[SupplierOut])
async def suppliers(
    ctx: TenantContext = Depends(require_permission("purchases.create")),
    session: AsyncSession = Depends(get_db),
) -> list[SupplierOut]:
    return [SupplierOut(id=row.id, code=row.code, name=row.name) for row in await list_suppliers(session, ctx)]


@router.post("/purchase-requisitions", response_model=DocumentOut, status_code=201)
async def requisition(
    body: RequisitionIn,
    ctx: TenantContext = Depends(require_permission("purchases.create")),
    session: AsyncSession = Depends(get_db),
) -> DocumentOut:
    row = await create_requisition(session, ctx, [item.model_dump() for item in body.items])
    return DocumentOut(id=row.id, document_number=row.document_number, status=row.status)


@router.post("/purchase-orders", response_model=DocumentOut, status_code=201)
async def purchase_order(
    body: PurchaseOrderIn,
    ctx: TenantContext = Depends(require_permission("purchases.create")),
    session: AsyncSession = Depends(get_db),
) -> DocumentOut:
    row = await create_purchase_order(
        session,
        ctx,
        supplier_id=body.supplier_id,
        items=[item.model_dump() for item in body.items],
    )
    return DocumentOut(id=row.id, document_number=row.document_number, status=row.status)


@router.post("/purchase-orders/{order_id}/submit", response_model=DocumentOut)
async def submit(
    order_id: UUID,
    ctx: TenantContext = Depends(require_permission("purchases.create")),
    session: AsyncSession = Depends(get_db),
) -> DocumentOut:
    row = await submit_purchase_order(session, ctx, order_id)
    return DocumentOut(id=row.id, document_number=row.document_number, status=row.status)


@router.post("/purchase-orders/{order_id}/approve", response_model=DocumentOut)
async def approve(
    order_id: UUID,
    ctx: TenantContext = Depends(require_permission("purchases.approve")),
    session: AsyncSession = Depends(get_db),
) -> DocumentOut:
    row = await approve_purchase_order(session, ctx, order_id)
    return DocumentOut(id=row.id, document_number=row.document_number, status=row.status)


@router.get("/purchase-orders/{order_id}/items")
async def items(
    order_id: UUID,
    ctx: TenantContext = Depends(require_permission("purchases.create")),
    session: AsyncSession = Depends(get_db),
) -> list[dict]:
    return [
        {
            "id": str(row.id),
            "variant_id": str(row.variant_id),
            "qty_ordered": float(row.qty_ordered),
            "qty_received": float(row.qty_received),
            "unit_cost": float(row.unit_cost),
        }
        for row in await po_items(session, order_id)
    ]


@router.post("/goods-receipts", response_model=DocumentOut, status_code=201)
async def grn(
    body: GrnIn,
    request: Request,
    ctx: TenantContext = Depends(require_permission("purchases.receive")),
    session: AsyncSession = Depends(get_db),
) -> DocumentOut:
    key = require_idempotency_key(request)
    row = await post_goods_receipt(
        session,
        ctx,
        purchase_order_id=body.purchase_order_id,
        warehouse_id=body.warehouse_id,
        items=[item.model_dump() for item in body.items],
        idempotency_key=key,
    )
    return DocumentOut(id=row.id, document_number=row.document_number, status=row.status)


@router.post("/supplier-invoices", response_model=DocumentOut, status_code=201)
async def invoice(
    body: SupplierInvoiceIn,
    ctx: TenantContext = Depends(require_permission("purchases.create")),
    session: AsyncSession = Depends(get_db),
) -> DocumentOut:
    row = await create_supplier_invoice(
        session,
        ctx,
        supplier_id=body.supplier_id,
        purchase_order_id=body.purchase_order_id,
        subtotal=body.subtotal,
        tax_total=body.tax_total,
        document_number=body.document_number,
    )
    return DocumentOut(id=row.id, document_number=row.document_number, status=row.status)


@router.post("/supplier-payments", response_model=DocumentOut, status_code=201)
async def payment(
    body: SupplierPaymentIn,
    ctx: TenantContext = Depends(require_permission("purchases.pay")),
    session: AsyncSession = Depends(get_db),
) -> DocumentOut:
    row = await pay_supplier(
        session,
        ctx,
        supplier_id=body.supplier_id,
        invoice_id=body.invoice_id,
        amount=body.amount,
        method=body.method,
    )
    return DocumentOut(id=row.id, document_number=str(row.id), status=row.status)
