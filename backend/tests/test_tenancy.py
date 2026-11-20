import pytest
from httpx import AsyncClient

from tests.helpers import (
    auth_headers,
    latest_email_token,
    login_user,
    register_user,
    unique_email,
    verify_user,
)


async def verified_login(client: AsyncClient, prefix: str) -> tuple[str, dict]:
    email = unique_email(prefix)
    await register_user(client, email)
    await verify_user(client, email)
    return email, await login_user(client, email)


@pytest.mark.asyncio
async def test_unverified_user_cannot_create_organization(client: AsyncClient) -> None:
    email = unique_email("unverified-org")
    await register_user(client, email)
    body = await login_user(client, email)
    response = await client.post(
        "/api/v1/organizations",
        headers=auth_headers(body),
        json={"name": "Blocked Co"},
    )
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "email_unverified"


@pytest.mark.asyncio
async def test_create_organization_and_list_memberships(client: AsyncClient) -> None:
    _email, body = await verified_login(client, "owner")
    created = await client.post(
        "/api/v1/organizations",
        headers=auth_headers(body),
        json={"name": "Lusaka Stores"},
    )
    assert created.status_code == 201, created.text
    org = created.json()
    assert org["name"] == "Lusaka Stores"
    assert org["base_currency_code"] == "ZMW"
    assert org["is_owner"] is True

    listed = await client.get("/api/v1/me/memberships", headers=auth_headers(body))
    assert listed.status_code == 200
    assert any(item["id"] == org["id"] for item in listed.json())


@pytest.mark.asyncio
async def test_user_can_belong_to_multiple_organizations(client: AsyncClient) -> None:
    _email, body = await verified_login(client, "multi")
    first = await client.post(
        "/api/v1/organizations", headers=auth_headers(body), json={"name": "Org One"}
    )
    second = await client.post(
        "/api/v1/organizations", headers=auth_headers(body), json={"name": "Org Two"}
    )
    assert first.status_code == 201
    assert second.status_code == 201
    listed = await client.get("/api/v1/me/memberships", headers=auth_headers(body))
    names = {item["name"] for item in listed.json()}
    assert names == {"Org One", "Org Two"}


@pytest.mark.asyncio
async def test_invitation_join_and_cross_tenant_blocked(client: AsyncClient) -> None:
    owner_email, owner = await verified_login(client, "owner2")
    invitee_email, invitee = await verified_login(client, "invitee")

    org_a = (
        await client.post(
            "/api/v1/organizations",
            headers=auth_headers(owner),
            json={"name": "Alpha Retail"},
        )
    ).json()
    org_b = (
        await client.post(
            "/api/v1/organizations",
            headers=auth_headers(invitee),
            json={"name": "Beta Pharmacy"},
        )
    ).json()

    invite = await client.post(
        "/api/v1/organizations/invitations",
        headers=auth_headers(owner, org_a["id"]),
        json={"email": invitee_email},
    )
    assert invite.status_code == 201, invite.text
    token = await latest_email_token(invitee_email, "organization_invite")

    accepted = await client.post(
        "/api/v1/invitations/accept",
        headers=auth_headers(invitee),
        json={"token": token},
    )
    assert accepted.status_code == 200, accepted.text
    memberships = await client.get("/api/v1/me/memberships", headers=auth_headers(invitee))
    ids = {item["id"] for item in memberships.json()}
    assert org_a["id"] in ids
    assert org_b["id"] in ids

    stolen = await client.get(
        "/api/v1/organizations/current",
        headers=auth_headers(owner, org_b["id"]),
    )
    assert stolen.status_code == 403

    allowed = await client.get(
        "/api/v1/organizations/current",
        headers=auth_headers(invitee, org_a["id"]),
    )
    assert allowed.status_code == 200
    assert allowed.json()["id"] == org_a["id"]
