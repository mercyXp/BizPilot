from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import TenantContext
from app.core.errors import AppError
from app.core.money import money
from app.modules.crm.models import Customer, CustomerCreditAccount, CustomerNote
from app.modules.inventory.service import next_document_number


async def create_customer(
    session: AsyncSession,
    ctx: TenantContext,
    *,
    name: str,
    code: str | None,
    phone: str | None,
    email: str | None,
    credit_limit: Decimal | None,
) -> Customer:
    number = code.strip().upper() if code else await next_document_number(
        session, ctx, document_type="customer", prefix="CUS"
    )
    customer = Customer(
        organization_id=ctx.organization_id,
        code=number,
        name=name.strip(),
        phone=phone,
        email=email.strip().lower() if email else None,
        is_active=True,
    )
    session.add(customer)
    try:
        await session.flush()
    except IntegrityError as exc:
        raise AppError(409, "Customer code already exists", code="conflict") from exc
    session.add(
        CustomerCreditAccount(
            organization_id=ctx.organization_id,
            customer_id=customer.id,
            credit_limit=money(credit_limit or 0),
            status="open",
            balance=money(0),
        )
    )
    await session.flush()
    return customer


async def list_customers(session: AsyncSession, ctx: TenantContext) -> list[Customer]:
    rows = await session.scalars(
        select(Customer)
        .where(Customer.organization_id == ctx.organization_id)
        .order_by(Customer.name)
    )
    return list(rows)


async def get_customer(session: AsyncSession, ctx: TenantContext, customer_id: UUID) -> Customer:
    customer = await session.get(Customer, customer_id)
    if customer is None:
        raise AppError(404, "Customer not found", code="not_found")
    _ = ctx
    return customer


async def get_credit(
    session: AsyncSession, ctx: TenantContext, customer_id: UUID
) -> CustomerCreditAccount:
    await get_customer(session, ctx, customer_id)
    row = await session.scalar(
        select(CustomerCreditAccount).where(CustomerCreditAccount.customer_id == customer_id)
    )
    if row is None:
        row = CustomerCreditAccount(
            organization_id=ctx.organization_id,
            customer_id=customer_id,
            credit_limit=money(0),
            status="open",
            balance=money(0),
        )
        session.add(row)
        await session.flush()
    return row


async def set_credit_limit(
    session: AsyncSession, ctx: TenantContext, customer_id: UUID, credit_limit: Decimal
) -> CustomerCreditAccount:
    row = await get_credit(session, ctx, customer_id)
    row.credit_limit = money(credit_limit)
    await session.flush()
    return row


async def assert_credit_available(
    session: AsyncSession, ctx: TenantContext, customer_id: UUID, amount: Decimal
) -> CustomerCreditAccount:
    row = await get_credit(session, ctx, customer_id)
    if row.status != "open":
        raise AppError(409, "Customer credit is not open", code="conflict")
    if money(row.balance + amount) > row.credit_limit:
        raise AppError(409, "Customer credit limit exceeded", code="conflict")
    return row


async def apply_credit_delta(
    session: AsyncSession, ctx: TenantContext, customer_id: UUID, delta: Decimal
) -> None:
    row = await get_credit(session, ctx, customer_id)
    row.balance = money(row.balance + delta)
    await session.flush()


async def add_note(
    session: AsyncSession, ctx: TenantContext, customer_id: UUID, body: str
) -> CustomerNote:
    await get_customer(session, ctx, customer_id)
    note = CustomerNote(
        organization_id=ctx.organization_id,
        customer_id=customer_id,
        body=body.strip(),
        created_by_user_id=ctx.user_id,
    )
    session.add(note)
    await session.flush()
    return note
