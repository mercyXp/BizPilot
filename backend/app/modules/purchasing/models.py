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
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Uuid

from app.core.db import Base
from app.core.ids import new_uuid


class Supplier(Base):
    __tablename__ = "suppliers"
    __table_args__ = (UniqueConstraint("organization_id", "code", name="uq_suppliers_org_code"),)

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=new_uuid)
    organization_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(32))
    email: Mapped[str | None] = mapped_column(String(320))
    tax_id: Mapped[str | None] = mapped_column(String(64))
    address_json: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    payment_terms_days: Mapped[int] = mapped_column(default=0, server_default=text("0"))
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=text("true")
    )


class PurchaseRequisition(Base):
    __tablename__ = "purchase_requisitions"
    __table_args__ = (
        UniqueConstraint("organization_id", "document_number", name="uq_pr_org_number"),
        CheckConstraint("status IN ('draft', 'submitted', 'approved', 'cancelled')", name="ck_pr_status"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=new_uuid)
    organization_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    branch_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("branches.id"))
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, default="draft", server_default=text("'draft'")
    )
    requested_by: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False)
    document_number: Mapped[str] = mapped_column(String(64), nullable=False)


class PurchaseRequisitionItem(Base):
    __tablename__ = "purchase_requisition_items"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=new_uuid)
    organization_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    requisition_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("purchase_requisitions.id", ondelete="CASCADE"), nullable=False
    )
    variant_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("product_variants.id"), nullable=False
    )
    qty: Mapped[Decimal] = mapped_column(Numeric(19, 4), nullable=False)


class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"
    __table_args__ = (
        UniqueConstraint("organization_id", "document_number", name="uq_po_org_number"),
        CheckConstraint(
            "status IN ('draft', 'pending_approval', 'approved', 'sent', 'partial', 'received', 'cancelled')",
            name="ck_po_status",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=new_uuid)
    organization_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    branch_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("branches.id"))
    supplier_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("suppliers.id"), nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="draft", server_default=text("'draft'")
    )
    document_number: Mapped[str] = mapped_column(String(64), nullable=False)
    ordered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    expected_at: Mapped[date | None] = mapped_column(Date)


class PurchaseOrderItem(Base):
    __tablename__ = "purchase_order_items"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=new_uuid)
    organization_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    purchase_order_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("purchase_orders.id", ondelete="CASCADE"), nullable=False
    )
    variant_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("product_variants.id"), nullable=False
    )
    qty_ordered: Mapped[Decimal] = mapped_column(Numeric(19, 4), nullable=False)
    qty_received: Mapped[Decimal] = mapped_column(Numeric(19, 4), nullable=False, server_default=text("0"))
    unit_cost: Mapped[Decimal] = mapped_column(Numeric(19, 4), nullable=False)


class GoodsReceivedNote(Base):
    __tablename__ = "goods_received_notes"
    __table_args__ = (
        UniqueConstraint("organization_id", "document_number", name="uq_grn_org_number"),
        CheckConstraint("status IN ('draft', 'posted')", name="ck_grn_status"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=new_uuid)
    organization_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    purchase_order_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("purchase_orders.id"), nullable=False
    )
    warehouse_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("warehouses.id"), nullable=False
    )
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    document_number: Mapped[str] = mapped_column(String(64), nullable=False)
    received_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class GoodsReceivedItem(Base):
    __tablename__ = "goods_received_items"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=new_uuid)
    organization_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    grn_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("goods_received_notes.id", ondelete="CASCADE"), nullable=False
    )
    purchase_order_item_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("purchase_order_items.id"), nullable=False
    )
    qty_accepted: Mapped[Decimal] = mapped_column(Numeric(19, 4), nullable=False)
    qty_rejected: Mapped[Decimal] = mapped_column(Numeric(19, 4), nullable=False, server_default=text("0"))


class SupplierInvoice(Base):
    __tablename__ = "supplier_invoices"
    __table_args__ = (
        UniqueConstraint("organization_id", "document_number", name="uq_supplier_invoices_org_number"),
        CheckConstraint(
            "status IN ('draft', 'posted', 'paid', 'partial')",
            name="ck_supplier_invoices_status",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=new_uuid)
    organization_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    supplier_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("suppliers.id"), nullable=False
    )
    purchase_order_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("purchase_orders.id")
    )
    document_number: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(19, 4), nullable=False)
    tax_total: Mapped[Decimal] = mapped_column(Numeric(19, 4), nullable=False, server_default=text("0"))
    total: Mapped[Decimal] = mapped_column(Numeric(19, 4), nullable=False)
    due_at: Mapped[date | None] = mapped_column(Date)


class SupplierPayment(Base):
    __tablename__ = "supplier_payments"
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'completed', 'failed')",
            name="ck_supplier_payments_status",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=new_uuid)
    organization_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    supplier_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("suppliers.id"), nullable=False
    )
    invoice_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("supplier_invoices.id")
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(19, 4), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    method: Mapped[str] = mapped_column(String(32), nullable=False)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
