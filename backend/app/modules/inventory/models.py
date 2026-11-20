from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Uuid

from app.core.db import Base
from app.core.ids import new_uuid


class ProductBatch(Base):
    __tablename__ = "product_batches"
    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "variant_id",
            "batch_number",
            name="uq_batches_org_variant_number",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=new_uuid)
    organization_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    variant_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("product_variants.id"), nullable=False
    )
    batch_number: Mapped[str] = mapped_column(String(64), nullable=False)
    expires_on: Mapped[date | None] = mapped_column(Date)
    manufactured_on: Mapped[date | None] = mapped_column(Date)


class StockBalance(Base):
    __tablename__ = "stock_balances"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=new_uuid)
    organization_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    warehouse_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("warehouses.id"), nullable=False
    )
    variant_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("product_variants.id"), nullable=False
    )
    batch_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("product_batches.id"))
    qty_on_hand: Mapped[Decimal] = mapped_column(
        Numeric(19, 4), nullable=False, server_default=text("0")
    )
    qty_reserved: Mapped[Decimal] = mapped_column(
        Numeric(19, 4), nullable=False, server_default=text("0")
    )
    avg_unit_cost: Mapped[Decimal] = mapped_column(
        Numeric(19, 4), nullable=False, server_default=text("0")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


class StockMovement(Base):
    __tablename__ = "stock_movements"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=new_uuid)
    organization_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    warehouse_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("warehouses.id"), nullable=False
    )
    branch_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("branches.id"), nullable=False
    )
    variant_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("product_variants.id"), nullable=False
    )
    batch_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("product_batches.id"))
    qty_delta: Mapped[Decimal] = mapped_column(Numeric(19, 4), nullable=False)
    unit_cost: Mapped[Decimal] = mapped_column(Numeric(19, 4), nullable=False)
    movement_type: Mapped[str] = mapped_column(String(32), nullable=False)
    source_type: Mapped[str] = mapped_column(String(32), nullable=False)
    source_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    created_by_user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False
    )


class DocumentSequence(Base):
    __tablename__ = "document_sequences"
    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "branch_id",
            "document_type",
            name="uq_document_sequences_org_branch_type",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=new_uuid)
    organization_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    branch_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("branches.id"))
    document_type: Mapped[str] = mapped_column(String(64), nullable=False)
    prefix: Mapped[str] = mapped_column(String(16), nullable=False)
    next_value: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("1"))


class StockTransfer(Base):
    __tablename__ = "stock_transfers"
    __table_args__ = (
        UniqueConstraint("organization_id", "document_number", name="uq_transfers_org_number"),
        CheckConstraint(
            "status IN ('draft', 'approved', 'dispatched', 'partially_received', 'completed', 'cancelled')",
            name="ck_transfers_status",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=new_uuid)
    organization_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    source_warehouse_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("warehouses.id"), nullable=False
    )
    dest_warehouse_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("warehouses.id"), nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="draft", server_default=text("'draft'")
    )
    document_number: Mapped[str] = mapped_column(String(64), nullable=False)
    shipped_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    received_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class StockTransferItem(Base):
    __tablename__ = "stock_transfer_items"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=new_uuid)
    organization_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    transfer_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("stock_transfers.id", ondelete="CASCADE"), nullable=False
    )
    variant_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("product_variants.id"), nullable=False
    )
    batch_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("product_batches.id"))
    qty_sent: Mapped[Decimal] = mapped_column(Numeric(19, 4), nullable=False)
    qty_received: Mapped[Decimal] = mapped_column(
        Numeric(19, 4), nullable=False, server_default=text("0")
    )


class StockCount(Base):
    __tablename__ = "stock_counts"
    __table_args__ = (
        CheckConstraint(
            "status IN ('in_progress', 'posted', 'cancelled')",
            name="ck_counts_status",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=new_uuid)
    organization_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    warehouse_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("warehouses.id"), nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="in_progress", server_default=text("'in_progress'")
    )
    counted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class StockCountItem(Base):
    __tablename__ = "stock_count_items"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=new_uuid)
    organization_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    count_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("stock_counts.id", ondelete="CASCADE"), nullable=False
    )
    variant_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("product_variants.id"), nullable=False
    )
    batch_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("product_batches.id"))
    system_qty: Mapped[Decimal] = mapped_column(Numeric(19, 4), nullable=False)
    counted_qty: Mapped[Decimal | None] = mapped_column(Numeric(19, 4))
