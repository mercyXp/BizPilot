import pytest
from httpx import AsyncClient

from tests.helpers import (
    assert_error,
    create_branch,
    create_organization,
    login,
    register,
    tenant_headers,
    unique_email,
)


async def _owner_with_branches(client: AsyncClient):
    email = unique_email("owner")
    owner = await register(client, email, "Owner")
    token = await login(client, email)
    org = await create_organization(client, token, "Owner Shop")
    branch_a = await create_branch(client, token, org["id"], "A", "Branch A")
    branch_b = await create_branch(client, token, org["id"], "B", "Branch B")
    return {
        "user_id": owner["id"],
        "email": email,
        "token": token,
        "org_id": org["id"],
        "membership_id": org["membership_id"],
        "branch_a": branch_a["id"],
        "branch_b": branch_b["id"],
    }


async def _add_member(
    client: AsyncClient,
    owner: dict,
    *,
    role_code: str,
    branch_ids: list[str] | None = None,
    access_all_branches: bool = False,
    full_name: str = "Member",
) -> dict:
    email = unique_email(role_code)
    user = await register(client, email, full_name)
    token = await login(client, email)
    response = await client.post(
        "/api/v1/memberships",
        headers=tenant_headers(owner["token"], owner["org_id"]),
        json={
            "email": email,
            "role_code": role_code,
            "access_all_branches": access_all_branches,
            "branch_ids": branch_ids or [],
        },
    )
    assert response.status_code == 201, response.text
    return {
        "user_id": user["id"],
        "email": email,
        "token": token,
        "membership_id": response.json()["id"],
    }


@pytest.mark.asyncio
async def test_cashier_cannot_post_journal_or_manage_branches(client: AsyncClient) -> None:
    owner = await _owner_with_branches(client)
    cashier = await _add_member(
        client,
        owner,
        role_code="cashier",
        branch_ids=[owner["branch_a"]],
    )

    journal = await client.post(
        "/api/v1/authorization/gates/journal-post",
        headers=tenant_headers(cashier["token"], owner["org_id"]),
    )
    assert_error(journal, 403, "permission_denied")

    created = await client.post(
        "/api/v1/branches",
        headers=tenant_headers(cashier["token"], owner["org_id"]),
        json={"code": "C", "name": "Should fail"},
    )
    assert_error(created, 403, "permission_denied")

    owner_journal = await client.post(
        "/api/v1/authorization/gates/journal-post",
        headers=tenant_headers(owner["token"], owner["org_id"]),
    )
    assert owner_journal.status_code == 200, owner_journal.text
    assert owner_journal.json()["effect"] == "authorization_only"


@pytest.mark.asyncio
async def test_viewer_cannot_adjust_stock_until_allow_override(client: AsyncClient) -> None:
    owner = await _owner_with_branches(client)
    viewer = await _add_member(
        client,
        owner,
        role_code="viewer",
        branch_ids=[owner["branch_a"]],
    )
    headers_a = tenant_headers(viewer["token"], owner["org_id"], owner["branch_a"])
    denied = await client.post("/api/v1/authorization/gates/inventory-adjust", headers=headers_a)
    assert_error(denied, 403, "permission_denied")

    override = await client.put(
        f"/api/v1/memberships/{viewer['membership_id']}/overrides",
        headers=tenant_headers(owner["token"], owner["org_id"]),
        json={"permission_code": "inventory.adjust", "effect": "allow"},
    )
    assert override.status_code == 200, override.text

    allowed = await client.post("/api/v1/authorization/gates/inventory-adjust", headers=headers_a)
    assert allowed.status_code == 200, allowed.text

    other_branch = await client.post(
        "/api/v1/authorization/gates/inventory-adjust",
        headers=tenant_headers(viewer["token"], owner["org_id"], owner["branch_b"]),
    )
    assert_error(other_branch, 403, "permission_denied")


@pytest.mark.asyncio
async def test_deny_override_beats_accountant_role(client: AsyncClient) -> None:
    owner = await _owner_with_branches(client)
    accountant = await _add_member(client, owner, role_code="accountant", access_all_branches=True)
    headers = tenant_headers(accountant["token"], owner["org_id"])

    allowed = await client.post("/api/v1/authorization/gates/journal-post", headers=headers)
    assert allowed.status_code == 200, allowed.text

    denied = await client.put(
        f"/api/v1/memberships/{accountant['membership_id']}/overrides",
        headers=tenant_headers(owner["token"], owner["org_id"]),
        json={"permission_code": "accounting.journal.post", "effect": "deny"},
    )
    assert denied.status_code == 200, denied.text
    blocked = await client.post("/api/v1/authorization/gates/journal-post", headers=headers)
    assert_error(blocked, 403, "permission_denied")

    cleared = await client.delete(
        f"/api/v1/memberships/{accountant['membership_id']}/overrides/accounting.journal.post",
        headers=tenant_headers(owner["token"], owner["org_id"]),
    )
    assert cleared.status_code == 200, cleared.text
    restored = await client.post("/api/v1/authorization/gates/journal-post", headers=headers)
    assert restored.status_code == 200, restored.text


@pytest.mark.asyncio
async def test_branch_grants_do_not_leak(client: AsyncClient) -> None:
    owner = await _owner_with_branches(client)
    cashier = await _add_member(
        client,
        owner,
        role_code="cashier",
        branch_ids=[owner["branch_a"]],
    )
    headers = tenant_headers(cashier["token"], owner["org_id"])

    listing = await client.get("/api/v1/branches", headers=headers)
    assert listing.status_code == 200, listing.text
    assert [row["id"] for row in listing.json()] == [owner["branch_a"]]

    own = await client.get(f"/api/v1/branches/{owner['branch_a']}", headers=headers)
    assert own.status_code == 200, own.text

    leaked = await client.get(f"/api/v1/branches/{owner['branch_b']}", headers=headers)
    assert_error(leaked, 403, "permission_denied")

    context = await client.get("/api/v1/authorization/context", headers=headers)
    assert context.status_code == 200, context.text
    body = context.json()
    assert body["access_all_branches"] is False
    assert body["branch_ids"] == [owner["branch_a"]]
    assert "accounting.journal.post" not in body["permissions"]
    assert "inventory.adjust" not in body["permissions"]
    assert "platform.orgs.manage" not in body["permissions"]


@pytest.mark.asyncio
async def test_owner_context_excludes_platform_permission(client: AsyncClient) -> None:
    owner = await _owner_with_branches(client)
    context = await client.get(
        "/api/v1/authorization/context",
        headers=tenant_headers(owner["token"], owner["org_id"]),
    )
    assert context.status_code == 200, context.text
    permissions = set(context.json()["permissions"])
    assert "accounting.journal.post" in permissions
    assert "branches.manage" in permissions
    assert "platform.orgs.manage" not in permissions
    assert context.json()["access_all_branches"] is True


@pytest.mark.asyncio
async def test_org_admin_cannot_assign_owner_or_post_journal(client: AsyncClient) -> None:
    owner = await _owner_with_branches(client)
    admin = await _add_member(client, owner, role_code="org_admin", access_all_branches=True)
    target_email = unique_email("promote")
    await register(client, target_email, "Promote")

    assign = await client.post(
        "/api/v1/memberships",
        headers=tenant_headers(admin["token"], owner["org_id"]),
        json={
            "email": target_email,
            "role_code": "owner",
            "access_all_branches": True,
            "branch_ids": [],
        },
    )
    assert_error(assign, 403, "permission_denied")

    journal = await client.post(
        "/api/v1/authorization/gates/journal-post",
        headers=tenant_headers(admin["token"], owner["org_id"]),
    )
    assert_error(journal, 403, "permission_denied")

    cashier = await client.post(
        "/api/v1/memberships",
        headers=tenant_headers(admin["token"], owner["org_id"]),
        json={
            "email": target_email,
            "role_code": "cashier",
            "access_all_branches": False,
            "branch_ids": [owner["branch_a"]],
        },
    )
    assert cashier.status_code == 201, cashier.text


@pytest.mark.asyncio
async def test_last_owner_role_cannot_be_removed_and_suspension_blocks_access(
    client: AsyncClient,
) -> None:
    owner = await _owner_with_branches(client)
    cashier = await _add_member(
        client,
        owner,
        role_code="cashier",
        branch_ids=[owner["branch_a"]],
    )
    remove = await client.delete(
        f"/api/v1/memberships/{owner['membership_id']}/roles/owner",
        headers=tenant_headers(owner["token"], owner["org_id"]),
    )
    assert_error(remove, 409, "conflict")

    suspended = await client.patch(
        f"/api/v1/memberships/{cashier['membership_id']}",
        headers=tenant_headers(owner["token"], owner["org_id"]),
        json={"status": "suspended"},
    )
    assert suspended.status_code == 200, suspended.text
    blocked = await client.get(
        "/api/v1/branches",
        headers=tenant_headers(cashier["token"], owner["org_id"]),
    )
    assert_error(blocked, 403, "permission_denied")


@pytest.mark.asyncio
async def test_unauthenticated_and_bad_credentials_use_the_error_envelope(
    client: AsyncClient,
) -> None:
    missing = await client.get("/api/v1/branches", headers={"X-Organization-Id": "00000000-0000-7000-8000-000000000099"})
    assert_error(missing, 401, "unauthenticated")

    email = unique_email("login")
    await register(client, email)
    wrong = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "not-the-password"},
    )
    assert_error(wrong, 401, "unauthenticated")

    duplicate = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "password123", "full_name": "Again"},
    )
    assert_error(duplicate, 409, "conflict")
