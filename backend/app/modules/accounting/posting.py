"""Domain-to-ledger mappings. Sales and purchasing call these, not journal tables."""

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import TenantContext
from app.core.money import ZERO, money
from app.modules.accounting.contracts import JournalLineCommand, PostCommand
from app.modules.accounting.coa import COMPONENT_ACCOUNT, DEDUCTION_CODES
from app.modules.accounting.engine import account_for, post
from app.modules.audit.service import write_outbox


async def request_post(session: AsyncSession, ctx: TenantContext, source_type: str, source_id: UUID) -> None:
    await write_outbox(
        session,
        ctx,
        "accounting_post_requested",
        {"source_type": source_type, "source_id": str(source_id)},
    )


def _line(account_id, debit=ZERO, credit=ZERO, **kwargs) -> JournalLineCommand:
    return JournalLineCommand(account_id=account_id, debit=money(debit), credit=money(credit), **kwargs)


async def post_sale(
    session: AsyncSession,
    ctx: TenantContext,
    *,
    sale_id: UUID,
    branch_id: UUID,
    customer_id: UUID | None,
    revenue: Decimal,
    tax: Decimal,
    cogs: Decimal,
    tenders: list[tuple[str, Decimal]],
) -> None:
    await request_post(session, ctx, "sale", sale_id)
    lines: list[JournalLineCommand] = []
    revenue_account = await account_for(session, ctx, "revenue")
    if revenue > ZERO:
        lines.append(_line(revenue_account.id, credit=revenue, branch_id=branch_id))
    if tax > ZERO:
        tax_account = await account_for(session, ctx, "tax_payable")
        lines.append(_line(tax_account.id, credit=tax, branch_id=branch_id))
    for method, amount in tenders:
        if amount <= ZERO:
            continue
        key = {"cash": "cash", "mobile_money": "mobile_money", "card": "bank", "bank_transfer": "bank"}.get(
            method, "cash"
        )
        if method == "store_credit":
            ar = await account_for(session, ctx, "ar")
            lines.append(
                _line(ar.id, debit=amount, branch_id=branch_id, party_type="customer", party_id=customer_id)
            )
        else:
            account = await account_for(session, ctx, key)
            lines.append(_line(account.id, debit=amount, branch_id=branch_id))
    if cogs > ZERO:
        cogs_account = await account_for(session, ctx, "cogs")
        inventory = await account_for(session, ctx, "inventory")
        lines.append(_line(cogs_account.id, debit=cogs, branch_id=branch_id))
        lines.append(_line(inventory.id, credit=cogs, branch_id=branch_id))
    if len(lines) < 2:
        return
    await post(
        session,
        ctx,
        PostCommand(
            source_type="sale",
            source_id=sale_id,
            description="POS sale",
            occurred_at=datetime.now(UTC),
            branch_id=branch_id,
            lines=tuple(lines),
        ),
    )


async def post_refund(
    session: AsyncSession,
    ctx: TenantContext,
    *,
    refund_id: UUID,
    branch_id: UUID,
    customer_id: UUID | None,
    amount: Decimal,
    tax: Decimal,
    restock_cogs: Decimal,
    method: str,
) -> None:
    await request_post(session, ctx, "refund", refund_id)
    revenue = await account_for(session, ctx, "revenue")
    lines = [_line(revenue.id, debit=amount - tax, branch_id=branch_id)]
    if tax > ZERO:
        tax_account = await account_for(session, ctx, "tax_payable")
        lines.append(_line(tax_account.id, debit=tax, branch_id=branch_id))
    if method == "store_credit":
        ar = await account_for(session, ctx, "ar")
        lines.append(
            _line(ar.id, credit=amount, branch_id=branch_id, party_type="customer", party_id=customer_id)
        )
    else:
        cash = await account_for(session, ctx, "cash" if method == "cash" else "mobile_money")
        lines.append(_line(cash.id, credit=amount, branch_id=branch_id))
    if restock_cogs > ZERO:
        inventory = await account_for(session, ctx, "inventory")
        cogs = await account_for(session, ctx, "cogs")
        lines.append(_line(inventory.id, debit=restock_cogs, branch_id=branch_id))
        lines.append(_line(cogs.id, credit=restock_cogs, branch_id=branch_id))
    await post(
        session,
        ctx,
        PostCommand(
            source_type="refund",
            source_id=refund_id,
            description="Sale refund",
            occurred_at=datetime.now(UTC),
            branch_id=branch_id,
            lines=tuple(lines),
        ),
    )


async def post_grn(
    session: AsyncSession,
    ctx: TenantContext,
    *,
    grn_id: UUID,
    branch_id: UUID | None,
    inventory_value: Decimal,
) -> None:
    await request_post(session, ctx, "grn", grn_id)
    if inventory_value <= ZERO:
        return
    inventory = await account_for(session, ctx, "inventory")
    grni = await account_for(session, ctx, "grni")
    await post(
        session,
        ctx,
        PostCommand(
            source_type="grn",
            source_id=grn_id,
            description="Goods received",
            occurred_at=datetime.now(UTC),
            branch_id=branch_id,
            lines=(
                _line(inventory.id, debit=inventory_value, branch_id=branch_id),
                _line(grni.id, credit=inventory_value, branch_id=branch_id),
            ),
        ),
    )


async def post_supplier_invoice(
    session: AsyncSession,
    ctx: TenantContext,
    *,
    invoice_id: UUID,
    supplier_id: UUID,
    subtotal: Decimal,
    tax: Decimal,
    total: Decimal,
) -> None:
    await request_post(session, ctx, "supplier_invoice", invoice_id)
    grni = await account_for(session, ctx, "grni")
    ap = await account_for(session, ctx, "ap")
    lines = [
        _line(grni.id, debit=subtotal),
        _line(ap.id, credit=total, party_type="supplier", party_id=supplier_id),
    ]
    if tax > ZERO:
        tax_input = await account_for(session, ctx, "tax_input")
        lines.insert(1, _line(tax_input.id, debit=tax))
    await post(
        session,
        ctx,
        PostCommand(
            source_type="supplier_invoice",
            source_id=invoice_id,
            description="Supplier invoice",
            occurred_at=datetime.now(UTC),
            branch_id=ctx.branch_id,
            lines=tuple(lines),
        ),
    )


async def post_supplier_payment(
    session: AsyncSession,
    ctx: TenantContext,
    *,
    payment_id: UUID,
    supplier_id: UUID,
    amount: Decimal,
    method: str,
) -> None:
    await request_post(session, ctx, "supplier_payment", payment_id)
    ap = await account_for(session, ctx, "ap")
    cash_key = "cash" if method == "cash" else "bank"
    cash = await account_for(session, ctx, cash_key)
    await post(
        session,
        ctx,
        PostCommand(
            source_type="supplier_payment",
            source_id=payment_id,
            description="Supplier payment",
            occurred_at=datetime.now(UTC),
            branch_id=ctx.branch_id,
            lines=(
                _line(ap.id, debit=amount, party_type="supplier", party_id=supplier_id),
                _line(cash.id, credit=amount),
            ),
        ),
    )


async def post_expense(
    session: AsyncSession,
    ctx: TenantContext,
    *,
    expense_id: UUID,
    branch_id: UUID | None,
    payment_method: str,
    lines: list[tuple[UUID, Decimal]],
    tax: Decimal,
) -> None:
    await request_post(session, ctx, "expense", expense_id)
    journal_lines = [_line(account_id, debit=amount, branch_id=branch_id) for account_id, amount in lines]
    total = sum((amount for _account, amount in lines), ZERO) + tax
    if tax > ZERO:
        tax_input = await account_for(session, ctx, "tax_input")
        journal_lines.append(_line(tax_input.id, debit=tax, branch_id=branch_id))
    cash_key = "cash" if payment_method == "cash" else "bank"
    cash = await account_for(session, ctx, cash_key)
    journal_lines.append(_line(cash.id, credit=total, branch_id=branch_id))
    await post(
        session,
        ctx,
        PostCommand(
            source_type="expense",
            source_id=expense_id,
            description="Expense",
            occurred_at=datetime.now(UTC),
            branch_id=branch_id,
            lines=tuple(journal_lines),
        ),
    )


async def post_payroll_run(
    session: AsyncSession,
    ctx: TenantContext,
    *,
    run_id: UUID,
    items: list[tuple[str, str, Decimal]],
) -> None:
    """items: (kind, code, amount) from payroll_components."""

    await request_post(session, ctx, "payroll_run", run_id)
    totals: dict[str, Decimal] = {}
    for kind, code, amount in items:
        if amount == ZERO:
            continue
        if kind == "earning":
            key = "salary"
        elif kind == "employer_contribution":
            key = "employer"
        else:
            key = DEDUCTION_CODES.get(code.upper(), COMPONENT_ACCOUNT["deduction"])
        totals[key] = totals.get(key, ZERO) + amount

    lines: list[JournalLineCommand] = []
    salary = totals.get("salary", ZERO)
    employer = totals.get("employer", ZERO)
    deductions = sum(
        (value for key, value in totals.items() if key not in {"salary", "employer"}),
        ZERO,
    )
    net = salary - deductions
    if salary > ZERO:
        account = await account_for(session, ctx, "salary")
        lines.append(_line(account.id, debit=salary))
    if employer > ZERO:
        expense = await account_for(session, ctx, "employer")
        payable = await account_for(session, ctx, "payroll_other")
        lines.append(_line(expense.id, debit=employer))
        lines.append(_line(payable.id, credit=employer))
    for key, amount in totals.items():
        if key in {"salary", "employer"} or amount <= ZERO:
            continue
        account = await account_for(session, ctx, key)
        lines.append(_line(account.id, credit=amount))
    if net > ZERO:
        clearing = await account_for(session, ctx, "net_pay")
        lines.append(_line(clearing.id, credit=net))
    if len(lines) < 2:
        return
    await post(
        session,
        ctx,
        PostCommand(
            source_type="payroll_run",
            source_id=run_id,
            description="Payroll run",
            occurred_at=datetime.now(UTC),
            branch_id=None,
            lines=tuple(lines),
        ),
    )


async def post_cash_variance(
    session: AsyncSession,
    ctx: TenantContext,
    *,
    session_id: UUID,
    branch_id: UUID,
    variance: Decimal,
) -> None:
    if variance == ZERO:
        return
    await request_post(session, ctx, "pos_variance", session_id)
    cash = await account_for(session, ctx, "cash")
    over_short = await account_for(session, ctx, "cash_variance")
    if variance > ZERO:
        lines = (
            _line(cash.id, debit=variance, branch_id=branch_id),
            _line(over_short.id, credit=variance, branch_id=branch_id),
        )
    else:
        amount = abs(variance)
        lines = (
            _line(over_short.id, debit=amount, branch_id=branch_id),
            _line(cash.id, credit=amount, branch_id=branch_id),
        )
    await post(
        session,
        ctx,
        PostCommand(
            source_type="pos_variance",
            source_id=session_id,
            description="POS cash variance",
            occurred_at=datetime.now(UTC),
            branch_id=branch_id,
            lines=lines,
        ),
    )
