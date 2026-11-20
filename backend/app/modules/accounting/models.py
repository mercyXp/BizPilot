from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Uuid

from app.core.db import Base
from app.core.ids import new_uuid


class FiscalYear(Base):
    __tablename__ = "fiscal_years"
    __table_args__ = (
        UniqueConstraint("organization_id", "name", name="uq_fiscal_years_org_name"),
        CheckConstraint("status IN ('open', 'closed')", name="ck_fiscal_years_status"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=new_uuid)
    organization_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    starts_on: Mapped[date] = mapped_column(Date, nullable=False)
    ends_on: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, default="open", server_default=text("'open'")
    )


class AccountingPeriod(Base):
    __tablename__ = "accounting_periods"
    __table_args__ = (
        UniqueConstraint("organization_id", "fiscal_year_id", "name", name="uq_periods_org_year_name"),
        CheckConstraint("status IN ('open', 'closed', 'locked')", name="ck_periods_status"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=new_uuid)
    organization_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    fiscal_year_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("fiscal_years.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    starts_on: Mapped[date] = mapped_column(Date, nullable=False)
    ends_on: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, default="open", server_default=text("'open'")
    )


class ChartAccount(Base):
    __tablename__ = "chart_of_accounts"
    __table_args__ = (
        UniqueConstraint("organization_id", "code", name="uq_accounts_org_code"),
        CheckConstraint(
            "type IN ('asset', 'liability', 'equity', 'income', 'expense')",
            name="ck_accounts_type",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=new_uuid)
    organization_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    code: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    type: Mapped[str] = mapped_column(String(16), nullable=False)
    subtype: Mapped[str | None] = mapped_column(String(32))
    parent_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("chart_of_accounts.id"))
    is_postable: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=text("true")
    )
    is_system: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=text("false")
    )
    currency_code: Mapped[str] = mapped_column(
        String(3), nullable=False, default="ZMW", server_default=text("'ZMW'")
    )


class AccountingDocumentMap(Base):
    __tablename__ = "accounting_document_maps"
    __table_args__ = (
        UniqueConstraint("organization_id", "map_key", name="uq_document_maps_org_key"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=new_uuid)
    organization_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    map_key: Mapped[str] = mapped_column(String(64), nullable=False)
    account_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("chart_of_accounts.id"), nullable=False
    )


class TaxRate(Base):
    __tablename__ = "tax_rates"
    __table_args__ = (UniqueConstraint("organization_id", "code", name="uq_tax_rates_org_code"),)

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=new_uuid)
    organization_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    code: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    rate: Mapped[Decimal] = mapped_column(Numeric(9, 6), nullable=False)
    inclusive: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=text("false")
    )
    effective_from: Mapped[date | None] = mapped_column(Date)
    effective_to: Mapped[date | None] = mapped_column(Date)


class JournalEntry(Base):
    __tablename__ = "journal_entries"
    __table_args__ = (
        UniqueConstraint("organization_id", "entry_number", name="uq_journals_org_number"),
        CheckConstraint(
            "status IN ('draft', 'posted', 'reversed')",
            name="ck_journals_status",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=new_uuid)
    organization_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    period_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("accounting_periods.id"), nullable=False
    )
    entry_number: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, default="draft", server_default=text("'draft'")
    )
    source_type: Mapped[str] = mapped_column(String(32), nullable=False)
    source_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    reverses_journal_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("journal_entries.id")
    )
    reversed_by_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True))
    description: Mapped[str] = mapped_column(Text, nullable=False)
    posted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    idempotency_key: Mapped[str | None] = mapped_column(String(128))


class JournalLine(Base):
    __tablename__ = "journal_lines"
    __table_args__ = (
        CheckConstraint(
            "(debit = 0 AND credit > 0) OR (credit = 0 AND debit > 0)",
            name="ck_journal_lines_side",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=new_uuid)
    organization_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    journal_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("journal_entries.id", ondelete="CASCADE"), nullable=False
    )
    account_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("chart_of_accounts.id"), nullable=False
    )
    branch_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("branches.id"))
    debit: Mapped[Decimal] = mapped_column(Numeric(19, 4), nullable=False, server_default=text("0"))
    credit: Mapped[Decimal] = mapped_column(Numeric(19, 4), nullable=False, server_default=text("0"))
    party_type: Mapped[str | None] = mapped_column(String(32))
    party_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True))
    tax_rate_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("tax_rates.id"))
    memo: Mapped[str | None] = mapped_column(String(255))


class SubledgerBalance(Base):
    __tablename__ = "subledger_balances"
    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "party_type",
            "party_id",
            "account_id",
            name="uq_subledger_party_account",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=new_uuid)
    organization_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    party_type: Mapped[str] = mapped_column(String(32), nullable=False)
    party_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    account_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("chart_of_accounts.id"), nullable=False
    )
    balance: Mapped[Decimal] = mapped_column(Numeric(19, 4), nullable=False, server_default=text("0"))


class BankAccount(Base):
    __tablename__ = "bank_accounts"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=new_uuid)
    organization_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    account_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("chart_of_accounts.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    bank_name: Mapped[str | None] = mapped_column(String(200))
    account_number_masked: Mapped[str | None] = mapped_column(String(64))
    currency_code: Mapped[str] = mapped_column(
        String(3), nullable=False, default="ZMW", server_default=text("'ZMW'")
    )


class BankTransaction(Base):
    __tablename__ = "bank_transactions"
    __table_args__ = (
        CheckConstraint(
            "status IN ('unmatched', 'matched', 'ignored')",
            name="ck_bank_tx_status",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=new_uuid)
    organization_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    bank_account_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("bank_accounts.id"), nullable=False
    )
    posted_on: Mapped[date] = mapped_column(Date, nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(19, 4), nullable=False)
    description: Mapped[str | None] = mapped_column(String(255))
    external_ref: Mapped[str | None] = mapped_column(String(128))
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, default="unmatched", server_default=text("'unmatched'")
    )


class BankReconciliation(Base):
    __tablename__ = "bank_reconciliations"
    __table_args__ = (
        CheckConstraint("status IN ('open', 'completed')", name="ck_bank_recon_status"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=new_uuid)
    organization_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    bank_account_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("bank_accounts.id"), nullable=False
    )
    statement_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, default="open", server_default=text("'open'")
    )


class ReconciliationItem(Base):
    __tablename__ = "reconciliation_items"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=new_uuid)
    organization_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    reconciliation_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("bank_reconciliations.id", ondelete="CASCADE"), nullable=False
    )
    bank_transaction_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("bank_transactions.id"), nullable=False
    )
    journal_line_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("journal_lines.id")
    )


class Expense(Base):
    __tablename__ = "expenses"
    __table_args__ = (
        UniqueConstraint("organization_id", "document_number", name="uq_expenses_org_number"),
        CheckConstraint(
            "status IN ('draft', 'approved', 'posted', 'rejected')",
            name="ck_expenses_status",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=new_uuid)
    organization_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    branch_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("branches.id"))
    vendor_name: Mapped[str] = mapped_column(String(200), nullable=False)
    supplier_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("suppliers.id"))
    amount: Mapped[Decimal] = mapped_column(Numeric(19, 4), nullable=False)
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(19, 4), nullable=False, server_default=text("0"))
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, default="draft", server_default=text("'draft'")
    )
    incurred_on: Mapped[date] = mapped_column(Date, nullable=False)
    payment_method: Mapped[str] = mapped_column(
        String(32), nullable=False, default="cash", server_default=text("'cash'")
    )
    document_number: Mapped[str] = mapped_column(String(64), nullable=False)


class ExpenseLine(Base):
    __tablename__ = "expense_lines"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=new_uuid)
    organization_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    expense_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("expenses.id", ondelete="CASCADE"), nullable=False
    )
    account_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("chart_of_accounts.id"), nullable=False
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(19, 4), nullable=False)
    memo: Mapped[str | None] = mapped_column(String(255))
