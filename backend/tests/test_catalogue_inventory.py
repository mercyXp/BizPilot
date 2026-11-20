import pytest
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import get_settings
from tests.helpers import (
    assert_error,
    auth_headers,
    login,
    register,
    tenant_headers,
    unique_email,
)


async def _shop(client: AsyncClient):
    email = unique_email("shop")
    await register(client, email)
    token = await login(client, email)
    onboard = await client.post(
        "/api/v1/organizations/onboarding",
        headers=auth_headers(token),
        json={
            "name": "Stock Shop",
            "industry_code": "general",
            "branch": {"code": "HQ", "name": "HQ"},
            "warehouse": {"code": "HQ-WH", "name": "HQ warehouse"},
        },
    )
    assert onboard.status_code == 201, onboard.text
    org = onboard.json()
    headers = tenant_headers(token, org["id"], org["branch_id"])
    uoms = await client.get("/api/v1/units-of-measure", headers=headers)
    assert uoms.status_code == 200, uoms.text
    uom_id = uoms.json()[0]["id"]
    product = await client.post(
        "/api/v1/products",
        headers=headers,
        json={"name": "Mealie meal", "type": "goods", "uom_id": uom_id, "sku": unique_email("sku")[:20]},
    )
    assert product.status_code == 201, product.text
    variants = await client.get(f"/api/v1/products/{product.json()['id']}/variants", headers=headers)
    variant_id = variants.json()[0]["id"]
    return {
        "token": token,
        "org_id": org["id"],
        "branch_id": org["branch_id"],
        "warehouse_id": org["warehouse_id"],
        "headers": headers,
        "variant_id": variant_id,
        "uom_id": uom_id,
    }


@pytest.mark.asyncio
async def test_branch_price_overrides_org_default(client: AsyncClient) -> None:
    shop = await _shop(client)
    headers = shop["headers"]
    org_price = await client.post(
        "/api/v1/product-prices",
        headers=headers,
        json={"variant_id": shop["variant_id"], "amount": 50, "currency_code": "ZMW"},
    )
    assert org_price.status_code == 201, org_price.text
    branch_price = await client.post(
        "/api/v1/product-prices",
        headers=headers,
        json={
            "variant_id": shop["variant_id"],
            "amount": 55,
            "currency_code": "ZMW",
            "branch_id": shop["branch_id"],
        },
    )
    assert branch_price.status_code == 201, branch_price.text
    resolved = await client.get(
        "/api/v1/product-prices/resolve",
        headers=headers,
        params={"variant_id": shop["variant_id"], "branch_id": shop["branch_id"]},
    )
    assert resolved.status_code == 200, resolved.text
    assert resolved.json()["amount"] == 55
    org_resolved = await client.get(
        "/api/v1/product-prices/resolve",
        headers=headers,
        params={"variant_id": shop["variant_id"]},
    )
    assert org_resolved.json()["amount"] == 50


@pytest.mark.asyncio
async def test_movements_are_immutable_and_balances_reconcile(client: AsyncClient) -> None:
    shop = await _shop(client)
    headers = shop["headers"]
    receipt = await client.post(
        "/api/v1/inventory/adjustments",
        headers=headers,
        json={
            "warehouse_id": shop["warehouse_id"],
            "variant_id": shop["variant_id"],
            "qty_delta": 10,
            "unit_cost": 8,
            "source_type": "purchase_receipt",
        },
    )
    assert receipt.status_code == 201, receipt.text
    movement_id = receipt.json()["id"]
    issue = await client.post(
        "/api/v1/inventory/adjustments",
        headers=headers,
        json={
            "warehouse_id": shop["warehouse_id"],
            "variant_id": shop["variant_id"],
            "qty_delta": -3,
            "unit_cost": 0,
        },
    )
    assert issue.status_code == 201, issue.text
    balances = await client.get(
        "/api/v1/stock-balances",
        headers=headers,
        params={"warehouse_id": shop["warehouse_id"]},
    )
    assert balances.status_code == 200, balances.text
    row = next(item for item in balances.json() if item["variant_id"] == shop["variant_id"])
    assert row["qty_on_hand"] == 7

    settings = get_settings()
    engine = create_async_engine(settings.database_url)
    async with engine.connect() as connection:
        await connection.execute(
            text("SELECT set_config('app.current_user_id', :user, true)"),
            {"user": "00000000-0000-0000-0000-000000000001"},
        )
        try:
            await connection.execute(
                text("UPDATE stock_movements SET qty_delta = 99 WHERE id = CAST(:id AS uuid)"),
                {"id": movement_id},
            )
            raise AssertionError("movement update should have been rejected")
        except Exception as exc:
            assert "append-only" in str(exc) or "stock_movements" in str(exc)
        await connection.rollback()
    await engine.dispose()


@pytest.mark.asyncio
async def test_purchase_order_does_not_receive_stock(client: AsyncClient) -> None:
    shop = await _shop(client)
    denied = await client.post(
        "/api/v1/inventory/adjustments",
        headers=shop["headers"],
        json={
            "warehouse_id": shop["warehouse_id"],
            "variant_id": shop["variant_id"],
            "qty_delta": 4,
            "unit_cost": 1,
            "source_type": "purchase_order",
        },
    )
    assert_error(denied, 422, "validation_error")
    balances = await client.get("/api/v1/stock-balances", headers=shop["headers"])
    assert balances.json() == []


@pytest.mark.asyncio
async def test_negative_stock_denied_by_default(client: AsyncClient) -> None:
    shop = await _shop(client)
    denied = await client.post(
        "/api/v1/inventory/adjustments",
        headers=shop["headers"],
        json={
            "warehouse_id": shop["warehouse_id"],
            "variant_id": shop["variant_id"],
            "qty_delta": -1,
            "unit_cost": 1,
        },
    )
    assert_error(denied, 409, "conflict")


@pytest.mark.asyncio
async def test_transfer_and_count_variance(client: AsyncClient) -> None:
    shop = await _shop(client)
    headers = shop["headers"]
    second_branch = await client.post(
        "/api/v1/branches",
        headers=headers,
        json={"code": "KIT", "name": "Kitwe"},
    )
    warehouses = await client.get(
        "/api/v1/warehouses",
        headers=headers,
        params={"branch_id": second_branch.json()["id"]},
    )
    dest_id = warehouses.json()[0]["id"]
    await client.post(
        "/api/v1/inventory/adjustments",
        headers=headers,
        json={
            "warehouse_id": shop["warehouse_id"],
            "variant_id": shop["variant_id"],
            "qty_delta": 5,
            "unit_cost": 2,
            "source_type": "purchase_receipt",
        },
    )
    created = await client.post(
        "/api/v1/stock-transfers",
        headers=tenant_headers(shop["token"], shop["org_id"]),
        json={
            "source_warehouse_id": shop["warehouse_id"],
            "dest_warehouse_id": dest_id,
            "items": [{"variant_id": shop["variant_id"], "qty": 5}],
        },
    )
    assert created.status_code == 201, created.text
    transfer_id = created.json()["id"]
    dispatched = await client.post(
        f"/api/v1/stock-transfers/{transfer_id}/dispatch",
        headers=tenant_headers(shop["token"], shop["org_id"]),
    )
    assert dispatched.status_code == 200, dispatched.text
    items = await client.get(
        f"/api/v1/stock-transfers/{transfer_id}/items",
        headers=tenant_headers(shop["token"], shop["org_id"]),
    )
    item_id = items.json()[0]["id"]
    received = await client.post(
        f"/api/v1/stock-transfers/{transfer_id}/receive",
        headers=tenant_headers(shop["token"], shop["org_id"]),
        json={"items": [{"item_id": item_id, "qty": 5}]},
    )
    assert received.status_code == 200, received.text
    assert received.json()["status"] == "completed"

    count = await client.post(
        "/api/v1/stock-counts",
        headers=tenant_headers(shop["token"], shop["org_id"]),
        json={
            "warehouse_id": dest_id,
            "items": [{"variant_id": shop["variant_id"], "counted_qty": 4}],
        },
    )
    assert count.status_code == 201, count.text
    posted = await client.post(
        f"/api/v1/stock-counts/{count.json()['id']}/post",
        headers=tenant_headers(shop["token"], shop["org_id"]),
    )
    assert posted.status_code == 200, posted.text
    dest_balances = await client.get(
        "/api/v1/stock-balances",
        headers=tenant_headers(shop["token"], shop["org_id"]),
        params={"warehouse_id": dest_id},
    )
    row = dest_balances.json()[0]
    assert row["qty_on_hand"] == 4


@pytest.mark.asyncio
async def test_catalogue_isolated_between_orgs(client: AsyncClient) -> None:
    shop = await _shop(client)
    other_email = unique_email("other-shop")
    await register(client, other_email)
    other_token = await login(client, other_email)
    other = await client.post(
        "/api/v1/organizations/onboarding",
        headers=auth_headers(other_token),
        json={
            "name": "Other Shop",
            "branch": {"code": "X", "name": "X"},
        },
    )
    leaked = await client.get(
        "/api/v1/products",
        headers=tenant_headers(other_token, other.json()["id"]),
    )
    assert leaked.status_code == 200
    assert leaked.json() == []
    swapped = await client.get(
        "/api/v1/products",
        headers=tenant_headers(shop["token"], other.json()["id"]),
    )
    assert_error(swapped, 403, "permission_denied")
