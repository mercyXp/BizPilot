from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.ops_schemas import CreditIn, CreditOut, CustomerIn, CustomerOut, NoteIn
from app.core.context import TenantContext
from app.core.db import get_db
from app.modules.authorization.deps import require_permission
from app.modules.crm.service import (
    add_note,
    create_customer,
    get_credit,
    list_customers,
    set_credit_limit,
)

router = APIRouter(tags=["customers"])


def _customer(row) -> CustomerOut:
    return CustomerOut(id=row.id, code=row.code, name=row.name, is_active=row.is_active)


@router.post("/customers", response_model=CustomerOut, status_code=201)
async def create(
    body: CustomerIn,
    ctx: TenantContext = Depends(require_permission("customers.manage")),
    session: AsyncSession = Depends(get_db),
) -> CustomerOut:
    row = await create_customer(
        session,
        ctx,
        name=body.name,
        code=body.code,
        phone=body.phone,
        email=body.email,
        credit_limit=body.credit_limit,
    )
    return _customer(row)


@router.get("/customers", response_model=list[CustomerOut])
async def list_rows(
    ctx: TenantContext = Depends(require_permission("customers.manage")),
    session: AsyncSession = Depends(get_db),
) -> list[CustomerOut]:
    return [_customer(row) for row in await list_customers(session, ctx)]


@router.get("/customers/{customer_id}/credit", response_model=CreditOut)
async def credit(
    customer_id: UUID,
    ctx: TenantContext = Depends(require_permission("customers.manage")),
    session: AsyncSession = Depends(get_db),
) -> CreditOut:
    row = await get_credit(session, ctx, customer_id)
    return CreditOut(
        customer_id=row.customer_id,
        credit_limit=float(row.credit_limit),
        balance=float(row.balance),
        status=row.status,
    )


@router.put("/customers/{customer_id}/credit", response_model=CreditOut)
async def update_credit(
    customer_id: UUID,
    body: CreditIn,
    ctx: TenantContext = Depends(require_permission("customers.credit")),
    session: AsyncSession = Depends(get_db),
) -> CreditOut:
    row = await set_credit_limit(session, ctx, customer_id, body.credit_limit)
    return CreditOut(
        customer_id=row.customer_id,
        credit_limit=float(row.credit_limit),
        balance=float(row.balance),
        status=row.status,
    )


@router.post("/customers/{customer_id}/notes", status_code=201)
async def note(
    customer_id: UUID,
    body: NoteIn,
    ctx: TenantContext = Depends(require_permission("customers.manage")),
    session: AsyncSession = Depends(get_db),
) -> dict:
    row = await add_note(session, ctx, customer_id, body.body)
    return {"id": str(row.id)}
