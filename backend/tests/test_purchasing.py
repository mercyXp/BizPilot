import pytest
from httpx import AsyncClient

from tests.helpers import (
    assert_error,
    login,
    onboard_shop,
    register,
    tenant_headers,
    unique_email,
)


@pytest.mark.asyncio
async def test_grn_increases_stock_and_po_does_not(client: AsyncClient) -> None:
    shop = await onboard_shop(client, "Buy Shop")
    supplier = await client.post(
        "/api/v1/suppliers",
        headers=shop["headers"],
        json={"name": "Mill", "code": "MILL"},
    )
    assert supplier.status_code == 201, supplier.text
    po = await client.post(
        "/api/v1/purchase-orders",
        headers=shop["headers"],
        json={
            "supplier_id": supplier.json()["id"],
            "items": [{"variant_id": shop["variant_id"], "qty": 5, "unit_cost": 3}],
        },
    )
    assert po.status_code == 201, po.text
    submitted = await client.post(
        f"/api/v1/purchase-orders/{po.json()['id']}/submit",
        headers=shop["headers"],
    )
    assert submitted.status_code == 200, submitted.text
    approved = await client.post(
        f"/api/v1/purchase-orders/{po.json()['id']}/approve",
        headers=shop["headers"],
    )
    assert approved.status_code == 200, approved.text
    balances = await client.get(
        "/api/v1/stock-balances",
        headers=shop["headers"],
        params={"warehouse_id": shop["warehouse_id"]},
    )
    before = next(item for item in balances.json() if item["variant_id"] == shop["variant_id"])
    assert before["qty_on_hand"] == 20
    items = await client.get(f"/api/v1/purchase-orders/{po.json()['id']}/items", headers=shop["headers"])
    grn = await client.post(
        "/api/v1/goods-receipts",
        headers={**shop["headers"], "Idempotency-Key": "grn-1"},
        json={
            "purchase_order_id": po.json()["id"],
            "warehouse_id": shop["warehouse_id"],
            "items": [{"purchase_order_item_id": items.json()[0]["id"], "qty_accepted": 5}],
        },
    )
    assert grn.status_code == 201, grn.text
    after = await client.get(
        "/api/v1/stock-balances",
        headers=shop["headers"],
        params={"warehouse_id": shop["warehouse_id"]},
    )
    row = next(item for item in after.json() if item["variant_id"] == shop["variant_id"])
    assert row["qty_on_hand"] == 25
    invoice = await client.post(
        "/api/v1/supplier-invoices",
        headers=shop["headers"],
        json={
            "supplier_id": supplier.json()["id"],
            "purchase_order_id": po.json()["id"],
            "subtotal": 15,
            "tax_total": 0,
        },
    )
    assert invoice.status_code == 201, invoice.text
    pay = await client.post(
        "/api/v1/supplier-payments",
        headers=shop["headers"],
        json={
            "supplier_id": supplier.json()["id"],
            "invoice_id": invoice.json()["id"],
            "amount": 15,
            "method": "cash",
        },
    )
    assert pay.status_code == 201, pay.text


@pytest.mark.asyncio
async def test_cashier_cannot_approve_purchase_order(client: AsyncClient) -> None:
    shop = await onboard_shop(client, "Approve Shop")
    email = unique_email("cashier")
    await register(client, email, "Cashier")
    token = await login(client, email)
    member = await client.post(
        "/api/v1/memberships",
        headers=shop["headers"],
        json={
            "email": email,
            "role_code": "cashier",
            "access_all_branches": False,
            "branch_ids": [shop["branch_id"]],
        },
    )
    assert member.status_code == 201, member.text
    supplier = await client.post(
        "/api/v1/suppliers",
        headers=shop["headers"],
        json={"name": "Blocked", "code": "BLK"},
    )
    po = await client.post(
        "/api/v1/purchase-orders",
        headers=shop["headers"],
        json={
            "supplier_id": supplier.json()["id"],
            "items": [{"variant_id": shop["variant_id"], "qty": 1, "unit_cost": 1}],
        },
    )
    denied = await client.post(
        f"/api/v1/purchase-orders/{po.json()['id']}/approve",
        headers=tenant_headers(token, shop["org_id"], shop["branch_id"]),
    )
    assert_error(denied, 403, "permission_denied")
