from datetime import date

import pytest
from httpx import AsyncClient

from tests.helpers import assert_error, onboard_shop, register, unique_email, tenant_headers
from tests.helpers import login


async def _sale(client: AsyncClient, shop: dict, qty: int, key: str) -> dict:
    opened = await client.post(
        "/api/v1/pos/sessions",
        headers=shop["headers"],
        json={"warehouse_id": shop["warehouse_id"], "opening_float": 100},
    )
    assert opened.status_code == 201, opened.text
    sale = await client.post(
        f"/api/v1/pos/sessions/{opened.json()['id']}/sales",
        headers={**shop["headers"], "Idempotency-Key": key},
        json={
            "items": [{"variant_id": shop["variant_id"], "qty": qty}],
            "payments": [{"method": "cash", "amount": qty * 10}],
        },
    )
    assert sale.status_code == 201, sale.text
    return sale.json()


async def _add_cashier(client: AsyncClient, shop: dict) -> dict:
    email = unique_email("cashier")
    await register(client, email)
    token = await login(client, email)
    response = await client.post(
        "/api/v1/memberships",
        headers=shop["headers"],
        json={
            "email": email,
            "role_code": "cashier",
            "access_all_branches": False,
            "branch_ids": [shop["branch_id"]],
        },
    )
    assert response.status_code == 201, response.text
    return {"token": token, "membership_id": response.json()["id"]}


@pytest.mark.asyncio
async def test_sales_report_totals_match_completed_sales(client: AsyncClient) -> None:
    shop = await onboard_shop(client, "Report Shop")
    first = await _sale(client, shop, 2, "rep-sale-1")
    second = await _sale(client, shop, 1, "rep-sale-2")
    expected = float(first["total"]) + float(second["total"])
    today = date.today().isoformat()
    report = await client.get(
        "/api/v1/reporting/sales",
        headers=shop["headers"],
        params={"from_date": today, "to_date": today},
    )
    assert report.status_code == 200, report.text
    body = report.json()
    assert body["totals"]["sales_count"] == 2
    assert body["totals"]["revenue"] == pytest.approx(expected)
    summary = await client.get("/api/v1/reporting/summary", headers=shop["headers"])
    assert summary.status_code == 200, summary.text
    assert summary.json()["today_revenue"] == pytest.approx(expected)
    csv = await client.get(
        "/api/v1/reporting/sales",
        headers=shop["headers"],
        params={"export": "csv"},
    )
    assert csv.status_code == 200, csv.text
    assert "text/csv" in csv.headers["content-type"]
    assert "revenue" in csv.text


@pytest.mark.asyncio
async def test_cashier_cannot_view_reports(client: AsyncClient) -> None:
    shop = await onboard_shop(client, "Cashier Reports")
    cashier = await _add_cashier(client, shop)
    headers = tenant_headers(cashier["token"], shop["org_id"], shop["branch_id"])
    denied = await client.get("/api/v1/reporting/sales", headers=headers)
    assert_error(denied, 403, "permission_denied")
    summary = await client.get("/api/v1/reporting/summary", headers=headers)
    assert_error(summary, 403, "permission_denied")


@pytest.mark.asyncio
async def test_reports_are_tenant_isolated(client: AsyncClient) -> None:
    shop_a = await onboard_shop(client, "Iso Reports A")
    shop_b = await onboard_shop(client, "Iso Reports B")
    await _sale(client, shop_a, 3, "iso-a-sale")
    leaked = await client.get("/api/v1/reporting/sales", headers=shop_b["headers"])
    assert leaked.status_code == 200, leaked.text
    assert leaked.json()["totals"]["sales_count"] == 0
    swapped = await client.get(
        "/api/v1/reporting/sales",
        headers=tenant_headers(shop_a["token"], shop_b["org_id"], shop_b["branch_id"]),
    )
    assert_error(swapped, 403, "permission_denied")
