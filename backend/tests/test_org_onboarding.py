import pytest
from httpx import AsyncClient

from tests.helpers import (
    assert_error,
    auth_headers,
    create_organization,
    login,
    register,
    tenant_headers,
    unique_email,
)


@pytest.mark.asyncio
async def test_onboarding_creates_branch_warehouse_and_settings(client: AsyncClient) -> None:
    email = unique_email("onboard")
    await register(client, email)
    token = await login(client, email)
    response = await client.post(
        "/api/v1/organizations/onboarding",
        headers=auth_headers(token),
        json={
            "name": "Lusaka Grocers",
            "industry_code": "grocery",
            "timezone": "Africa/Lusaka",
            "base_currency_code": "ZMW",
            "branch": {"code": "HQ", "name": "Head office"},
            "warehouse": {"code": "HQ-WH", "name": "Main warehouse"},
        },
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["industry_code"] is None or body["timezone"] == "Africa/Lusaka"
    assert body["branch_id"]
    assert body["warehouse_id"]

    headers = tenant_headers(token, body["id"], body["branch_id"])
    current = await client.get("/api/v1/organizations/current", headers=headers)
    assert current.status_code == 200, current.text
    assert current.json()["timezone"] == "Africa/Lusaka"
    assert current.json()["base_currency_code"] == "ZMW"
    assert current.json()["industry_code"] == "grocery"

    settings = await client.get("/api/v1/organization-settings", headers=headers)
    assert settings.status_code == 200, settings.text
    assert settings.json()["settings"]["inventory"]["allow_negative_stock"] is False
    assert settings.json()["settings"]["catalogue"]["track_batches"] is True

    warehouses = await client.get("/api/v1/warehouses", headers=headers)
    assert warehouses.status_code == 200, warehouses.text
    assert any(row["id"] == body["warehouse_id"] for row in warehouses.json())

    second = await client.post(
        "/api/v1/branches",
        headers=headers,
        json={"code": "NDL", "name": "Ndola"},
    )
    assert second.status_code == 201, second.text
    ndola_wh = await client.get(
        "/api/v1/warehouses",
        headers=headers,
        params={"branch_id": second.json()["id"]},
    )
    assert ndola_wh.status_code == 200
    assert len(ndola_wh.json()) == 1

    saved = await client.put(
        "/api/v1/organization-settings",
        headers=headers,
        json={
            "settings": {
                "inventory": {"allow_negative_stock": False},
                "fiscal_year_start_month": 4,
            }
        },
    )
    assert saved.status_code == 200, saved.text
    assert saved.json()["settings"]["fiscal_year_start_month"] == 4

    packs = await client.get("/api/v1/industries")
    assert packs.status_code == 200
    assert {row["code"] for row in packs.json()} >= {"general", "grocery", "pharmacy", "clothing"}


@pytest.mark.asyncio
async def test_settings_and_warehouses_are_tenant_isolated(client: AsyncClient) -> None:
    email_a = unique_email("iso-a")
    email_b = unique_email("iso-b")
    await register(client, email_a)
    await register(client, email_b)
    token_a = await login(client, email_a)
    token_b = await login(client, email_b)
    org_a = await create_organization(client, token_a, "Iso A")
    org_b = await create_organization(client, token_b, "Iso B")
    await client.put(
        "/api/v1/organization-settings",
        headers=tenant_headers(token_a, org_a["id"]),
        json={"settings": {"mark": "a"}},
    )
    leaked = await client.get(
        "/api/v1/organization-settings",
        headers=tenant_headers(token_a, org_b["id"]),
    )
    assert_error(leaked, 403, "permission_denied")
    own = await client.get(
        "/api/v1/organization-settings",
        headers=tenant_headers(token_a, org_a["id"]),
    )
    assert own.json()["settings"]["mark"] == "a"
