from uuid import UUID

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.ops_schemas import PaymentOut, ReceiptOut, RefundIn, RefundOut, SaleOut
from app.core.context import TenantContext
from app.core.db import get_db
from app.modules.audit.service import require_idempotency_key
from app.modules.authorization.deps import require_permission
from app.modules.sales.service import (
    confirm_payment,
    get_receipt,
    get_sale,
    list_sales,
    refund_sale,
    sale_items,
    sale_payments,
)

router = APIRouter(tags=["sales"])


def _sale(row) -> SaleOut:
    return SaleOut(
        id=row.id,
        document_number=row.document_number,
        status=row.status,
        subtotal=float(row.subtotal),
        tax_total=float(row.tax_total),
        total=float(row.total),
        customer_id=row.customer_id,
    )


@router.get("/sales", response_model=list[SaleOut])
async def sales(
    ctx: TenantContext = Depends(require_permission("sales.view")),
    session: AsyncSession = Depends(get_db),
) -> list[SaleOut]:
    return [_sale(row) for row in await list_sales(session, ctx)]


@router.get("/sales/{sale_id}", response_model=SaleOut)
async def sale(
    sale_id: UUID,
    ctx: TenantContext = Depends(require_permission("sales.view")),
    session: AsyncSession = Depends(get_db),
) -> SaleOut:
    return _sale(await get_sale(session, ctx, sale_id))


@router.get("/sales/{sale_id}/items")
async def items(
    sale_id: UUID,
    ctx: TenantContext = Depends(require_permission("sales.view")),
    session: AsyncSession = Depends(get_db),
) -> list[dict]:
    await get_sale(session, ctx, sale_id)
    return [
        {"id": str(row.id), "variant_id": str(row.variant_id), "qty": float(row.qty), "line_total": float(row.line_total)}
        for row in await sale_items(session, sale_id)
    ]


@router.get("/sales/{sale_id}/payments", response_model=list[PaymentOut])
async def payments(
    sale_id: UUID,
    ctx: TenantContext = Depends(require_permission("sales.view")),
    session: AsyncSession = Depends(get_db),
) -> list[PaymentOut]:
    await get_sale(session, ctx, sale_id)
    return [
        PaymentOut(
            id=row.id,
            method=row.method,
            status=row.status,
            amount=float(row.amount),
            provider=row.provider,
            provider_ref=row.provider_ref,
        )
        for row in await sale_payments(session, sale_id)
    ]


@router.post("/sales/{sale_id}/refunds", response_model=RefundOut, status_code=201)
async def refunds(
    sale_id: UUID,
    body: RefundIn,
    request: Request,
    ctx: TenantContext = Depends(require_permission("sales.refund")),
    session: AsyncSession = Depends(get_db),
) -> RefundOut:
    key = require_idempotency_key(request)
    row = await refund_sale(
        session,
        ctx,
        sale_id,
        items=[item.model_dump() for item in body.items],
        reason=body.reason,
        restock=body.restock,
        idempotency_key=key,
    )
    return RefundOut(
        id=row.id, sale_id=row.sale_id, status=row.status, total=float(row.total), restock=row.restock
    )


@router.post("/payments/{payment_id}/confirm", response_model=PaymentOut)
async def confirm(
    payment_id: UUID,
    ctx: TenantContext = Depends(require_permission("sales.create")),
    session: AsyncSession = Depends(get_db),
) -> PaymentOut:
    row = await confirm_payment(session, ctx, payment_id)
    return PaymentOut(
        id=row.id,
        method=row.method,
        status=row.status,
        amount=float(row.amount),
        provider=row.provider,
        provider_ref=row.provider_ref,
    )


@router.get("/receipts/{receipt_id}", response_model=ReceiptOut)
async def receipt(
    receipt_id: UUID,
    ctx: TenantContext = Depends(require_permission("sales.view")),
    session: AsyncSession = Depends(get_db),
) -> ReceiptOut:
    row = await get_receipt(session, ctx, receipt_id)
    return ReceiptOut(
        id=row.id, sale_id=row.sale_id, document_number=row.document_number, payload_json=row.payload_json
    )
