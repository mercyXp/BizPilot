"""phase 6 sales, 7 purchasing/crm, 8 accounting, 9 payroll

Revision ID: 20261120_0004
Revises: 20261120_0003
Create Date: 2026-11-20
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

from app.core.ids import new_uuid

revision: str = "20261120_0004"
down_revision: Union[str, None] = "20261120_0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

UUID = postgresql.UUID(as_uuid=True)

TENANT_TABLES = (
    "audit_logs",
    "outbox_events",
    "idempotency_keys",
    "customers",
    "customer_addresses",
    "customer_credit_accounts",
    "customer_loyalty_accounts",
    "loyalty_transactions",
    "customer_notes",
    "suppliers",
    "fiscal_years",
    "accounting_periods",
    "chart_of_accounts",
    "accounting_document_maps",
    "tax_rates",
    "pos_sessions",
    "pos_cash_movements",
    "sales",
    "sale_items",
    "payments",
    "payment_allocations",
    "refunds",
    "refund_items",
    "receipts",
    "purchase_requisitions",
    "purchase_requisition_items",
    "purchase_orders",
    "purchase_order_items",
    "goods_received_notes",
    "goods_received_items",
    "supplier_invoices",
    "supplier_payments",
    "journal_entries",
    "journal_lines",
    "subledger_balances",
    "bank_accounts",
    "bank_transactions",
    "bank_reconciliations",
    "reconciliation_items",
    "expenses",
    "expense_lines",
    "departments",
    "employees",
    "attendance_records",
    "employee_shifts",
    "leave_requests",
    "payroll_components",
    "payroll_periods",
    "payroll_runs",
    "payroll_items",
)

_POLICY = """
CREATE POLICY {table}_tenant_isolation ON {table}
USING (
  organization_id = app_current_org()
  AND app_user_is_active_member(app_current_org(), app_current_user())
)
WITH CHECK (
  organization_id = app_current_org()
  AND app_user_is_active_member(app_current_org(), app_current_user())
)
"""


def _id() -> sa.Column:
    return sa.Column("id", UUID, primary_key=True)


def _org() -> sa.Column:
    return sa.Column("organization_id", UUID, nullable=False)


def upgrade() -> None:
    op.create_table(
        "audit_logs",
        _id(),
        sa.Column("organization_id", UUID),
        sa.Column("actor_user_id", UUID),
        sa.Column("action", sa.String(128), nullable=False),
        sa.Column("entity_type", sa.String(64), nullable=False),
        sa.Column("entity_id", UUID),
        sa.Column("before_json", postgresql.JSONB()),
        sa.Column("after_json", postgresql.JSONB()),
        sa.Column("ip", sa.String(64)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"]),
    )
    op.create_table(
        "outbox_events",
        _id(),
        _org(),
        sa.Column("event_type", sa.String(128), nullable=False),
        sa.Column("payload_json", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("status", sa.String(32), nullable=False, server_default=sa.text("'pending'")),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("available_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
    )
    op.create_table(
        "idempotency_keys",
        _id(),
        _org(),
        sa.Column("key", sa.String(128), nullable=False),
        sa.Column("request_hash", sa.String(128), nullable=False),
        sa.Column("response_json", postgresql.JSONB()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("organization_id", "key", name="uq_idempotency_org_key"),
    )
    op.create_table(
        "customers",
        _id(),
        _org(),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("phone", sa.String(32)),
        sa.Column("email", sa.String(320)),
        sa.Column("tax_id", sa.String(64)),
        sa.Column("address_json", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("organization_id", "code", name="uq_customers_org_code"),
    )
    op.create_table(
        "customer_addresses",
        _id(),
        _org(),
        sa.Column("customer_id", UUID, nullable=False),
        sa.Column("label", sa.String(64), nullable=False),
        sa.Column("address_json", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"], ondelete="CASCADE"),
    )
    op.create_table(
        "customer_credit_accounts",
        _id(),
        _org(),
        sa.Column("customer_id", UUID, nullable=False),
        sa.Column("credit_limit", sa.Numeric(19, 4), nullable=False, server_default=sa.text("0")),
        sa.Column("status", sa.String(16), nullable=False, server_default=sa.text("'open'")),
        sa.Column("balance", sa.Numeric(19, 4), nullable=False, server_default=sa.text("0")),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("customer_id", name="uq_credit_accounts_customer"),
    )
    op.create_table(
        "customer_loyalty_accounts",
        _id(),
        _org(),
        sa.Column("customer_id", UUID, nullable=False),
        sa.Column("points_balance", sa.Numeric(19, 4), nullable=False, server_default=sa.text("0")),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"], ondelete="CASCADE"),
    )
    op.create_table(
        "loyalty_transactions",
        _id(),
        _org(),
        sa.Column("account_id", UUID, nullable=False),
        sa.Column("delta", sa.Numeric(19, 4), nullable=False),
        sa.Column("source_type", sa.String(32), nullable=False),
        sa.Column("source_id", UUID, nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["account_id"], ["customer_loyalty_accounts.id"]),
    )
    op.create_table(
        "customer_notes",
        _id(),
        _org(),
        sa.Column("customer_id", UUID, nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("created_by_user_id", UUID, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"]),
    )
    op.create_table(
        "suppliers",
        _id(),
        _org(),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("phone", sa.String(32)),
        sa.Column("email", sa.String(320)),
        sa.Column("tax_id", sa.String(64)),
        sa.Column("address_json", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("payment_terms_days", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("organization_id", "code", name="uq_suppliers_org_code"),
    )
    op.create_table(
        "fiscal_years",
        _id(),
        _org(),
        sa.Column("name", sa.String(64), nullable=False),
        sa.Column("starts_on", sa.Date(), nullable=False),
        sa.Column("ends_on", sa.Date(), nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default=sa.text("'open'")),
        sa.CheckConstraint("status IN ('open', 'closed')", name="ck_fiscal_years_status"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("organization_id", "name", name="uq_fiscal_years_org_name"),
    )
    op.create_table(
        "accounting_periods",
        _id(),
        _org(),
        sa.Column("fiscal_year_id", UUID, nullable=False),
        sa.Column("name", sa.String(64), nullable=False),
        sa.Column("starts_on", sa.Date(), nullable=False),
        sa.Column("ends_on", sa.Date(), nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default=sa.text("'open'")),
        sa.CheckConstraint("status IN ('open', 'closed', 'locked')", name="ck_periods_status"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["fiscal_year_id"], ["fiscal_years.id"]),
        sa.UniqueConstraint("organization_id", "fiscal_year_id", "name", name="uq_periods_org_year_name"),
    )
    op.create_table(
        "chart_of_accounts",
        _id(),
        _org(),
        sa.Column("code", sa.String(32), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("type", sa.String(16), nullable=False),
        sa.Column("subtype", sa.String(32)),
        sa.Column("parent_id", UUID),
        sa.Column("is_postable", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("is_system", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("currency_code", sa.String(3), nullable=False, server_default=sa.text("'ZMW'")),
        sa.CheckConstraint(
            "type IN ('asset', 'liability', 'equity', 'income', 'expense')",
            name="ck_accounts_type",
        ),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["parent_id"], ["chart_of_accounts.id"]),
        sa.UniqueConstraint("organization_id", "code", name="uq_accounts_org_code"),
    )
    op.create_table(
        "accounting_document_maps",
        _id(),
        _org(),
        sa.Column("map_key", sa.String(64), nullable=False),
        sa.Column("account_id", UUID, nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["account_id"], ["chart_of_accounts.id"]),
        sa.UniqueConstraint("organization_id", "map_key", name="uq_document_maps_org_key"),
    )
    op.create_table(
        "tax_rates",
        _id(),
        _org(),
        sa.Column("code", sa.String(32), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("rate", sa.Numeric(9, 6), nullable=False),
        sa.Column("inclusive", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("effective_from", sa.Date()),
        sa.Column("effective_to", sa.Date()),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("organization_id", "code", name="uq_tax_rates_org_code"),
    )
    op.create_table(
        "pos_sessions",
        _id(),
        _org(),
        sa.Column("branch_id", UUID, nullable=False),
        sa.Column("warehouse_id", UUID, nullable=False),
        sa.Column("opened_by_user_id", UUID, nullable=False),
        sa.Column("closed_by_user_id", UUID),
        sa.Column("status", sa.String(16), nullable=False, server_default=sa.text("'open'")),
        sa.Column("opening_float", sa.Numeric(19, 4), nullable=False),
        sa.Column("closing_counted_cash", sa.Numeric(19, 4)),
        sa.Column("opened_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("closed_at", sa.DateTime(timezone=True)),
        sa.CheckConstraint("status IN ('open', 'closed')", name="ck_pos_sessions_status"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["branch_id"], ["branches.id"]),
        sa.ForeignKeyConstraint(["warehouse_id"], ["warehouses.id"]),
        sa.ForeignKeyConstraint(["opened_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["closed_by_user_id"], ["users.id"]),
    )
    op.create_table(
        "pos_cash_movements",
        _id(),
        _org(),
        sa.Column("session_id", UUID, nullable=False),
        sa.Column("type", sa.String(16), nullable=False),
        sa.Column("amount", sa.Numeric(19, 4), nullable=False),
        sa.Column("reason", sa.String(255)),
        sa.CheckConstraint("type IN ('in', 'out', 'sale', 'refund', 'variance')", name="ck_pos_cash_type"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["session_id"], ["pos_sessions.id"]),
    )
    op.create_table(
        "sales",
        _id(),
        _org(),
        sa.Column("branch_id", UUID, nullable=False),
        sa.Column("session_id", UUID),
        sa.Column("customer_id", UUID),
        sa.Column("document_number", sa.String(64), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("sale_type", sa.String(16), nullable=False, server_default=sa.text("'pos'")),
        sa.Column("subtotal", sa.Numeric(19, 4), nullable=False),
        sa.Column("discount_total", sa.Numeric(19, 4), nullable=False, server_default=sa.text("0")),
        sa.Column("tax_total", sa.Numeric(19, 4), nullable=False, server_default=sa.text("0")),
        sa.Column("total", sa.Numeric(19, 4), nullable=False),
        sa.Column("currency_code", sa.String(3), nullable=False, server_default=sa.text("'ZMW'")),
        sa.Column("idempotency_key", sa.String(128)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.CheckConstraint(
            "status IN ('draft', 'awaiting_payment', 'completed', 'voided', 'refunded', 'partially_refunded')",
            name="ck_sales_status",
        ),
        sa.CheckConstraint("sale_type IN ('pos', 'invoice')", name="ck_sales_type"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["branch_id"], ["branches.id"]),
        sa.ForeignKeyConstraint(["session_id"], ["pos_sessions.id"]),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"]),
        sa.UniqueConstraint("organization_id", "document_number", name="uq_sales_org_number"),
    )
    op.execute(
        """
        CREATE UNIQUE INDEX uq_sales_org_idempotency
        ON sales (organization_id, idempotency_key)
        WHERE idempotency_key IS NOT NULL
        """
    )
    op.create_table(
        "sale_items",
        _id(),
        _org(),
        sa.Column("sale_id", UUID, nullable=False),
        sa.Column("variant_id", UUID, nullable=False),
        sa.Column("description", sa.String(255), nullable=False),
        sa.Column("qty", sa.Numeric(19, 4), nullable=False),
        sa.Column("uom_id", UUID, nullable=False),
        sa.Column("unit_price", sa.Numeric(19, 4), nullable=False),
        sa.Column("discount_amount", sa.Numeric(19, 4), nullable=False, server_default=sa.text("0")),
        sa.Column("tax_rate_id", UUID),
        sa.Column("tax_amount", sa.Numeric(19, 4), nullable=False, server_default=sa.text("0")),
        sa.Column("line_total", sa.Numeric(19, 4), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["sale_id"], ["sales.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["variant_id"], ["product_variants.id"]),
        sa.ForeignKeyConstraint(["uom_id"], ["units_of_measure.id"]),
        sa.ForeignKeyConstraint(["tax_rate_id"], ["tax_rates.id"]),
    )
    op.create_table(
        "payments",
        _id(),
        _org(),
        sa.Column("sale_id", UUID),
        sa.Column("customer_id", UUID),
        sa.Column("method", sa.String(32), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("amount", sa.Numeric(19, 4), nullable=False),
        sa.Column("provider", sa.String(64)),
        sa.Column("provider_ref", sa.String(128)),
        sa.Column("received_at", sa.DateTime(timezone=True)),
        sa.CheckConstraint(
            "method IN ('cash', 'mobile_money', 'card', 'bank_transfer', 'store_credit')",
            name="ck_payments_method",
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'completed', 'failed', 'cancelled')",
            name="ck_payments_status",
        ),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["sale_id"], ["sales.id"]),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"]),
    )
    op.create_table(
        "payment_allocations",
        _id(),
        _org(),
        sa.Column("payment_id", UUID, nullable=False),
        sa.Column("source_type", sa.String(32), nullable=False),
        sa.Column("source_id", UUID, nullable=False),
        sa.Column("amount", sa.Numeric(19, 4), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["payment_id"], ["payments.id"], ondelete="CASCADE"),
    )
    op.create_table(
        "refunds",
        _id(),
        _org(),
        sa.Column("sale_id", UUID, nullable=False),
        sa.Column("reason", sa.String(255)),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("total", sa.Numeric(19, 4), nullable=False),
        sa.Column("restock", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("idempotency_key", sa.String(128)),
        sa.CheckConstraint("status IN ('completed', 'pending')", name="ck_refunds_status"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["sale_id"], ["sales.id"]),
    )
    op.create_table(
        "refund_items",
        _id(),
        _org(),
        sa.Column("refund_id", UUID, nullable=False),
        sa.Column("sale_item_id", UUID, nullable=False),
        sa.Column("qty", sa.Numeric(19, 4), nullable=False),
        sa.Column("amount", sa.Numeric(19, 4), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["refund_id"], ["refunds.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["sale_item_id"], ["sale_items.id"]),
    )
    op.create_table(
        "receipts",
        _id(),
        _org(),
        sa.Column("sale_id", UUID, nullable=False),
        sa.Column("document_number", sa.String(64), nullable=False),
        sa.Column("payload_json", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("pdf_object_key", sa.String(512)),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["sale_id"], ["sales.id"]),
        sa.UniqueConstraint("organization_id", "document_number", name="uq_receipts_org_number"),
    )
    op.create_table(
        "purchase_requisitions",
        _id(),
        _org(),
        sa.Column("branch_id", UUID),
        sa.Column("status", sa.String(16), nullable=False, server_default=sa.text("'draft'")),
        sa.Column("requested_by", UUID, nullable=False),
        sa.Column("document_number", sa.String(64), nullable=False),
        sa.CheckConstraint(
            "status IN ('draft', 'submitted', 'approved', 'cancelled')", name="ck_pr_status"
        ),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["branch_id"], ["branches.id"]),
        sa.ForeignKeyConstraint(["requested_by"], ["users.id"]),
        sa.UniqueConstraint("organization_id", "document_number", name="uq_pr_org_number"),
    )
    op.create_table(
        "purchase_requisition_items",
        _id(),
        _org(),
        sa.Column("requisition_id", UUID, nullable=False),
        sa.Column("variant_id", UUID, nullable=False),
        sa.Column("qty", sa.Numeric(19, 4), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["requisition_id"], ["purchase_requisitions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["variant_id"], ["product_variants.id"]),
    )
    op.create_table(
        "purchase_orders",
        _id(),
        _org(),
        sa.Column("branch_id", UUID),
        sa.Column("supplier_id", UUID, nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default=sa.text("'draft'")),
        sa.Column("document_number", sa.String(64), nullable=False),
        sa.Column("ordered_at", sa.DateTime(timezone=True)),
        sa.Column("expected_at", sa.Date()),
        sa.CheckConstraint(
            "status IN ('draft', 'pending_approval', 'approved', 'sent', 'partial', 'received', 'cancelled')",
            name="ck_po_status",
        ),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["branch_id"], ["branches.id"]),
        sa.ForeignKeyConstraint(["supplier_id"], ["suppliers.id"]),
        sa.UniqueConstraint("organization_id", "document_number", name="uq_po_org_number"),
    )
    op.create_table(
        "purchase_order_items",
        _id(),
        _org(),
        sa.Column("purchase_order_id", UUID, nullable=False),
        sa.Column("variant_id", UUID, nullable=False),
        sa.Column("qty_ordered", sa.Numeric(19, 4), nullable=False),
        sa.Column("qty_received", sa.Numeric(19, 4), nullable=False, server_default=sa.text("0")),
        sa.Column("unit_cost", sa.Numeric(19, 4), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["purchase_order_id"], ["purchase_orders.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["variant_id"], ["product_variants.id"]),
    )
    op.create_table(
        "goods_received_notes",
        _id(),
        _org(),
        sa.Column("purchase_order_id", UUID, nullable=False),
        sa.Column("warehouse_id", UUID, nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("document_number", sa.String(64), nullable=False),
        sa.Column("received_at", sa.DateTime(timezone=True)),
        sa.CheckConstraint("status IN ('draft', 'posted')", name="ck_grn_status"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["purchase_order_id"], ["purchase_orders.id"]),
        sa.ForeignKeyConstraint(["warehouse_id"], ["warehouses.id"]),
        sa.UniqueConstraint("organization_id", "document_number", name="uq_grn_org_number"),
    )
    op.create_table(
        "goods_received_items",
        _id(),
        _org(),
        sa.Column("grn_id", UUID, nullable=False),
        sa.Column("purchase_order_item_id", UUID, nullable=False),
        sa.Column("qty_accepted", sa.Numeric(19, 4), nullable=False),
        sa.Column("qty_rejected", sa.Numeric(19, 4), nullable=False, server_default=sa.text("0")),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["grn_id"], ["goods_received_notes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["purchase_order_item_id"], ["purchase_order_items.id"]),
    )
    op.create_table(
        "supplier_invoices",
        _id(),
        _org(),
        sa.Column("supplier_id", UUID, nullable=False),
        sa.Column("purchase_order_id", UUID),
        sa.Column("document_number", sa.String(64), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("subtotal", sa.Numeric(19, 4), nullable=False),
        sa.Column("tax_total", sa.Numeric(19, 4), nullable=False, server_default=sa.text("0")),
        sa.Column("total", sa.Numeric(19, 4), nullable=False),
        sa.Column("due_at", sa.Date()),
        sa.CheckConstraint(
            "status IN ('draft', 'posted', 'paid', 'partial')",
            name="ck_supplier_invoices_status",
        ),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["supplier_id"], ["suppliers.id"]),
        sa.ForeignKeyConstraint(["purchase_order_id"], ["purchase_orders.id"]),
        sa.UniqueConstraint("organization_id", "document_number", name="uq_supplier_invoices_org_number"),
    )
    op.create_table(
        "supplier_payments",
        _id(),
        _org(),
        sa.Column("supplier_id", UUID, nullable=False),
        sa.Column("invoice_id", UUID),
        sa.Column("amount", sa.Numeric(19, 4), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("method", sa.String(32), nullable=False),
        sa.Column("paid_at", sa.DateTime(timezone=True)),
        sa.CheckConstraint(
            "status IN ('pending', 'completed', 'failed')", name="ck_supplier_payments_status"
        ),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["supplier_id"], ["suppliers.id"]),
        sa.ForeignKeyConstraint(["invoice_id"], ["supplier_invoices.id"]),
    )
    op.create_table(
        "journal_entries",
        _id(),
        _org(),
        sa.Column("period_id", UUID, nullable=False),
        sa.Column("entry_number", sa.String(64), nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default=sa.text("'draft'")),
        sa.Column("source_type", sa.String(32), nullable=False),
        sa.Column("source_id", UUID, nullable=False),
        sa.Column("reverses_journal_id", UUID),
        sa.Column("reversed_by_id", UUID),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("posted_at", sa.DateTime(timezone=True)),
        sa.Column("idempotency_key", sa.String(128)),
        sa.CheckConstraint("status IN ('draft', 'posted', 'reversed')", name="ck_journals_status"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["period_id"], ["accounting_periods.id"]),
        sa.ForeignKeyConstraint(["reverses_journal_id"], ["journal_entries.id"]),
        sa.UniqueConstraint("organization_id", "entry_number", name="uq_journals_org_number"),
    )
    op.execute(
        """
        CREATE UNIQUE INDEX uq_journals_posted_source
        ON journal_entries (organization_id, source_type, source_id)
        WHERE status = 'posted'
        """
    )
    op.create_table(
        "journal_lines",
        _id(),
        _org(),
        sa.Column("journal_id", UUID, nullable=False),
        sa.Column("account_id", UUID, nullable=False),
        sa.Column("branch_id", UUID),
        sa.Column("debit", sa.Numeric(19, 4), nullable=False, server_default=sa.text("0")),
        sa.Column("credit", sa.Numeric(19, 4), nullable=False, server_default=sa.text("0")),
        sa.Column("party_type", sa.String(32)),
        sa.Column("party_id", UUID),
        sa.Column("tax_rate_id", UUID),
        sa.Column("memo", sa.String(255)),
        sa.CheckConstraint(
            "(debit = 0 AND credit > 0) OR (credit = 0 AND debit > 0)",
            name="ck_journal_lines_side",
        ),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["journal_id"], ["journal_entries.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["account_id"], ["chart_of_accounts.id"]),
        sa.ForeignKeyConstraint(["branch_id"], ["branches.id"]),
        sa.ForeignKeyConstraint(["tax_rate_id"], ["tax_rates.id"]),
    )
    op.create_table(
        "subledger_balances",
        _id(),
        _org(),
        sa.Column("party_type", sa.String(32), nullable=False),
        sa.Column("party_id", UUID, nullable=False),
        sa.Column("account_id", UUID, nullable=False),
        sa.Column("balance", sa.Numeric(19, 4), nullable=False, server_default=sa.text("0")),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["account_id"], ["chart_of_accounts.id"]),
        sa.UniqueConstraint(
            "organization_id", "party_type", "party_id", "account_id", name="uq_subledger_party_account"
        ),
    )
    op.create_table(
        "bank_accounts",
        _id(),
        _org(),
        sa.Column("account_id", UUID, nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("bank_name", sa.String(200)),
        sa.Column("account_number_masked", sa.String(64)),
        sa.Column("currency_code", sa.String(3), nullable=False, server_default=sa.text("'ZMW'")),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["account_id"], ["chart_of_accounts.id"]),
    )
    op.create_table(
        "bank_transactions",
        _id(),
        _org(),
        sa.Column("bank_account_id", UUID, nullable=False),
        sa.Column("posted_on", sa.Date(), nullable=False),
        sa.Column("amount", sa.Numeric(19, 4), nullable=False),
        sa.Column("description", sa.String(255)),
        sa.Column("external_ref", sa.String(128)),
        sa.Column("status", sa.String(16), nullable=False, server_default=sa.text("'unmatched'")),
        sa.CheckConstraint(
            "status IN ('unmatched', 'matched', 'ignored')", name="ck_bank_tx_status"
        ),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["bank_account_id"], ["bank_accounts.id"]),
    )
    op.create_table(
        "bank_reconciliations",
        _id(),
        _org(),
        sa.Column("bank_account_id", UUID, nullable=False),
        sa.Column("statement_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default=sa.text("'open'")),
        sa.CheckConstraint("status IN ('open', 'completed')", name="ck_bank_recon_status"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["bank_account_id"], ["bank_accounts.id"]),
    )
    op.create_table(
        "reconciliation_items",
        _id(),
        _org(),
        sa.Column("reconciliation_id", UUID, nullable=False),
        sa.Column("bank_transaction_id", UUID, nullable=False),
        sa.Column("journal_line_id", UUID),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["reconciliation_id"], ["bank_reconciliations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["bank_transaction_id"], ["bank_transactions.id"]),
        sa.ForeignKeyConstraint(["journal_line_id"], ["journal_lines.id"]),
    )
    op.create_table(
        "expenses",
        _id(),
        _org(),
        sa.Column("branch_id", UUID),
        sa.Column("vendor_name", sa.String(200), nullable=False),
        sa.Column("supplier_id", UUID),
        sa.Column("amount", sa.Numeric(19, 4), nullable=False),
        sa.Column("tax_amount", sa.Numeric(19, 4), nullable=False, server_default=sa.text("0")),
        sa.Column("status", sa.String(16), nullable=False, server_default=sa.text("'draft'")),
        sa.Column("incurred_on", sa.Date(), nullable=False),
        sa.Column("payment_method", sa.String(32), nullable=False, server_default=sa.text("'cash'")),
        sa.Column("document_number", sa.String(64), nullable=False),
        sa.CheckConstraint(
            "status IN ('draft', 'approved', 'posted', 'rejected')", name="ck_expenses_status"
        ),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["branch_id"], ["branches.id"]),
        sa.ForeignKeyConstraint(["supplier_id"], ["suppliers.id"]),
        sa.UniqueConstraint("organization_id", "document_number", name="uq_expenses_org_number"),
    )
    op.create_table(
        "expense_lines",
        _id(),
        _org(),
        sa.Column("expense_id", UUID, nullable=False),
        sa.Column("account_id", UUID, nullable=False),
        sa.Column("amount", sa.Numeric(19, 4), nullable=False),
        sa.Column("memo", sa.String(255)),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["expense_id"], ["expenses.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["account_id"], ["chart_of_accounts.id"]),
    )
    op.create_table(
        "departments",
        _id(),
        _org(),
        sa.Column("name", sa.String(200), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
    )
    op.create_table(
        "employees",
        _id(),
        _org(),
        sa.Column("branch_id", UUID),
        sa.Column("user_id", UUID),
        sa.Column("employee_number", sa.String(64), nullable=False),
        sa.Column("full_name", sa.String(200), nullable=False),
        sa.Column("hire_on", sa.Date(), nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default=sa.text("'active'")),
        sa.Column("department_id", UUID),
        sa.Column("job_title", sa.String(200)),
        sa.Column("base_salary", sa.Numeric(19, 4), nullable=False, server_default=sa.text("0")),
        sa.CheckConstraint("status IN ('active', 'terminated')", name="ck_employees_status"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["branch_id"], ["branches.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["department_id"], ["departments.id"]),
        sa.UniqueConstraint("organization_id", "employee_number", name="uq_employees_org_number"),
    )
    op.create_table(
        "attendance_records",
        _id(),
        _org(),
        sa.Column("employee_id", UUID, nullable=False),
        sa.Column("work_on", sa.Date(), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["employee_id"], ["employees.id"]),
        sa.UniqueConstraint("employee_id", "work_on", name="uq_attendance_employee_day"),
    )
    op.create_table(
        "employee_shifts",
        _id(),
        _org(),
        sa.Column("employee_id", UUID, nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("branch_id", UUID),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["employee_id"], ["employees.id"]),
        sa.ForeignKeyConstraint(["branch_id"], ["branches.id"]),
    )
    op.create_table(
        "leave_requests",
        _id(),
        _org(),
        sa.Column("employee_id", UUID, nullable=False),
        sa.Column("type", sa.String(32), nullable=False),
        sa.Column("starts_on", sa.Date(), nullable=False),
        sa.Column("ends_on", sa.Date(), nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default=sa.text("'pending'")),
        sa.CheckConstraint("status IN ('pending', 'approved', 'rejected')", name="ck_leave_status"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["employee_id"], ["employees.id"]),
    )
    op.create_table(
        "payroll_components",
        _id(),
        _org(),
        sa.Column("code", sa.String(32), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("kind", sa.String(32), nullable=False),
        sa.Column("calculation", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("effective_from", sa.Date()),
        sa.Column("effective_to", sa.Date()),
        sa.CheckConstraint(
            "kind IN ('earning', 'deduction', 'employer_contribution')",
            name="ck_payroll_components_kind",
        ),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("organization_id", "code", name="uq_payroll_components_org_code"),
    )
    op.create_table(
        "payroll_periods",
        _id(),
        _org(),
        sa.Column("starts_on", sa.Date(), nullable=False),
        sa.Column("ends_on", sa.Date(), nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default=sa.text("'open'")),
        sa.CheckConstraint("status IN ('open', 'closed')", name="ck_payroll_periods_status"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
    )
    op.create_table(
        "payroll_runs",
        _id(),
        _org(),
        sa.Column("period_id", UUID, nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True)),
        sa.Column("idempotency_key", sa.String(128)),
        sa.CheckConstraint("status IN ('draft', 'processed')", name="ck_payroll_runs_status"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["period_id"], ["payroll_periods.id"]),
    )
    op.create_table(
        "payroll_items",
        _id(),
        _org(),
        sa.Column("run_id", UUID, nullable=False),
        sa.Column("employee_id", UUID, nullable=False),
        sa.Column("component_id", UUID, nullable=False),
        sa.Column("amount", sa.Numeric(19, 4), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["run_id"], ["payroll_runs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["employee_id"], ["employees.id"]),
        sa.ForeignKeyConstraint(["component_id"], ["payroll_components.id"]),
    )

    op.execute(
        """
        CREATE FUNCTION app_reject_journal_mutation() RETURNS trigger
        LANGUAGE plpgsql AS $$
        BEGIN
          IF TG_TABLE_NAME = 'journal_lines' THEN
            RAISE EXCEPTION 'journal_lines are immutable' USING ERRCODE = 'P0001';
          END IF;
          IF TG_OP = 'DELETE' THEN
            RAISE EXCEPTION 'journal_entries are immutable' USING ERRCODE = 'P0001';
          END IF;
          IF OLD.status IN ('posted', 'reversed') THEN
            IF NEW.status = 'reversed'
               AND OLD.status = 'posted'
               AND NEW.reversed_by_id IS NOT NULL
               AND NEW.entry_number IS NOT DISTINCT FROM OLD.entry_number
               AND NEW.source_type IS NOT DISTINCT FROM OLD.source_type
               AND NEW.source_id IS NOT DISTINCT FROM OLD.source_id
               AND NEW.period_id IS NOT DISTINCT FROM OLD.period_id THEN
              RETURN NEW;
            END IF;
            RAISE EXCEPTION 'posted journals are immutable' USING ERRCODE = 'P0001';
          END IF;
          RETURN NEW;
        END;
        $$;
        """
    )
    op.execute(
        """
        CREATE TRIGGER journal_entries_immutable
        BEFORE UPDATE OR DELETE ON journal_entries
        FOR EACH ROW EXECUTE FUNCTION app_reject_journal_mutation();
        """
    )
    op.execute(
        """
        CREATE TRIGGER journal_lines_immutable
        BEFORE UPDATE OR DELETE ON journal_lines
        FOR EACH ROW EXECUTE FUNCTION app_reject_journal_mutation();
        """
    )
    op.execute(
        """
        CREATE FUNCTION app_reject_audit_mutation() RETURNS trigger
        LANGUAGE plpgsql AS $$
        BEGIN
          RAISE EXCEPTION 'audit_logs are append-only' USING ERRCODE = 'P0001';
        END;
        $$;
        """
    )
    op.execute(
        """
        CREATE TRIGGER audit_logs_immutable
        BEFORE UPDATE OR DELETE ON audit_logs
        FOR EACH ROW EXECUTE FUNCTION app_reject_audit_mutation();
        """
    )

    for table in TENANT_TABLES:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
        op.execute(_POLICY.format(table=table))

    op.execute(
        sa.text(
            """
            INSERT INTO permissions (id, code, description, module)
            VALUES (CAST(:id AS uuid), 'purchases.view', 'View purchase documents', 'purchasing')
            ON CONFLICT (code) DO NOTHING
            """
        ).bindparams(id=str(new_uuid()))
    )
    op.execute("GRANT SELECT, INSERT ON audit_logs TO bizpilot_app")
    op.execute("REVOKE UPDATE, DELETE ON audit_logs FROM bizpilot_app")
    op.execute("GRANT SELECT, INSERT ON journal_entries, journal_lines TO bizpilot_app")
    op.execute("REVOKE DELETE ON journal_entries, journal_lines FROM bizpilot_app")
    op.execute(
        "UPDATE app_metadata SET value = '9', updated_at = now() WHERE key = 'schema_phase'"
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS audit_logs_immutable ON audit_logs")
    op.execute("DROP TRIGGER IF EXISTS journal_lines_immutable ON journal_lines")
    op.execute("DROP TRIGGER IF EXISTS journal_entries_immutable ON journal_entries")
    op.execute("DROP FUNCTION IF EXISTS app_reject_audit_mutation()")
    op.execute("DROP FUNCTION IF EXISTS app_reject_journal_mutation()")
    for table in reversed(TENANT_TABLES):
        op.execute(f"DROP POLICY IF EXISTS {table}_tenant_isolation ON {table}")
        op.drop_table(table)
    op.execute(
        "UPDATE app_metadata SET value = '5', updated_at = now() WHERE key = 'schema_phase'"
    )
