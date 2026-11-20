from uuid import UUID

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.ops_schemas import (
    CashMovementIn,
    CloseSessionIn,
    PosSessionIn,
    PosSessionOut,
    SaleCompleteIn,
    SaleOut,
)
from app.core.context import TenantContext
from app.core.db import get_db
from app.modules.audit.service import require_idempotency_key
from app.modules.authorization.deps import require_permission
from app.modules.sales.service import add_cash_movement, close_session, complete_sale, open_session

router = APIRouter(prefix="/pos", tags=["pos"])


def _session(row) -> PosSessionOut:
    return PosSessionOut(
        id=row.id,
        branch_id=row.branch_id,
        warehouse_id=row.warehouse_id,
        status=row.status,
        opening_float=float(row.opening_float),
        closing_counted_cash=float(row.closing_counted_cash) if row.closing_counted_cash is not None else None,
    )


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


@router.post("/sessions", response_model=PosSessionOut, status_code=201)
async def open(
    body: PosSessionIn,
    ctx: TenantContext = Depends(require_permission("pos.session.open", branch_scoped=True)),
    session: AsyncSession = Depends(get_db),
) -> PosSessionOut:
    row = await open_session(
        session, ctx, warehouse_id=body.warehouse_id, opening_float=body.opening_float
    )
    return _session(row)


@router.post("/sessions/{session_id}/cash-movements", status_code=201)
async def cash(
    session_id: UUID,
    body: CashMovementIn,
    ctx: TenantContext = Depends(require_permission("sales.create")),
    session: AsyncSession = Depends(get_db),
) -> dict:
    row = await add_cash_movement(
        session, ctx, session_id, type=body.type, amount=body.amount, reason=body.reason
    )
    return {"id": str(row.id), "type": row.type, "amount": float(row.amount)}


@router.post("/sessions/{session_id}/close", response_model=PosSessionOut)
async def close(
    session_id: UUID,
    body: CloseSessionIn,
    ctx: TenantContext = Depends(require_permission("pos.session.close")),
    session: AsyncSession = Depends(get_db),
) -> PosSessionOut:
    return _session(await close_session(session, ctx, session_id, counted_cash=body.counted_cash))


@router.post("/sessions/{session_id}/sales", response_model=SaleOut, status_code=201)
async def sell(
    session_id: UUID,
    body: SaleCompleteIn,
    request: Request,
    ctx: TenantContext = Depends(require_permission("sales.create")),
    session: AsyncSession = Depends(get_db),
) -> SaleOut:
    key = require_idempotency_key(request)
    row = await complete_sale(
        session,
        ctx,
        pos_session_id=session_id,
        items=[item.model_dump() for item in body.items],
        payments=[item.model_dump() for item in body.payments],
        customer_id=body.customer_id,
        idempotency_key=key,
    )
    return _sale(row)
