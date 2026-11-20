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
async def test_invite_join_and_cross_tenant_closed(client: AsyncClient) -> None:
    owner_a = unique_email("inv-a")
    owner_b = unique_email("inv-b")
    guest = unique_email("guest")
    await register(client, owner_a, "Owner A")
    await register(client, owner_b, "Owner B")
    await register(client, guest, "Guest")
    token_a = await login(client, owner_a)
    token_b = await login(client, owner_b)
    token_guest = await login(client, guest)
    org_a = await create_organization(client, token_a, "Invite A")
    org_b = await create_organization(client, token_b, "Invite B")

    invited = await client.post(
        "/api/v1/invitations",
        headers=tenant_headers(token_a, org_a["id"]),
        json={
            "email": guest,
            "role_codes": ["cashier"],
            "branch_ids": [],
            "access_all_branches": True,
        },
    )
    assert invited.status_code == 201, invited.text
    invite_token = invited.json()["token"]

    accepted = await client.post(
        "/api/v1/invitations/accept",
        headers=auth_headers(token_guest),
        json={"token": invite_token},
    )
    assert accepted.status_code == 200, accepted.text
    assert "cashier" in accepted.json()["role_codes"]

    listing = await client.get("/api/v1/organizations", headers=auth_headers(token_guest))
    assert {row["id"] for row in listing.json()} == {org_a["id"]}

    foreign = await client.get(
        "/api/v1/branches",
        headers=tenant_headers(token_guest, org_b["id"]),
    )
    assert_error(foreign, 403, "permission_denied")

    mismatch = unique_email("other-guest")
    await register(client, mismatch, "Other")
    other_token = await login(client, mismatch)
    stolen = await client.post(
        "/api/v1/invitations/accept",
        headers=auth_headers(other_token),
        json={"token": invite_token},
    )
    assert stolen.status_code in {400, 403, 404}
