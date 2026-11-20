from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import TenantContext
from app.core.errors import AppError
from app.core.money import ZERO, money
from app.modules.accounting.engine import compute_tax, get_tax_rate
from app.modules.accounting.posting import post_cash_variance, post_refund, post_sale
from app.modules.audit.service import get_idempotent, store_idempotent, write_audit, request_hash
from app.modules.catalogue.models import Product, ProductVariant
from app.modules.catalogue.service import get_variant, resolve_price
from app.modules.crm.service import apply_credit_delta, assert_credit_available
from app.modules.inventory.service import issue, next_document_number, receive
from app.modules.sales.models import (
    Payment,
    PaymentAllocation,
    PosCashMovement,
    PosSession,
    Receipt,
    Refund,
    RefundItem,
    Sale,
    SaleItem,
)
from app.modules.sales.payments import provider_for
from app.modules.tenancy.service import get_warehouse


async def open_session(
    session: AsyncSession,
    ctx: TenantContext,
    *,
    warehouse_id: UUID,
    opening_float: Decimal,
) -> PosSession:
    if ctx.branch_id is None:
        raise AppError(422, "X-Branch-Id is required", code="validation_error")
    warehouse = await get_warehouse(session, ctx, warehouse_id)
    if warehouse.branch_id != ctx.branch_id:
        raise AppError(403, "Warehouse is not in the selected branch", code="permission_denied")
    row = PosSession(
        organization_id=ctx.organization_id,
        branch_id=ctx.branch_id,
        warehouse_id=warehouse.id,
        opened_by_user_id=ctx.user_id,
        status="open",
        opening_float=money(opening_float),
    )
    session.add(row)
    await session.flush()
    await write_audit(session, ctx, action="pos.session.open", entity_type="pos_session", entity_id=row.id)
    return row


async def add_cash_movement(
    session: AsyncSession,
    ctx: TenantContext,
    session_id: UUID,
    *,
    type: str,
    amount: Decimal,
    reason: str | None,
) -> PosCashMovement:
    pos = await _locked_session(session, ctx, session_id)
    if type not in {"in", "out"}:
        raise AppError(422, "Only cash in/out can be recorded here", code="validation_error")
    row = PosCashMovement(
        organization_id=ctx.organization_id,
        session_id=pos.id,
        type=type,
        amount=money(amount),
        reason=reason,
    )
    session.add(row)
    await session.flush()
    return row


async def close_session(
    session: AsyncSession,
    ctx: TenantContext,
    session_id: UUID,
    *,
    counted_cash: Decimal,
) -> PosSession:
    pos = await _locked_session(session, ctx, session_id)
    expected = await _expected_cash(session, pos)
    counted = money(counted_cash)
    variance = counted - expected
    pos.status = "closed"
    pos.closed_by_user_id = ctx.user_id
    pos.closed_at = datetime.now(UTC)
    pos.closing_counted_cash = counted
    session.add(
        PosCashMovement(
            organization_id=ctx.organization_id,
            session_id=pos.id,
            type="variance",
            amount=variance,
            reason="close",
        )
    )
    await session.flush()
    await post_cash_variance(
        session, ctx, session_id=pos.id, branch_id=pos.branch_id, variance=variance
    )
    await write_audit(session, ctx, action="pos.session.close", entity_type="pos_session", entity_id=pos.id)
    return pos


async def complete_sale(
    session: AsyncSession,
    ctx: TenantContext,
    *,
    pos_session_id: UUID,
    items: list[dict],
    payments: list[dict],
    customer_id: UUID | None,
    idempotency_key: str,
) -> Sale:
    digest = request_hash({"items": items, "payments": payments, "customer_id": str(customer_id or "")})
    cached = await get_idempotent(session, ctx, idempotency_key, digest)
    if cached:
        existing = await session.get(Sale, UUID(cached["id"]))
        if existing is not None:
            return existing

    existing_key = await session.scalar(
        select(Sale).where(
            Sale.organization_id == ctx.organization_id, Sale.idempotency_key == idempotency_key
        )
    )
    if existing_key is not None:
        return existing_key

    pos = await _locked_session(session, ctx, pos_session_id)
    if ctx.branch_id is not None and pos.branch_id != ctx.branch_id:
        raise AppError(403, "POS session is not in the selected branch", code="permission_denied")

    computed_items = []
    subtotal = ZERO
    discount_total = ZERO
    tax_total = ZERO
    for raw in items:
        variant = await get_variant(session, ctx, raw["variant_id"])
        product = await session.get(Product, variant.product_id)
        if product is None:
            raise AppError(404, "Product not found", code="not_found")
        qty = money(raw["qty"])
        if qty <= ZERO:
            raise AppError(422, "Quantity must be positive", code="validation_error")
        price = await resolve_price(
            session,
            ctx,
            variant_id=variant.id,
            branch_id=pos.branch_id,
            price_list_code=raw.get("price_list_code") or "retail",
            on=date.today(),
        )
        unit_price = money(price.amount)
        discount = money(raw.get("discount_amount") or 0)
        line_net = money(qty * unit_price - discount)
        tax_rate = await get_tax_rate(session, ctx, raw.get("tax_rate_id"))
        net, tax = compute_tax(line_net, tax_rate)
        line_total = money(net + tax)
        subtotal += net
        discount_total += discount
        tax_total += tax
        computed_items.append(
            {
                "variant": variant,
                "product": product,
                "qty": qty,
                "unit_price": unit_price,
                "discount": discount,
                "tax": tax,
                "tax_rate_id": tax_rate.id if tax_rate else None,
                "line_total": line_total,
                "uom_id": product.uom_id,
                "batch_id": raw.get("batch_id"),
            }
        )
    total = money(subtotal + tax_total)
    if not payments:
        raise AppError(422, "At least one payment is required", code="validation_error")

    number = await next_document_number(session, ctx, document_type="sale", prefix="SA")
    sale = Sale(
        organization_id=ctx.organization_id,
        branch_id=pos.branch_id,
        session_id=pos.id,
        customer_id=customer_id,
        document_number=number,
        status="awaiting_payment",
        sale_type="pos",
        subtotal=subtotal,
        discount_total=discount_total,
        tax_total=tax_total,
        total=total,
        currency_code=price.currency_code if computed_items else "ZMW",
        idempotency_key=idempotency_key,
    )
    session.add(sale)
    await session.flush()

    for item in computed_items:
        session.add(
            SaleItem(
                organization_id=ctx.organization_id,
                sale_id=sale.id,
                variant_id=item["variant"].id,
                description=item["variant"].name,
                qty=item["qty"],
                uom_id=item["uom_id"],
                unit_price=item["unit_price"],
                discount_amount=item["discount"],
                tax_rate_id=item["tax_rate_id"],
                tax_amount=item["tax"],
                line_total=item["line_total"],
            )
        )

    allocated = ZERO
    completed_tenders: list[tuple[str, Decimal]] = []
    all_completed = True
    for raw in payments:
        method = raw["method"]
        amount = money(raw["amount"])
        if amount <= ZERO:
            raise AppError(422, "Payment amount must be positive", code="validation_error")
        if method == "store_credit":
            if customer_id is None:
                raise AppError(422, "A customer is required for store credit", code="validation_error")
            if "customers.credit" not in ctx.permissions:
                raise AppError(403, "Missing permission customers.credit", code="permission_denied")
            await assert_credit_available(session, ctx, customer_id, amount)
            status = "completed"
            provider_name = "store_credit"
            provider_ref = None
        else:
            try:
                provider = provider_for(method, raw.get("provider"))
            except ValueError as exc:
                raise AppError(422, "Unknown payment method", code="validation_error") from exc
            intent = provider.create_intent(amount, sale.currency_code, sale.document_number)
            status = intent.status
            provider_name = intent.provider
            provider_ref = intent.provider_ref
        payment = Payment(
            organization_id=ctx.organization_id,
            sale_id=sale.id,
            customer_id=customer_id,
            method=method,
            status=status,
            amount=amount,
            provider=provider_name,
            provider_ref=provider_ref,
            received_at=datetime.now(UTC) if status == "completed" else None,
        )
        session.add(payment)
        await session.flush()
        session.add(
            PaymentAllocation(
                organization_id=ctx.organization_id,
                payment_id=payment.id,
                source_type="sale",
                source_id=sale.id,
                amount=amount,
            )
        )
        if status == "completed":
            allocated += amount
            completed_tenders.append((method, amount))
            if method == "cash":
                session.add(
                    PosCashMovement(
                        organization_id=ctx.organization_id,
                        session_id=pos.id,
                        type="sale",
                        amount=amount,
                        reason=sale.document_number,
                    )
                )
            if method == "store_credit":
                await apply_credit_delta(session, ctx, customer_id, amount)
        else:
            all_completed = False

    if allocated > total:
        raise AppError(422, "Payments exceed the sale total", code="validation_error")
    if all_completed and allocated != total:
        raise AppError(422, "Payments must equal the sale total", code="validation_error")

    if all_completed and allocated == total:
        await _fulfill_sale(session, ctx, sale, computed_items, completed_tenders, pos)
    else:
        sale.status = "awaiting_payment"

    receipt_number = await next_document_number(session, ctx, document_type="receipt", prefix="RC")
    session.add(
        Receipt(
            organization_id=ctx.organization_id,
            sale_id=sale.id,
            document_number=receipt_number,
            payload_json={
                "sale_id": str(sale.id),
                "total": str(sale.total),
                "status": sale.status,
                "document_number": sale.document_number,
            },
        )
    )
    await session.flush()
    await store_idempotent(
        session,
        ctx,
        idempotency_key,
        digest,
        {"id": str(sale.id), "status": sale.status, "document_number": sale.document_number},
    )
    return sale


async def confirm_payment(session: AsyncSession, ctx: TenantContext, payment_id: UUID) -> Payment:
    payment = await session.get(Payment, payment_id)
    if payment is None:
        raise AppError(404, "Payment not found", code="not_found")
    if payment.status == "completed":
        return payment
    if payment.provider != "mock_mobile_pending":
        raise AppError(422, "Only mock mobile payments can be confirmed here", code="validation_error")
    payment.status = "completed"
    payment.received_at = datetime.now(UTC)
    await session.flush()
    if payment.sale_id is None:
        return payment
    sale = await session.get(Sale, payment.sale_id)
    if sale is None:
        return payment
    payments = list(await session.scalars(select(Payment).where(Payment.sale_id == sale.id)))
    if any(row.status != "completed" for row in payments):
        return payment
    allocated = sum((row.amount for row in payments), ZERO)
    if allocated != sale.total:
        return payment
    items = list(await session.scalars(select(SaleItem).where(SaleItem.sale_id == sale.id)))
    pos = await session.get(PosSession, sale.session_id) if sale.session_id else None
    computed = []
    for item in items:
        variant = await session.get(ProductVariant, item.variant_id)
        product = await session.get(Product, variant.product_id) if variant else None
        computed.append(
            {
                "variant": variant,
                "product": product,
                "qty": item.qty,
                "batch_id": None,
            }
        )
    tenders = [(row.method, row.amount) for row in payments]
    if pos is None:
        raise AppError(409, "POS session is required to complete this sale", code="conflict")
    await _fulfill_sale(session, ctx, sale, computed, tenders, pos)
    return payment


async def refund_sale(
    session: AsyncSession,
    ctx: TenantContext,
    sale_id: UUID,
    *,
    items: list[dict],
    reason: str | None,
    restock: bool,
    idempotency_key: str,
) -> Refund:
    digest = request_hash({"sale_id": str(sale_id), "items": items, "restock": restock})
    cached = await get_idempotent(session, ctx, idempotency_key, digest)
    if cached:
        existing = await session.get(Refund, UUID(cached["id"]))
        if existing is not None:
            return existing
    sale = await session.get(Sale, sale_id)
    if sale is None:
        raise AppError(404, "Sale not found", code="not_found")
    if sale.status not in {"completed", "partially_refunded"}:
        raise AppError(409, "Only a completed sale can be refunded", code="conflict")
    pos = await session.get(PosSession, sale.session_id) if sale.session_id else None
    total = ZERO
    tax_total = ZERO
    restock_cogs = ZERO
    refund = Refund(
        organization_id=ctx.organization_id,
        sale_id=sale.id,
        reason=reason,
        status="completed",
        total=ZERO,
        restock=restock,
        idempotency_key=idempotency_key,
    )
    session.add(refund)
    await session.flush()
    for raw in items:
        sale_item = await session.get(SaleItem, raw["sale_item_id"])
        if sale_item is None or sale_item.sale_id != sale.id:
            raise AppError(422, "Sale item not found", code="validation_error")
        already = await session.scalar(
            select(RefundItem.qty).where(RefundItem.sale_item_id == sale_item.id)
        )
        already_qty = money(already or 0)
        qty = money(raw["qty"])
        if qty <= ZERO or already_qty + qty > sale_item.qty:
            raise AppError(422, "Refund quantity exceeds remaining quantity", code="validation_error")
        share = qty / sale_item.qty
        amount = money(sale_item.line_total * share)
        tax = money(sale_item.tax_amount * share)
        total += amount
        tax_total += tax
        session.add(
            RefundItem(
                organization_id=ctx.organization_id,
                refund_id=refund.id,
                sale_item_id=sale_item.id,
                qty=qty,
                amount=amount,
            )
        )
        if restock and pos is not None:
            movement = await receive(
                session,
                ctx,
                warehouse_id=pos.warehouse_id,
                variant_id=sale_item.variant_id,
                qty=qty,
                unit_cost=ZERO,
                source_type="refund_return",
                source_id=refund.id,
                batch_id=None,
            )
            restock_cogs += money(abs(movement.qty_delta) * movement.unit_cost)
    refund.total = total
    if pos is not None:
        session.add(
            PosCashMovement(
                organization_id=ctx.organization_id,
                session_id=pos.id,
                type="refund",
                amount=total,
                reason=reason,
            )
        )
    remaining = sale.total - total
    prior = await session.scalars(select(Refund).where(Refund.sale_id == sale.id, Refund.id != refund.id))
    prior_total = sum((row.total for row in prior), ZERO)
    if prior_total + total >= sale.total:
        sale.status = "refunded"
    else:
        sale.status = "partially_refunded"
        _ = remaining
    await post_refund(
        session,
        ctx,
        refund_id=refund.id,
        branch_id=sale.branch_id,
        customer_id=sale.customer_id,
        amount=total,
        tax=tax_total,
        restock_cogs=restock_cogs,
        method="cash",
    )
    await session.flush()
    await store_idempotent(
        session, ctx, idempotency_key, digest, {"id": str(refund.id), "total": str(refund.total)}
    )
    return refund


async def get_sale(session: AsyncSession, ctx: TenantContext, sale_id: UUID) -> Sale:
    sale = await session.get(Sale, sale_id)
    if sale is None:
        raise AppError(404, "Sale not found", code="not_found")
    if not ctx.can_access_branch(sale.branch_id):
        raise AppError(403, "Branch is not granted to this membership", code="permission_denied")
    return sale


async def list_sales(session: AsyncSession, ctx: TenantContext) -> list[Sale]:
    statement = select(Sale).where(Sale.organization_id == ctx.organization_id)
    if not ctx.access_all_branches:
        if not ctx.branch_ids:
            return []
        statement = statement.where(Sale.branch_id.in_(ctx.branch_ids))
    rows = await session.scalars(statement.order_by(Sale.document_number.desc()))
    return list(rows)


async def get_receipt(session: AsyncSession, ctx: TenantContext, receipt_id: UUID) -> Receipt:
    row = await session.get(Receipt, receipt_id)
    if row is None:
        raise AppError(404, "Receipt not found", code="not_found")
    await get_sale(session, ctx, row.sale_id)
    return row


async def sale_items(session: AsyncSession, sale_id: UUID) -> list[SaleItem]:
    return list(await session.scalars(select(SaleItem).where(SaleItem.sale_id == sale_id)))


async def sale_payments(session: AsyncSession, sale_id: UUID) -> list[Payment]:
    return list(await session.scalars(select(Payment).where(Payment.sale_id == sale_id)))


async def _fulfill_sale(
    session: AsyncSession,
    ctx: TenantContext,
    sale: Sale,
    computed_items: list[dict],
    tenders: list[tuple[str, Decimal]],
    pos: PosSession,
) -> None:
    cogs = ZERO
    for item in computed_items:
        product = item["product"]
        if product is None or not product.track_inventory:
            continue
        movement = await issue(
            session,
            ctx,
            warehouse_id=pos.warehouse_id,
            variant_id=item["variant"].id,
            qty=item["qty"],
            source_type="sale",
            source_id=sale.id,
            batch_id=item.get("batch_id"),
            movement_type="sale_issue",
        )
        cogs += money(abs(movement.qty_delta) * movement.unit_cost)
    sale.status = "completed"
    sale.completed_at = datetime.now(UTC)
    revenue = money(sale.total - sale.tax_total)
    await post_sale(
        session,
        ctx,
        sale_id=sale.id,
        branch_id=sale.branch_id,
        customer_id=sale.customer_id,
        revenue=revenue,
        tax=sale.tax_total,
        cogs=cogs,
        tenders=tenders,
    )
    await write_audit(
        session,
        ctx,
        action="sales.complete",
        entity_type="sale",
        entity_id=sale.id,
        after={"document_number": sale.document_number, "total": str(sale.total)},
    )


async def _locked_session(session: AsyncSession, ctx: TenantContext, session_id: UUID) -> PosSession:
    pos = await session.scalar(
        select(PosSession).where(PosSession.id == session_id).with_for_update()
    )
    if pos is None:
        raise AppError(404, "POS session not found", code="not_found")
    if pos.status != "open":
        raise AppError(409, "POS session is not open", code="conflict")
    if pos.opened_by_user_id != ctx.user_id and "org.manage" not in ctx.permissions:
        raise AppError(403, "POS session belongs to another cashier", code="permission_denied")
    return pos


async def _expected_cash(session: AsyncSession, pos: PosSession) -> Decimal:
    rows = await session.scalars(select(PosCashMovement).where(PosCashMovement.session_id == pos.id))
    expected = money(pos.opening_float)
    for row in rows:
        if row.type in {"in", "sale"}:
            expected += row.amount
        elif row.type in {"out", "refund"}:
            expected -= row.amount
    return expected
