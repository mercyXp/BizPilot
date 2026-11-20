from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Uuid

from app.core.db import Base
from app.core.ids import new_uuid


class PosSession(Base):
    __tablename__ = "pos_sessions"
    __table_args__ = (
        CheckConstraint("status IN ('open', 'closed')", name="ck_pos_sessions_status"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=new_uuid)
    organization_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    branch_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("branches.id"), nullable=False
    )
    warehouse_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("warehouses.id"), nullable=False
    )
    opened_by_user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    closed_by_user_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id"))
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, default="open", server_default=text("'open'")
    )
    opening_float: Mapped[Decimal] = mapped_column(Numeric(19, 4), nullable=False)
    closing_counted_cash: Mapped[Decimal | None] = mapped_column(Numeric(19, 4))
    opened_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class PosCashMovement(Base):
    __tablename__ = "pos_cash_movements"
    __table_args__ = (
        CheckConstraint(
            "type IN ('in', 'out', 'sale', 'refund', 'variance')",
            name="ck_pos_cash_type",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=new_uuid)
    organization_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    session_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("pos_sessions.id"), nullable=False
    )
    type: Mapped[str] = mapped_column(String(16), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(19, 4), nullable=False)
    reason: Mapped[str | None] = mapped_column(String(255))


class Sale(Base):
    __tablename__ = "sales"
    __table_args__ = (
        UniqueConstraint("organization_id", "document_number", name="uq_sales_org_number"),
        CheckConstraint(
            "status IN ('draft', 'awaiting_payment', 'completed', 'voided', 'refunded', 'partially_refunded')",
            name="ck_sales_status",
        ),
        CheckConstraint("sale_type IN ('pos', 'invoice')", name="ck_sales_type"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=new_uuid)
    organization_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    branch_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("branches.id"), nullable=False
    )
    session_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("pos_sessions.id"))
    customer_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("customers.id"))
    document_number: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    sale_type: Mapped[str] = mapped_column(
        String(16), nullable=False, default="pos", server_default=text("'pos'")
    )
    subtotal: Mapped[Decimal] = mapped_column(Numeric(19, 4), nullable=False)
    discount_total: Mapped[Decimal] = mapped_column(Numeric(19, 4), nullable=False, server_default=text("0"))
    tax_total: Mapped[Decimal] = mapped_column(Numeric(19, 4), nullable=False, server_default=text("0"))
    total: Mapped[Decimal] = mapped_column(Numeric(19, 4), nullable=False)
    currency_code: Mapped[str] = mapped_column(
        String(3), nullable=False, default="ZMW", server_default=text("'ZMW'")
    )
    idempotency_key: Mapped[str | None] = mapped_column(String(128))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class SaleItem(Base):
    __tablename__ = "sale_items"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=new_uuid)
    organization_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    sale_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("sales.id", ondelete="CASCADE"), nullable=False
    )
    variant_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("product_variants.id"), nullable=False
    )
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    qty: Mapped[Decimal] = mapped_column(Numeric(19, 4), nullable=False)
    uom_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("units_of_measure.id"), nullable=False
    )
    unit_price: Mapped[Decimal] = mapped_column(Numeric(19, 4), nullable=False)
    discount_amount: Mapped[Decimal] = mapped_column(Numeric(19, 4), nullable=False, server_default=text("0"))
    tax_rate_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("tax_rates.id"))
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(19, 4), nullable=False, server_default=text("0"))
    line_total: Mapped[Decimal] = mapped_column(Numeric(19, 4), nullable=False)


class Payment(Base):
    __tablename__ = "payments"
    __table_args__ = (
        CheckConstraint(
            "method IN ('cash', 'mobile_money', 'card', 'bank_transfer', 'store_credit')",
            name="ck_payments_method",
        ),
        CheckConstraint(
            "status IN ('pending', 'completed', 'failed', 'cancelled')",
            name="ck_payments_status",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=new_uuid)
    organization_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    sale_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("sales.id"))
    customer_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("customers.id"))
    method: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(19, 4), nullable=False)
    provider: Mapped[str | None] = mapped_column(String(64))
    provider_ref: Mapped[str | None] = mapped_column(String(128))
    received_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class PaymentAllocation(Base):
    __tablename__ = "payment_allocations"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=new_uuid)
    organization_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    payment_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("payments.id", ondelete="CASCADE"), nullable=False
    )
    source_type: Mapped[str] = mapped_column(String(32), nullable=False)
    source_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(19, 4), nullable=False)


class Refund(Base):
    __tablename__ = "refunds"
    __table_args__ = (
        CheckConstraint("status IN ('completed', 'pending')", name="ck_refunds_status"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=new_uuid)
    organization_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    sale_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("sales.id"), nullable=False
    )
    reason: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    total: Mapped[Decimal] = mapped_column(Numeric(19, 4), nullable=False)
    restock: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=text("true")
    )
    idempotency_key: Mapped[str | None] = mapped_column(String(128))


class RefundItem(Base):
    __tablename__ = "refund_items"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=new_uuid)
    organization_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    refund_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("refunds.id", ondelete="CASCADE"), nullable=False
    )
    sale_item_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("sale_items.id"), nullable=False
    )
    qty: Mapped[Decimal] = mapped_column(Numeric(19, 4), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(19, 4), nullable=False)


class Receipt(Base):
    __tablename__ = "receipts"
    __table_args__ = (
        UniqueConstraint("organization_id", "document_number", name="uq_receipts_org_number"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=new_uuid)
    organization_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    sale_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("sales.id"), nullable=False
    )
    document_number: Mapped[str] = mapped_column(String(64), nullable=False)
    payload_json: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    pdf_object_key: Mapped[str | None] = mapped_column(String(512))
