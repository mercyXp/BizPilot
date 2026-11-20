from calendar import monthrange
from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import TenantContext
from app.core.errors import AppError
from app.core.money import ZERO, money
from app.modules.accounting.coa import TEMPLATE
from app.modules.accounting.models import (
    AccountingDocumentMap,
    AccountingPeriod,
    BankAccount,
    BankReconciliation,
    BankTransaction,
    ChartAccount,
    Expense,
    ExpenseLine,
    FiscalYear,
    JournalEntry,
    JournalLine,
    ReconciliationItem,
    TaxRate,
)
from app.modules.accounting.posting import post_expense
from app.modules.inventory.service import next_document_number
from app.modules.tenancy.service import get_settings


async def seed_books(session: AsyncSession, ctx: TenantContext, *, currency: str) -> None:
    existing = await session.scalar(
        select(ChartAccount).where(ChartAccount.organization_id == ctx.organization_id)
    )
    if existing is not None:
        return
    settings = (await get_settings(session, ctx)).settings
    start_month = 1
    if isinstance(settings, dict):
        start_month = int(settings.get("fiscal_year_start_month") or 1)
    year = date.today().year
    starts = date(year, start_month, 1)
    end_year = year if start_month == 1 else year + 1
    end_month = 12 if start_month == 1 else start_month - 1
    ends = date(end_year, end_month, monthrange(end_year, end_month)[1])
    fiscal = FiscalYear(
        organization_id=ctx.organization_id,
        name=str(year),
        starts_on=starts,
        ends_on=ends,
        status="open",
    )
    session.add(fiscal)
    await session.flush()
    cursor = starts
    while cursor <= ends:
        last = date(cursor.year, cursor.month, monthrange(cursor.year, cursor.month)[1])
        if last > ends:
            last = ends
        session.add(
            AccountingPeriod(
                organization_id=ctx.organization_id,
                fiscal_year_id=fiscal.id,
                name=cursor.strftime("%Y-%m"),
                starts_on=cursor,
                ends_on=last,
                status="open",
            )
        )
        if cursor.month == 12:
            cursor = date(cursor.year + 1, 1, 1)
        else:
            cursor = date(cursor.year, cursor.month + 1, 1)
    for code, name, type_, subtype, map_key in TEMPLATE:
        account = ChartAccount(
            organization_id=ctx.organization_id,
            code=code,
            name=name,
            type=type_,
            subtype=subtype,
            is_postable=True,
            is_system=True,
            currency_code=currency,
        )
        session.add(account)
        await session.flush()
        session.add(
            AccountingDocumentMap(
                organization_id=ctx.organization_id,
                map_key=map_key,
                account_id=account.id,
            )
        )
    session.add(
        TaxRate(
            organization_id=ctx.organization_id,
            code="DEV_ZERO",
            name="DEV_ONLY zero rate",
            rate=ZERO,
            inclusive=False,
            effective_from=starts,
        )
    )
    await session.flush()


async def list_accounts(session: AsyncSession, ctx: TenantContext) -> list[ChartAccount]:
    rows = await session.scalars(
        select(ChartAccount)
        .where(ChartAccount.organization_id == ctx.organization_id)
        .order_by(ChartAccount.code)
    )
    return list(rows)


async def list_periods(session: AsyncSession, ctx: TenantContext) -> list[AccountingPeriod]:
    rows = await session.scalars(
        select(AccountingPeriod)
        .where(AccountingPeriod.organization_id == ctx.organization_id)
        .order_by(AccountingPeriod.starts_on)
    )
    return list(rows)


async def close_period(session: AsyncSession, ctx: TenantContext, period_id: UUID) -> AccountingPeriod:
    period = await session.get(AccountingPeriod, period_id)
    if period is None:
        raise AppError(404, "Period not found", code="not_found")
    period.status = "closed"
    await session.flush()
    return period


async def list_journals(session: AsyncSession, ctx: TenantContext) -> list[JournalEntry]:
    rows = await session.scalars(
        select(JournalEntry)
        .where(JournalEntry.organization_id == ctx.organization_id)
        .order_by(JournalEntry.posted_at.desc().nullslast())
    )
    return list(rows)


async def get_journal(session: AsyncSession, ctx: TenantContext, journal_id: UUID) -> JournalEntry:
    row = await session.get(JournalEntry, journal_id)
    if row is None:
        raise AppError(404, "Journal not found", code="not_found")
    _ = ctx
    return row


async def journal_lines(session: AsyncSession, journal_id: UUID) -> list[JournalLine]:
    rows = await session.scalars(select(JournalLine).where(JournalLine.journal_id == journal_id))
    return list(rows)


async def create_expense(
    session: AsyncSession,
    ctx: TenantContext,
    *,
    vendor_name: str,
    amount: Decimal,
    tax_amount: Decimal,
    incurred_on: date,
    payment_method: str,
    account_id: UUID | None,
    lines: list[dict],
) -> Expense:
    number = await next_document_number(session, ctx, document_type="expense", prefix="EX")
    expense = Expense(
        organization_id=ctx.organization_id,
        branch_id=ctx.branch_id,
        vendor_name=vendor_name.strip(),
        amount=money(amount),
        tax_amount=money(tax_amount),
        status="draft",
        incurred_on=incurred_on,
        payment_method=payment_method,
        document_number=number,
    )
    session.add(expense)
    await session.flush()
    if not lines:
        if account_id is None:
            mapped = await session.scalar(
                select(AccountingDocumentMap).where(
                    AccountingDocumentMap.organization_id == ctx.organization_id,
                    AccountingDocumentMap.map_key == "expense",
                )
            )
            if mapped is None:
                raise AppError(422, "Expense account is not configured", code="validation_error")
            account_id = mapped.account_id
        lines = [{"account_id": account_id, "amount": amount, "memo": None}]
    for line in lines:
        session.add(
            ExpenseLine(
                organization_id=ctx.organization_id,
                expense_id=expense.id,
                account_id=line["account_id"],
                amount=money(line["amount"]),
                memo=line.get("memo"),
            )
        )
    await session.flush()
    return expense


async def approve_expense(session: AsyncSession, ctx: TenantContext, expense_id: UUID) -> Expense:
    expense = await session.get(Expense, expense_id)
    if expense is None:
        raise AppError(404, "Expense not found", code="not_found")
    if expense.status not in {"draft", "approved"}:
        raise AppError(409, "Expense cannot be approved", code="conflict")
    rows = list(await session.scalars(select(ExpenseLine).where(ExpenseLine.expense_id == expense.id)))
    await post_expense(
        session,
        ctx,
        expense_id=expense.id,
        branch_id=expense.branch_id,
        payment_method=expense.payment_method,
        lines=[(row.account_id, row.amount) for row in rows],
        tax=expense.tax_amount,
    )
    expense.status = "posted"
    await session.flush()
    return expense


async def create_bank_account(
    session: AsyncSession,
    ctx: TenantContext,
    *,
    account_id: UUID,
    name: str,
    bank_name: str | None,
) -> BankAccount:
    gl = await session.get(ChartAccount, account_id)
    if gl is None:
        raise AppError(422, "GL account not found", code="validation_error")
    row = BankAccount(
        organization_id=ctx.organization_id,
        account_id=account_id,
        name=name.strip(),
        bank_name=bank_name,
        currency_code=gl.currency_code,
    )
    session.add(row)
    await session.flush()
    return row


async def add_bank_transaction(
    session: AsyncSession,
    ctx: TenantContext,
    *,
    bank_account_id: UUID,
    posted_on: date,
    amount: Decimal,
    description: str | None,
    external_ref: str | None,
) -> BankTransaction:
    account = await session.get(BankAccount, bank_account_id)
    if account is None:
        raise AppError(404, "Bank account not found", code="not_found")
    row = BankTransaction(
        organization_id=ctx.organization_id,
        bank_account_id=bank_account_id,
        posted_on=posted_on,
        amount=money(amount),
        description=description,
        external_ref=external_ref,
        status="unmatched",
    )
    session.add(row)
    await session.flush()
    return row


async def create_reconciliation(
    session: AsyncSession,
    ctx: TenantContext,
    *,
    bank_account_id: UUID,
    statement_date: date,
    items: list[dict],
) -> BankReconciliation:
    recon = BankReconciliation(
        organization_id=ctx.organization_id,
        bank_account_id=bank_account_id,
        statement_date=statement_date,
        status="open",
    )
    session.add(recon)
    await session.flush()
    for item in items:
        tx = await session.get(BankTransaction, item["bank_transaction_id"])
        if tx is None or tx.status != "unmatched":
            raise AppError(409, "Bank line is not unmatched", code="conflict")
        line_id = item.get("journal_line_id")
        if line_id is None:
            raise AppError(422, "Unmatched items cannot post a reconciliation", code="validation_error")
        line = await session.get(JournalLine, line_id)
        if line is None:
            raise AppError(422, "Journal line not found", code="validation_error")
        tx.status = "matched"
        session.add(
            ReconciliationItem(
                organization_id=ctx.organization_id,
                reconciliation_id=recon.id,
                bank_transaction_id=tx.id,
                journal_line_id=line.id,
            )
        )
    recon.status = "completed"
    await session.flush()
    return recon


async def trial_balance(session: AsyncSession, ctx: TenantContext, period_id: UUID | None) -> list[dict]:
    statement = (
        select(
            ChartAccount.code,
            ChartAccount.name,
            ChartAccount.type,
            JournalLine.debit,
            JournalLine.credit,
            JournalEntry.period_id,
            JournalEntry.status,
        )
        .join(JournalEntry, JournalEntry.id == JournalLine.journal_id)
        .join(ChartAccount, ChartAccount.id == JournalLine.account_id)
        .where(JournalLine.organization_id == ctx.organization_id, JournalEntry.status == "posted")
    )
    if period_id is not None:
        statement = statement.where(JournalEntry.period_id == period_id)
    rows = (await session.execute(statement)).all()
    totals: dict[str, dict] = {}
    for code, name, type_, debit, credit, _period, _status in rows:
        bucket = totals.setdefault(code, {"code": code, "name": name, "type": type_, "debit": ZERO, "credit": ZERO})
        bucket["debit"] += money(debit)
        bucket["credit"] += money(credit)
    result = []
    for code in sorted(totals):
        row = totals[code]
        result.append(
            {
                "code": row["code"],
                "name": row["name"],
                "type": row["type"],
                "debit": float(row["debit"]),
                "credit": float(row["credit"]),
                "balance": float(row["debit"] - row["credit"]),
            }
        )
    return result


async def profit_and_loss(session: AsyncSession, ctx: TenantContext, period_id: UUID | None) -> dict:
    rows = await trial_balance(session, ctx, period_id)
    income = sum((Decimal(str(row["credit"] - row["debit"])) for row in rows if row["type"] == "income"), ZERO)
    expense = sum((Decimal(str(row["debit"] - row["credit"])) for row in rows if row["type"] == "expense"), ZERO)
    return {
        "income": float(income),
        "expense": float(expense),
        "net_income": float(income - expense),
        "lines": [row for row in rows if row["type"] in {"income", "expense"}],
    }


async def balance_sheet(session: AsyncSession, ctx: TenantContext, period_id: UUID | None) -> dict:
    rows = await trial_balance(session, ctx, period_id)
    pnl = await profit_and_loss(session, ctx, period_id)
    assets = [row for row in rows if row["type"] == "asset"]
    liabilities = [row for row in rows if row["type"] == "liability"]
    equity = [row for row in rows if row["type"] == "equity"]
    asset_total = sum((Decimal(str(row["balance"])) for row in assets), ZERO)
    liability_total = sum((Decimal(str(-row["balance"])) for row in liabilities), ZERO)
    equity_total = sum((Decimal(str(-row["balance"])) for row in equity), ZERO) + Decimal(
        str(pnl["net_income"])
    )
    return {
        "assets": float(asset_total),
        "liabilities": float(liability_total),
        "equity": float(equity_total),
        "balanced": money(asset_total) == money(liability_total + equity_total),
        "lines": rows,
    }


async def create_tax_rate(
    session: AsyncSession,
    ctx: TenantContext,
    *,
    code: str,
    name: str,
    rate: Decimal,
    inclusive: bool,
) -> TaxRate:
    if "official" in name.lower() or "zambia vat" in name.lower():
        raise AppError(422, "Do not label unverified rates as official", code="validation_error")
    row = TaxRate(
        organization_id=ctx.organization_id,
        code=code.strip().upper(),
        name=name.strip(),
        rate=money(rate),
        inclusive=inclusive,
    )
    session.add(row)
    await session.flush()
    return row
