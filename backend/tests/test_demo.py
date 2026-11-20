import pytest
from httpx import AsyncClient

from tests.helpers import tenant_headers


async def enter(client: AsyncClient, role: str) -> dict:
    response = await client.post("/api/v1/demo/enter", json={"role": role})
    assert response.status_code == 200, response.text
    return response.json()


def headers_for(body: dict, branch_id: str | None = None) -> dict[str, str]:
    org_id = body["demo"]["organization"]["id"]
    branch = branch_id or body["demo"]["branches"][0]["id"]
    return tenant_headers(body["access_token"], org_id, branch)


@pytest.mark.asyncio
async def test_demo_roles_are_public(client: AsyncClient) -> None:
    response = await client.get("/api/v1/demo/roles")
    assert response.status_code == 200, response.text
    keys = [row["key"] for row in response.json()["roles"]]
    assert keys == ["owner", "admin", "manager", "salesperson", "stock", "auditor"]


@pytest.mark.asyncio
async def test_owner_enters_shared_mwamba_tenant(client: AsyncClient) -> None:
    body = await enter(client, "owner")
    assert body["user"]["email"] == "owner@demo.bizpilot.local"
    assert body["demo"]["organization"]["name"] == "Mwamba Retail Group"
    assert body["demo"]["kpis"]["branches"] == 3
    assert body["demo"]["kpis"]["products"] >= 12
    names = {row["name"] for row in body["demo"]["branches"]}
    assert names == {"Lusaka Central", "Chelstone", "Kitwe"}


@pytest.mark.asyncio
async def test_salesperson_cannot_read_accounting(client: AsyncClient) -> None:
    body = await enter(client, "salesperson")
    headers = headers_for(body)
    forbidden = await client.get("/api/v1/reports/profit-and-loss", headers=headers)
    assert forbidden.status_code == 403, forbidden.text
    journals = await client.get("/api/v1/journals", headers=headers)
    assert journals.status_code == 403, journals.text
    sales = await client.get("/api/v1/sales", headers=headers)
    assert sales.status_code == 200, sales.text


@pytest.mark.asyncio
async def test_auditor_cannot_create_sale(client: AsyncClient) -> None:
    body = await enter(client, "auditor")
    headers = headers_for(body)
    reports = await client.get("/api/v1/reports/profit-and-loss", headers=headers)
    assert reports.status_code == 200, reports.text
    pos = await client.post(
        "/api/v1/pos/sessions",
        headers=headers,
        json={"warehouse_id": "00000000-0000-0000-0000-000000000001", "opening_float": 0},
    )
    assert pos.status_code in {403, 422, 404}


@pytest.mark.asyncio
async def test_salesperson_cannot_record_expense(client: AsyncClient) -> None:
    body = await enter(client, "salesperson")
    headers = headers_for(body)
    response = await client.post(
        "/api/v1/expenses",
        headers=headers,
        json={
            "vendor_name": "ZESCO",
            "amount": 120,
            "incurred_on": "2026-11-01",
            "payment_method": "cash",
        },
    )
    assert response.status_code == 403, response.text


@pytest.mark.asyncio
async def test_manager_can_record_expense(client: AsyncClient) -> None:
    body = await enter(client, "manager")
    headers = headers_for(body)
    response = await client.post(
        "/api/v1/expenses",
        headers=headers,
        json={
            "vendor_name": "ZESCO",
            "amount": 120,
            "incurred_on": "2026-11-01",
            "payment_method": "cash",
        },
    )
    assert response.status_code == 201, response.text


@pytest.mark.asyncio
async def test_role_switch_stays_on_same_business(client: AsyncClient) -> None:
    owner = await enter(client, "owner")
    org_id = owner["demo"]["organization"]["id"]
    switched = await client.post(
        "/api/v1/demo/switch",
        headers={"Authorization": f"Bearer {owner['access_token']}"},
        json={"role": "manager"},
    )
    assert switched.status_code == 200, switched.text
    body = switched.json()
    assert body["user"]["email"] == "manager@demo.bizpilot.local"
    assert body["demo"]["organization"]["id"] == org_id
