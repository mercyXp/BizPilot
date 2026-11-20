from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import TenantContext
from app.core.errors import AppError
from app.core.ids import new_uuid
from app.core.money import ZERO, money
from app.modules.accounting.contracts import JournalLineCommand, PostCommand
from app.modules.accounting.models import (
    AccountingDocumentMap,
    AccountingPeriod,
    ChartAccount,
    JournalEntry,
    JournalLine,
    SubledgerBalance,
    TaxRate,
)
from app.modules.audit.service import write_audit, write_outbox
from app.modules.inventory.service import next_document_number


async def account_for(session: AsyncSession, ctx: TenantContext, map_key: str) -> ChartAccount:
    mapped = await session.scalar(
        select(AccountingDocumentMap).where(
            AccountingDocumentMap.organization_id == ctx.organization_id,
            AccountingDocumentMap.map_key == map_key,
        )
    )
    if mapped is None:
        raise AppError(422, f"Accounting map {map_key} is not configured", code="validation_error")
    account = await session.get(ChartAccount, mapped.account_id)
    if account is None:
        raise AppError(422, "Mapped account is missing", code="validation_error")
    return account


async def get_tax_rate(session: AsyncSession, ctx: TenantContext, tax_rate_id: UUID | None) -> TaxRate | None:
    if tax_rate_id is None:
        return None
    rate = await session.get(TaxRate, tax_rate_id)
    if rate is None:
        raise AppError(422, "Tax rate not found", code="validation_error")
    _ = ctx
    return rate


def compute_tax(amount: Decimal, rate: TaxRate | None) -> tuple[Decimal, Decimal]:
    """Return (net, tax) for a line amount treated as exclusive unless the rate is inclusive."""

    net = money(amount)
    if rate is None or rate.rate == ZERO:
        return net, ZERO
    factor = Decimal(rate.rate)
    if rate.inclusive:
        tax = money(net - (net / (Decimal("1") + factor)))
        return money(net - tax), tax
    tax = money(net * factor)
    return net, tax


async def post(session: AsyncSession, ctx: TenantContext, command: PostCommand) -> JournalEntry:
    if command.idempotency_key:
        existing = await session.scalar(
            select(JournalEntry).where(
                JournalEntry.organization_id == ctx.organization_id,
                JournalEntry.idempotency_key == command.idempotency_key,
            )
        )
        if existing is not None:
            return existing

    duplicate = await session.scalar(
        select(JournalEntry).where(
            JournalEntry.organization_id == ctx.organization_id,
            JournalEntry.source_type == command.source_type,
            JournalEntry.source_id == command.source_id,
            JournalEntry.status == "posted",
        )
    )
    if duplicate is not None:
        return duplicate

    if len(command.lines) < 2:
        raise AppError(422, "A journal needs at least two lines", code="validation_error")

    debit_total = ZERO
    credit_total = ZERO
    prepared: list[JournalLineCommand] = []
    for line in command.lines:
        debit = money(line.debit)
        credit = money(line.credit)
        if debit < ZERO or credit < ZERO:
            raise AppError(422, "Journal amounts cannot be negative", code="validation_error")
        if (debit == ZERO and credit == ZERO) or (debit > ZERO and credit > ZERO):
            raise AppError(422, "Each journal line must be debit or credit, not both", code="validation_error")
        debit_total += debit
        credit_total += credit
        prepared.append(
            JournalLineCommand(
                account_id=line.account_id,
                debit=debit,
                credit=credit,
                branch_id=line.branch_id if line.branch_id is not None else command.branch_id,
                party_type=line.party_type,
                party_id=line.party_id,
                tax_rate_id=line.tax_rate_id,
                memo=line.memo,
            )
        )
    if debit_total != credit_total:
        raise AppError(422, "Journal is not balanced", code="validation_error")
    if debit_total == ZERO:
        raise AppError(422, "Journal total cannot be zero", code="validation_error")

    occurred = command.occurred_at
    if occurred.tzinfo is None:
        occurred = occurred.replace(tzinfo=UTC)
    period = await _period_for(session, ctx, occurred.date())
    number = await next_document_number(session, ctx, document_type="journal", prefix="JE")
    entry = JournalEntry(
        organization_id=ctx.organization_id,
        period_id=period.id,
        entry_number=number,
        status="posted",
        source_type=command.source_type,
        source_id=command.source_id,
        reverses_journal_id=command.reverses_journal_id,
        description=command.description,
        posted_at=datetime.now(UTC),
        idempotency_key=command.idempotency_key,
    )
    session.add(entry)
    await session.flush()
    for line in prepared:
        account = await session.get(ChartAccount, line.account_id)
        if account is None or not account.is_postable:
            raise AppError(422, "Account is not postable", code="validation_error")
        session.add(
            JournalLine(
                organization_id=ctx.organization_id,
                journal_id=entry.id,
                account_id=account.id,
                branch_id=line.branch_id,
                debit=line.debit,
                credit=line.credit,
                party_type=line.party_type,
                party_id=line.party_id,
                tax_rate_id=line.tax_rate_id,
                memo=line.memo,
            )
        )
        if line.party_type and line.party_id:
            delta = line.debit - line.credit
            await _apply_subledger(session, ctx, line.party_type, line.party_id, account.id, delta)
    try:
        await session.flush()
    except DBAPIError as exc:
        raise AppError(409, "Journal could not be posted", code="conflict") from exc

    await write_outbox(
        session,
        ctx,
        "accounting_posted",
        {"journal_id": str(entry.id), "source_type": command.source_type, "source_id": str(command.source_id)},
    )
    await write_audit(
        session,
        ctx,
        action="accounting.journal.post",
        entity_type="journal_entry",
        entity_id=entry.id,
        after={"entry_number": entry.entry_number, "source_type": command.source_type},
    )
    return entry


async def reverse(
    session: AsyncSession, ctx: TenantContext, journal_id: UUID, *, idempotency_key: str | None
) -> JournalEntry:
    original = await session.get(JournalEntry, journal_id)
    if original is None:
        raise AppError(404, "Journal not found", code="not_found")
    if original.status != "posted":
        raise AppError(409, "Only posted journals can be reversed", code="conflict")
    if original.reversed_by_id is not None:
        existing = await session.get(JournalEntry, original.reversed_by_id)
        if existing is not None:
            return existing
    lines = list(
        await session.scalars(select(JournalLine).where(JournalLine.journal_id == original.id))
    )
    reversal_id = new_uuid()
    command = PostCommand(
        source_type="reversal",
        source_id=reversal_id,
        description=f"Reversal of {original.entry_number}",
        occurred_at=datetime.now(UTC),
        branch_id=None,
        lines=tuple(
            JournalLineCommand(
                account_id=line.account_id,
                debit=line.credit,
                credit=line.debit,
                branch_id=line.branch_id,
                party_type=line.party_type,
                party_id=line.party_id,
                tax_rate_id=line.tax_rate_id,
                memo=line.memo,
            )
            for line in lines
        ),
        idempotency_key=idempotency_key,
        reverses_journal_id=original.id,
    )
    reversal = await post(session, ctx, command)
    original.status = "reversed"
    original.reversed_by_id = reversal.id
    try:
        await session.flush()
    except DBAPIError as exc:
        raise AppError(409, "Posted journals are immutable", code="conflict") from exc
    return reversal


async def post_manual(
    session: AsyncSession,
    ctx: TenantContext,
    *,
    description: str,
    lines: list[dict],
    idempotency_key: str | None,
) -> JournalEntry:
    prepared = []
    for line in lines:
        prepared.append(
            JournalLineCommand(
                account_id=line["account_id"],
                debit=money(line.get("debit") or 0),
                credit=money(line.get("credit") or 0),
                branch_id=line.get("branch_id"),
                memo=line.get("memo"),
            )
        )
    return await post(
        session,
        ctx,
        PostCommand(
            source_type="manual",
            source_id=new_uuid(),
            description=description,
            occurred_at=datetime.now(UTC),
            branch_id=ctx.branch_id,
            lines=tuple(prepared),
            idempotency_key=idempotency_key,
        ),
    )


async def _period_for(session: AsyncSession, ctx: TenantContext, on: date) -> AccountingPeriod:
    period = await session.scalar(
        select(AccountingPeriod).where(
            AccountingPeriod.organization_id == ctx.organization_id,
            AccountingPeriod.starts_on <= on,
            AccountingPeriod.ends_on >= on,
        )
    )
    if period is None:
        raise AppError(422, "No accounting period covers this date", code="validation_error")
    if period.status != "open":
        raise AppError(409, "Accounting period is closed", code="conflict")
    return period


async def _apply_subledger(
    session: AsyncSession,
    ctx: TenantContext,
    party_type: str,
    party_id: UUID,
    account_id: UUID,
    delta: Decimal,
) -> None:
    row = await session.scalar(
        select(SubledgerBalance)
        .where(
            SubledgerBalance.organization_id == ctx.organization_id,
            SubledgerBalance.party_type == party_type,
            SubledgerBalance.party_id == party_id,
            SubledgerBalance.account_id == account_id,
        )
        .with_for_update()
    )
    if row is None:
        row = SubledgerBalance(
            organization_id=ctx.organization_id,
            party_type=party_type,
            party_id=party_id,
            account_id=account_id,
            balance=ZERO,
        )
        session.add(row)
        await session.flush()
    row.balance = money(row.balance + delta)


async def posted_totals(session: AsyncSession, ctx: TenantContext, journal_id: UUID) -> tuple[Decimal, Decimal]:
    debit = await session.scalar(
        select(func.coalesce(func.sum(JournalLine.debit), 0)).where(JournalLine.journal_id == journal_id)
    )
    credit = await session.scalar(
        select(func.coalesce(func.sum(JournalLine.credit), 0)).where(JournalLine.journal_id == journal_id)
    )
    _ = ctx
    return money(debit), money(credit)
