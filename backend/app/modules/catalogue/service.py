from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import Select, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import TenantContext
from app.core.errors import AppError
from app.modules.catalogue.models import (
    Product,
    ProductCategory,
    ProductPrice,
    ProductTaxCategory,
    ProductVariant,
    UnitOfMeasure,
)
from app.modules.tenancy.service import get_settings


async def create_uom(
    session: AsyncSession,
    ctx: TenantContext,
    *,
    code: str,
    name: str,
    is_integer: bool,
) -> UnitOfMeasure:
    row = UnitOfMeasure(
        organization_id=ctx.organization_id,
        code=code.strip().upper(),
        name=name.strip(),
        is_integer=is_integer,
    )
    session.add(row)
    try:
        await session.flush()
    except IntegrityError as exc:
        raise AppError(409, "Unit of measure already exists", code="conflict") from exc
    return row


async def list_uom(session: AsyncSession, ctx: TenantContext) -> list[UnitOfMeasure]:
    rows = await session.scalars(
        select(UnitOfMeasure)
        .where(UnitOfMeasure.organization_id == ctx.organization_id)
        .order_by(UnitOfMeasure.code)
    )
    return list(rows)


async def create_category(
    session: AsyncSession,
    ctx: TenantContext,
    *,
    name: str,
    parent_id: UUID | None,
) -> ProductCategory:
    path = name.strip()
    if parent_id:
        parent = await session.get(ProductCategory, parent_id)
        if parent is None:
            raise AppError(404, "Category not found", code="not_found")
        path = f"{parent.path}/{name.strip()}"
    row = ProductCategory(
        organization_id=ctx.organization_id,
        parent_id=parent_id,
        name=name.strip(),
        path=path,
        is_active=True,
    )
    session.add(row)
    await session.flush()
    return row


async def create_tax_category(
    session: AsyncSession, ctx: TenantContext, *, name: str
) -> ProductTaxCategory:
    row = ProductTaxCategory(organization_id=ctx.organization_id, name=name.strip())
    session.add(row)
    await session.flush()
    return row


async def create_product(
    session: AsyncSession,
    ctx: TenantContext,
    *,
    name: str,
    type: str,
    uom_id: UUID,
    sku: str | None,
    category_id: UUID | None,
    tax_category_id: UUID | None,
    track_inventory: bool | None,
    track_batches: bool | None,
    track_expiry: bool | None,
) -> Product:
    await _uom(session, ctx, uom_id)
    org_settings = (await get_settings(session, ctx)).settings
    catalogue = org_settings.get("catalogue") if isinstance(org_settings, dict) else {}
    catalogue = catalogue if isinstance(catalogue, dict) else {}
    product = Product(
        organization_id=ctx.organization_id,
        name=name.strip(),
        type=type,
        uom_id=uom_id,
        sku=sku.strip() if sku else None,
        category_id=category_id,
        tax_category_id=tax_category_id,
        track_inventory=True if track_inventory is None else track_inventory,
        track_batches=catalogue.get("track_batches", False)
        if track_batches is None
        else track_batches,
        track_expiry=catalogue.get("track_expiry", False) if track_expiry is None else track_expiry,
        is_active=True,
    )
    if product.type == "service":
        product.track_inventory = False
    session.add(product)
    try:
        await session.flush()
    except IntegrityError as exc:
        raise AppError(409, "Product SKU already exists", code="conflict") from exc
    variant = ProductVariant(
        organization_id=ctx.organization_id,
        product_id=product.id,
        sku=product.sku,
        name=product.name,
        attributes={},
        is_active=True,
    )
    session.add(variant)
    await session.flush()
    return product


async def list_products(session: AsyncSession, ctx: TenantContext) -> list[Product]:
    rows = await session.scalars(
        select(Product)
        .where(Product.organization_id == ctx.organization_id, Product.deleted_at.is_(None))
        .order_by(Product.name)
    )
    return list(rows)


async def get_product(session: AsyncSession, ctx: TenantContext, product_id: UUID) -> Product:
    product = await session.get(Product, product_id)
    if product is None or product.deleted_at is not None:
        raise AppError(404, "Product not found", code="not_found")
    return product


async def create_variant(
    session: AsyncSession,
    ctx: TenantContext,
    *,
    product_id: UUID,
    name: str,
    sku: str | None,
    attributes: dict,
) -> ProductVariant:
    await get_product(session, ctx, product_id)
    row = ProductVariant(
        organization_id=ctx.organization_id,
        product_id=product_id,
        name=name.strip(),
        sku=sku.strip() if sku else None,
        attributes=attributes,
        is_active=True,
    )
    session.add(row)
    await session.flush()
    return row


async def list_variants(
    session: AsyncSession, ctx: TenantContext, product_id: UUID
) -> list[ProductVariant]:
    await get_product(session, ctx, product_id)
    rows = await session.scalars(
        select(ProductVariant)
        .where(
            ProductVariant.organization_id == ctx.organization_id,
            ProductVariant.product_id == product_id,
        )
        .order_by(ProductVariant.name)
    )
    return list(rows)


async def get_variant(session: AsyncSession, ctx: TenantContext, variant_id: UUID) -> ProductVariant:
    variant = await session.get(ProductVariant, variant_id)
    if variant is None:
        raise AppError(404, "Variant not found", code="not_found")
    return variant


async def create_price(
    session: AsyncSession,
    ctx: TenantContext,
    *,
    variant_id: UUID,
    amount: Decimal,
    currency_code: str,
    branch_id: UUID | None,
    price_list_code: str,
    effective_from: date | None,
    effective_to: date | None,
) -> ProductPrice:
    await get_variant(session, ctx, variant_id)
    row = ProductPrice(
        organization_id=ctx.organization_id,
        variant_id=variant_id,
        branch_id=branch_id,
        price_list_code=price_list_code,
        amount=amount,
        currency_code=currency_code,
        effective_from=effective_from,
        effective_to=effective_to,
    )
    session.add(row)
    await session.flush()
    return row


async def resolve_price(
    session: AsyncSession,
    ctx: TenantContext,
    *,
    variant_id: UUID,
    branch_id: UUID | None,
    price_list_code: str,
    on: date,
) -> ProductPrice:
    await get_variant(session, ctx, variant_id)
    statement: Select = select(ProductPrice).where(
        ProductPrice.organization_id == ctx.organization_id,
        ProductPrice.variant_id == variant_id,
        ProductPrice.price_list_code == price_list_code,
        or_(ProductPrice.effective_from.is_(None), ProductPrice.effective_from <= on),
        or_(ProductPrice.effective_to.is_(None), ProductPrice.effective_to >= on),
    )
    if branch_id is not None:
        statement = statement.where(
            or_(ProductPrice.branch_id == branch_id, ProductPrice.branch_id.is_(None))
        )
    else:
        statement = statement.where(ProductPrice.branch_id.is_(None))
    rows = list(await session.scalars(statement))
    if not rows:
        raise AppError(404, "Price not found", code="not_found")
    branch_match = [row for row in rows if branch_id is not None and row.branch_id == branch_id]
    chosen = branch_match[0] if branch_match else rows[0]
    return chosen


async def _uom(session: AsyncSession, ctx: TenantContext, uom_id: UUID) -> UnitOfMeasure:
    row = await session.get(UnitOfMeasure, uom_id)
    if row is None:
        raise AppError(422, "Unit of measure not found", code="validation_error")
    _ = ctx
    return row
