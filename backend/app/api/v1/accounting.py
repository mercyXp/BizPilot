from uuid import UUID

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.ops_schemas import (
    AccountOut,
    BankAccountIn,
    BankAccountOut,
    BankTxIn,
    BankTxOut,
    ExpenseIn,
    ExpenseOut,
    JournalOut,
    ManualJournalIn,
    PeriodOut,
    ReconIn,
    TaxRateIn,
    TaxRateOut,
)
from app.core.context import TenantContext
from app.core.db import get_db
from app.modules.accounting.engine import post_manual, reverse
from app.modules.accounting.service import (
    add_bank_transaction,
    approve_expense,
    close_period,
    create_bank_account,
    create_expense,
    create_reconciliation,
    create_tax_rate,
    get_journal,
    journal_lines,
    list_accounts,
    list_journals,
    list_periods,
    profit_and_loss,
    trial_balance,
    balance_sheet,
)
from app.modules.audit.service import require_idempotency_key
from app.modules.authorization.deps import require_permission

router = APIRouter(tags=["accounting"])


def _journal(row) -> JournalOut:
    return JournalOut(
        id=row.id,
        entry_number=row.entry_number,
        status=row.status,
        source_type=row.source_type,
        description=row.description,
    )


@router.get("/accounts", response_model=list[AccountOut])
async def accounts(
    ctx: TenantContext = Depends(require_permission("accounting.reports.view")),
    session: AsyncSession = Depends(get_db),
) -> list[AccountOut]:
    return [
        AccountOut(id=row.id, code=row.code, name=row.name, type=row.type)
        for row in await list_accounts(session, ctx)
    ]


@router.get("/periods", response_model=list[PeriodOut])
async def periods(
    ctx: TenantContext = Depends(require_permission("accounting.reports.view")),
    session: AsyncSession = Depends(get_db),
) -> list[PeriodOut]:
    return [
        PeriodOut(
            id=row.id, name=row.name, starts_on=row.starts_on, ends_on=row.ends_on, status=row.status
        )
        for row in await list_periods(session, ctx)
    ]


@router.post("/periods/{period_id}/close", response_model=PeriodOut)
async def close(
    period_id: UUID,
    ctx: TenantContext = Depends(require_permission("accounting.period.close")),
    session: AsyncSession = Depends(get_db),
) -> PeriodOut:
    row = await close_period(session, ctx, period_id)
    return PeriodOut(
        id=row.id, name=row.name, starts_on=row.starts_on, ends_on=row.ends_on, status=row.status
    )


@router.post("/journals", response_model=JournalOut, status_code=201)
async def create_journal(
    body: ManualJournalIn,
    request: Request,
    ctx: TenantContext = Depends(require_permission("accounting.journal.post")),
    session: AsyncSession = Depends(get_db),
) -> JournalOut:
    key = require_idempotency_key(request)
    row = await post_manual(
        session,
        ctx,
        description=body.description,
        lines=[line.model_dump() for line in body.lines],
        idempotency_key=key,
    )
    return _journal(row)


@router.get("/journals", response_model=list[JournalOut])
async def journals(
    ctx: TenantContext = Depends(require_permission("accounting.reports.view")),
    session: AsyncSession = Depends(get_db),
) -> list[JournalOut]:
    return [_journal(row) for row in await list_journals(session, ctx)]


@router.get("/journals/{journal_id}")
async def journal(
    journal_id: UUID,
    ctx: TenantContext = Depends(require_permission("accounting.reports.view")),
    session: AsyncSession = Depends(get_db),
) -> dict:
    row = await get_journal(session, ctx, journal_id)
    lines = await journal_lines(session, journal_id)
    return {
        **_journal(row).model_dump(),
        "lines": [
            {
                "id": str(line.id),
                "account_id": str(line.account_id),
                "debit": float(line.debit),
                "credit": float(line.credit),
            }
            for line in lines
        ],
    }


@router.post("/journals/{journal_id}/reverse", response_model=JournalOut)
async def reverse_journal(
    journal_id: UUID,
    request: Request,
    ctx: TenantContext = Depends(require_permission("accounting.journal.post")),
    session: AsyncSession = Depends(get_db),
) -> JournalOut:
    key = require_idempotency_key(request)
    return _journal(await reverse(session, ctx, journal_id, idempotency_key=key))


@router.get("/reports/trial-balance")
async def tb(
    period_id: UUID | None = None,
    ctx: TenantContext = Depends(require_permission("accounting.reports.view")),
    session: AsyncSession = Depends(get_db),
) -> list[dict]:
    return await trial_balance(session, ctx, period_id)


@router.get("/reports/profit-and-loss")
async def pnl(
    period_id: UUID | None = None,
    ctx: TenantContext = Depends(require_permission("accounting.reports.view")),
    session: AsyncSession = Depends(get_db),
) -> dict:
    return await profit_and_loss(session, ctx, period_id)


@router.get("/reports/balance-sheet")
async def bs(
    period_id: UUID | None = None,
    ctx: TenantContext = Depends(require_permission("accounting.reports.view")),
    session: AsyncSession = Depends(get_db),
) -> dict:
    return await balance_sheet(session, ctx, period_id)


@router.post("/expenses", response_model=ExpenseOut, status_code=201)
async def expense(
    body: ExpenseIn,
    ctx: TenantContext = Depends(require_permission("expenses.create")),
    session: AsyncSession = Depends(get_db),
) -> ExpenseOut:
    row = await create_expense(
        session,
        ctx,
        vendor_name=body.vendor_name,
        amount=body.amount,
        tax_amount=body.tax_amount,
        incurred_on=body.incurred_on,
        payment_method=body.payment_method,
        account_id=body.account_id,
        lines=[],
    )
    return ExpenseOut(
        id=row.id, document_number=row.document_number, status=row.status, amount=float(row.amount)
    )


@router.post("/expenses/{expense_id}/approve", response_model=ExpenseOut)
async def expense_approve(
    expense_id: UUID,
    ctx: TenantContext = Depends(require_permission("expenses.approve")),
    session: AsyncSession = Depends(get_db),
) -> ExpenseOut:
    row = await approve_expense(session, ctx, expense_id)
    return ExpenseOut(
        id=row.id, document_number=row.document_number, status=row.status, amount=float(row.amount)
    )


@router.post("/bank-accounts", response_model=BankAccountOut, status_code=201)
async def bank_account(
    body: BankAccountIn,
    ctx: TenantContext = Depends(require_permission("accounting.journal.post")),
    session: AsyncSession = Depends(get_db),
) -> BankAccountOut:
    row = await create_bank_account(
        session, ctx, account_id=body.account_id, name=body.name, bank_name=body.bank_name
    )
    return BankAccountOut(id=row.id, name=row.name, account_id=row.account_id)


@router.post("/bank-transactions", response_model=BankTxOut, status_code=201)
async def bank_tx(
    body: BankTxIn,
    ctx: TenantContext = Depends(require_permission("accounting.journal.post")),
    session: AsyncSession = Depends(get_db),
) -> BankTxOut:
    row = await add_bank_transaction(
        session,
        ctx,
        bank_account_id=body.bank_account_id,
        posted_on=body.posted_on,
        amount=body.amount,
        description=body.description,
        external_ref=body.external_ref,
    )
    return BankTxOut(id=row.id, amount=float(row.amount), status=row.status)


@router.post("/bank-reconciliations", status_code=201)
async def recon(
    body: ReconIn,
    ctx: TenantContext = Depends(require_permission("accounting.journal.post")),
    session: AsyncSession = Depends(get_db),
) -> dict:
    row = await create_reconciliation(
        session,
        ctx,
        bank_account_id=body.bank_account_id,
        statement_date=body.statement_date,
        items=[item.model_dump() for item in body.items],
    )
    return {"id": str(row.id), "status": row.status}


@router.post("/tax-rates", response_model=TaxRateOut, status_code=201)
async def tax_rate(
    body: TaxRateIn,
    ctx: TenantContext = Depends(require_permission("org.settings")),
    session: AsyncSession = Depends(get_db),
) -> TaxRateOut:
    row = await create_tax_rate(
        session, ctx, code=body.code, name=body.name, rate=body.rate, inclusive=body.inclusive
    )
    return TaxRateOut(
        id=row.id, code=row.code, name=row.name, rate=float(row.rate), inclusive=row.inclusive
    )
