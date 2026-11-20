import pytest
from httpx import AsyncClient

from tests.helpers import assert_error, onboard_shop, tenant_headers


async def _open_session(client: AsyncClient, shop: dict) -> str:
    opened = await client.post(
        "/api/v1/pos/sessions",
        headers=shop["headers"],
        json={"warehouse_id": shop["warehouse_id"], "opening_float": 100},
    )
    assert opened.status_code == 201, opened.text
    return opened.json()["id"]


@pytest.mark.asyncio
async def test_cash_sale_updates_stock_and_rejects_duplicate_key(client: AsyncClient) -> None:
    shop = await onboard_shop(client, "POS Shop")
    session_id = await _open_session(client, shop)
    payload = {
        "items": [{"variant_id": shop["variant_id"], "qty": 2}],
        "payments": [{"method": "cash", "amount": 20}],
    }
    headers = {**shop["headers"], "Idempotency-Key": "sale-1"}
    first = await client.post(f"/api/v1/pos/sessions/{session_id}/sales", headers=headers, json=payload)
    assert first.status_code == 201, first.text
    assert first.json()["status"] == "completed"
    sale_id = first.json()["id"]
    second = await client.post(f"/api/v1/pos/sessions/{session_id}/sales", headers=headers, json=payload)
    assert second.status_code == 201, second.text
    assert second.json()["id"] == sale_id
    balances = await client.get(
        "/api/v1/stock-balances",
        headers=shop["headers"],
        params={"warehouse_id": shop["warehouse_id"]},
    )
    row = next(item for item in balances.json() if item["variant_id"] == shop["variant_id"])
    assert row["qty_on_hand"] == 18
    journals = await client.get("/api/v1/journals", headers=shop["headers"])
    assert journals.status_code == 200, journals.text
    assert any(row["source_type"] == "sale" for row in journals.json())


@pytest.mark.asyncio
async def test_mock_mobile_stays_pending_without_webhook(client: AsyncClient) -> None:
    shop = await onboard_shop(client, "Mobile Shop")
    session_id = await _open_session(client, shop)
    sale = await client.post(
        f"/api/v1/pos/sessions/{session_id}/sales",
        headers={**shop["headers"], "Idempotency-Key": "momo-1"},
        json={
            "items": [{"variant_id": shop["variant_id"], "qty": 1}],
            "payments": [{"method": "mobile_money", "amount": 10, "provider": "mock_mobile_pending"}],
        },
    )
    assert sale.status_code == 201, sale.text
    assert sale.json()["status"] == "awaiting_payment"
    payments = await client.get(f"/api/v1/sales/{sale.json()['id']}/payments", headers=shop["headers"])
    assert payments.json()[0]["status"] == "pending"
    balances = await client.get(
        "/api/v1/stock-balances",
        headers=shop["headers"],
        params={"warehouse_id": shop["warehouse_id"]},
    )
    row = next(item for item in balances.json() if item["variant_id"] == shop["variant_id"])
    assert row["qty_on_hand"] == 20
    confirm = await client.post(
        f"/api/v1/payments/{payments.json()[0]['id']}/confirm",
        headers=shop["headers"],
    )
    assert confirm.status_code == 200, confirm.text
    assert confirm.json()["status"] == "completed"
    completed = await client.get(f"/api/v1/sales/{sale.json()['id']}", headers=shop["headers"])
    assert completed.json()["status"] == "completed"
    after = await client.get(
        "/api/v1/stock-balances",
        headers=shop["headers"],
        params={"warehouse_id": shop["warehouse_id"]},
    )
    row = next(item for item in after.json() if item["variant_id"] == shop["variant_id"])
    assert row["qty_on_hand"] == 19


@pytest.mark.asyncio
async def test_refund_restocks_and_sale_is_branch_isolated(client: AsyncClient) -> None:
    shop = await onboard_shop(client, "Refund Shop")
    session_id = await _open_session(client, shop)
    sale = await client.post(
        f"/api/v1/pos/sessions/{session_id}/sales",
        headers={**shop["headers"], "Idempotency-Key": "refund-sale"},
        json={
            "items": [{"variant_id": shop["variant_id"], "qty": 1}],
            "payments": [{"method": "cash", "amount": 10}],
        },
    )
    assert sale.status_code == 201, sale.text
    items = await client.get(f"/api/v1/sales/{sale.json()['id']}/items", headers=shop["headers"])
    refund = await client.post(
        f"/api/v1/sales/{sale.json()['id']}/refunds",
        headers={**shop["headers"], "Idempotency-Key": "refund-1"},
        json={"items": [{"sale_item_id": items.json()[0]["id"], "qty": 1}], "restock": True},
    )
    assert refund.status_code == 201, refund.text
    balances = await client.get(
        "/api/v1/stock-balances",
        headers=shop["headers"],
        params={"warehouse_id": shop["warehouse_id"]},
    )
    row = next(item for item in balances.json() if item["variant_id"] == shop["variant_id"])
    assert row["qty_on_hand"] == 20

    other = await onboard_shop(client, "Other POS")
    leaked = await client.get("/api/v1/sales", headers=other["headers"])
    assert leaked.json() == []
    swapped = await client.get(
        "/api/v1/sales",
        headers=tenant_headers(shop["token"], other["org_id"], other["branch_id"]),
    )
    assert_error(swapped, 403, "permission_denied")
