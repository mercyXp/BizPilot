from uuid import UUID, uuid4

from httpx import AsyncClient, Response


def unique_email(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex[:10]}@example.com"


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def tenant_headers(
    token: str,
    organization_id: UUID | str,
    branch_id: UUID | str | None = None,
) -> dict[str, str]:
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Organization-Id": str(organization_id),
    }
    if branch_id is not None:
        headers["X-Branch-Id"] = str(branch_id)
    return headers


def assert_error(response: Response, status: int, code: str) -> None:
    assert response.status_code == status, response.text
    body = response.json()
    assert body["error"]["code"] == code
    assert "traceback" not in response.text.lower()
    assert "password_hash" not in response.text


async def register(
    client: AsyncClient,
    email: str,
    full_name: str = "Test User",
    *,
    verify: bool = True,
) -> dict:
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "password123", "full_name": full_name},
    )
    assert response.status_code == 201, response.text
    body = response.json()
    if verify:
        token = body.get("verification_token")
        assert token, body
        verified = await client.post("/api/v1/auth/verify-email", json={"token": token})
        assert verified.status_code == 200, verified.text
        body["email_verified"] = True
    return body


async def login(client: AsyncClient, email: str) -> str:
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "password123"},
    )
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


async def create_organization(client: AsyncClient, token: str, name: str) -> dict:
    response = await client.post(
        "/api/v1/organizations",
        headers=auth_headers(token),
        json={"name": name},
    )
    assert response.status_code == 201, response.text
    return response.json()


async def onboard_shop(client: AsyncClient, name: str = "Shop") -> dict:
    email = unique_email("shop")
    await register(client, email)
    token = await login(client, email)
    onboard = await client.post(
        "/api/v1/organizations/onboarding",
        headers=auth_headers(token),
        json={
            "name": name,
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
    price = await client.post(
        "/api/v1/product-prices",
        headers=headers,
        json={"variant_id": variant_id, "amount": 10, "currency_code": "ZMW"},
    )
    assert price.status_code == 201, price.text
    stock = await client.post(
        "/api/v1/inventory/adjustments",
        headers=headers,
        json={
            "warehouse_id": org["warehouse_id"],
            "variant_id": variant_id,
            "qty_delta": 20,
            "unit_cost": 4,
            "source_type": "purchase_receipt",
        },
    )
    assert stock.status_code == 201, stock.text
    return {
        "email": email,
        "token": token,
        "org_id": org["id"],
        "membership_id": org["membership_id"],
        "branch_id": org["branch_id"],
        "warehouse_id": org["warehouse_id"],
        "headers": headers,
        "variant_id": variant_id,
        "uom_id": uom_id,
    }


async def create_branch(
    client: AsyncClient,
    token: str,
    organization_id: str,
    code: str,
    name: str,
) -> dict:
    response = await client.post(
        "/api/v1/branches",
        headers=tenant_headers(token, organization_id),
        json={"code": code, "name": name},
    )
    assert response.status_code == 201, response.text
    return response.json()
