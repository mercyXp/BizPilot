from datetime import date
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas import (
    PriceIn,
    PriceOut,
    ProductIn,
    ProductOut,
    UomIn,
    UomOut,
    VariantIn,
    VariantOut,
)
from app.core.context import TenantContext
from app.core.db import get_db
from app.modules.authorization.deps import require_permission
from app.modules.catalogue.service import (
    create_price,
    create_product,
    create_uom,
    create_variant,
    list_products,
    list_uom,
    list_variants,
    resolve_price,
)

router = APIRouter(tags=["catalogue"])


@router.post("/units-of-measure", response_model=UomOut, status_code=201)
async def add_uom(
    body: UomIn,
    ctx: TenantContext = Depends(require_permission("catalogue.manage")),
    session: AsyncSession = Depends(get_db),
) -> UomOut:
    row = await create_uom(session, ctx, code=body.code, name=body.name, is_integer=body.is_integer)
    return UomOut(id=row.id, code=row.code, name=row.name, is_integer=row.is_integer)


@router.get("/units-of-measure", response_model=list[UomOut])
async def get_uom(
    ctx: TenantContext = Depends(require_permission("catalogue.view")),
    session: AsyncSession = Depends(get_db),
) -> list[UomOut]:
    return [
        UomOut(id=row.id, code=row.code, name=row.name, is_integer=row.is_integer)
        for row in await list_uom(session, ctx)
    ]


@router.post("/products", response_model=ProductOut, status_code=201)
async def add_product(
    body: ProductIn,
    ctx: TenantContext = Depends(require_permission("catalogue.manage")),
    session: AsyncSession = Depends(get_db),
) -> ProductOut:
    row = await create_product(
        session,
        ctx,
        name=body.name,
        type=body.type,
        uom_id=body.uom_id,
        sku=body.sku,
        category_id=body.category_id,
        tax_category_id=body.tax_category_id,
        track_inventory=body.track_inventory,
        track_batches=body.track_batches,
        track_expiry=body.track_expiry,
    )
    return ProductOut(
        id=row.id,
        name=row.name,
        type=row.type,
        sku=row.sku,
        track_inventory=row.track_inventory,
        track_batches=row.track_batches,
        is_active=row.is_active,
    )


@router.get("/products", response_model=list[ProductOut])
async def get_products(
    ctx: TenantContext = Depends(require_permission("catalogue.view")),
    session: AsyncSession = Depends(get_db),
) -> list[ProductOut]:
    return [
        ProductOut(
            id=row.id,
            name=row.name,
            type=row.type,
            sku=row.sku,
            track_inventory=row.track_inventory,
            track_batches=row.track_batches,
            is_active=row.is_active,
        )
        for row in await list_products(session, ctx)
    ]


@router.post("/products/{product_id}/variants", response_model=VariantOut, status_code=201)
async def add_variant(
    product_id: UUID,
    body: VariantIn,
    ctx: TenantContext = Depends(require_permission("catalogue.manage")),
    session: AsyncSession = Depends(get_db),
) -> VariantOut:
    row = await create_variant(
        session,
        ctx,
        product_id=product_id,
        name=body.name,
        sku=body.sku,
        attributes=body.attributes,
    )
    return VariantOut(
        id=row.id,
        product_id=row.product_id,
        name=row.name,
        sku=row.sku,
        attributes=row.attributes,
    )


@router.get("/products/{product_id}/variants", response_model=list[VariantOut])
async def get_variants(
    product_id: UUID,
    ctx: TenantContext = Depends(require_permission("catalogue.view")),
    session: AsyncSession = Depends(get_db),
) -> list[VariantOut]:
    return [
        VariantOut(
            id=row.id,
            product_id=row.product_id,
            name=row.name,
            sku=row.sku,
            attributes=row.attributes,
        )
        for row in await list_variants(session, ctx, product_id)
    ]


@router.post("/product-prices", response_model=PriceOut, status_code=201)
async def add_price(
    body: PriceIn,
    ctx: TenantContext = Depends(require_permission("catalogue.manage")),
    session: AsyncSession = Depends(get_db),
) -> PriceOut:
    row = await create_price(
        session,
        ctx,
        variant_id=body.variant_id,
        amount=Decimal(str(body.amount)),
        currency_code=body.currency_code,
        branch_id=body.branch_id,
        price_list_code=body.price_list_code,
        effective_from=None,
        effective_to=None,
    )
    return PriceOut(
        id=row.id,
        variant_id=row.variant_id,
        branch_id=row.branch_id,
        amount=float(row.amount),
        currency_code=row.currency_code,
        price_list_code=row.price_list_code,
    )


@router.get("/product-prices/resolve", response_model=PriceOut)
async def get_price(
    variant_id: UUID,
    branch_id: UUID | None = None,
    price_list_code: str = Query(default="retail"),
    ctx: TenantContext = Depends(require_permission("catalogue.view")),
    session: AsyncSession = Depends(get_db),
) -> PriceOut:
    row = await resolve_price(
        session,
        ctx,
        variant_id=variant_id,
        branch_id=branch_id,
        price_list_code=price_list_code,
        on=date.today(),
    )
    return PriceOut(
        id=row.id,
        variant_id=row.variant_id,
        branch_id=row.branch_id,
        amount=float(row.amount),
        currency_code=row.currency_code,
        price_list_code=row.price_list_code,
    )
