import pytest
from httpx import AsyncClient

from tests.helpers import assert_error, login, register, unique_email


def _csrf(client: AsyncClient) -> dict[str, str]:
    token = client.cookies.get("bp_csrf")
    assert token
    return {"X-CSRF-Token": token}


@pytest.mark.asyncio
async def test_unverified_user_can_login_but_cannot_create_org(client: AsyncClient) -> None:
    email = unique_email("unverified")
    await register(client, email, verify=False)
    token = await login(client, email)
    blocked = await client.post(
        "/api/v1/organizations",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Too Soon"},
    )
    assert_error(blocked, 403, "email_unverified")
    me = await client.get("/api/v1/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["email_verified"] is False


@pytest.mark.asyncio
async def test_refresh_rotation_and_reuse_revokes_family(client: AsyncClient) -> None:
    email = unique_email("refresh")
    await register(client, email)
    first = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "password123"},
    )
    assert first.status_code == 200, first.text
    old_access = first.json()["access_token"]
    old_refresh = client.cookies.get("bp_refresh")
    csrf = _csrf(client)

    rotated = await client.post("/api/v1/auth/refresh", headers=csrf)
    assert rotated.status_code == 200, rotated.text
    new_access = rotated.json()["access_token"]
    assert new_access != old_access

    stale_access = await client.get("/api/v1/me", headers={"Authorization": f"Bearer {old_access}"})
    assert_error(stale_access, 401, "unauthenticated")

    rotated_csrf = _csrf(client)
    client.cookies.set("bp_refresh", old_refresh, path="/api/v1/auth")
    reuse = await client.post("/api/v1/auth/refresh", headers=rotated_csrf)
    assert_error(reuse, 401, "unauthenticated")


@pytest.mark.asyncio
async def test_logout_revokes_session(client: AsyncClient) -> None:
    email = unique_email("logout")
    await register(client, email)
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "password123"},
    )
    token = login_response.json()["access_token"]
    csrf = _csrf(client)
    logged_out = await client.post("/api/v1/auth/logout", headers=csrf)
    assert logged_out.status_code == 204
    me = await client.get("/api/v1/me", headers={"Authorization": f"Bearer {token}"})
    assert_error(me, 401, "unauthenticated")


@pytest.mark.asyncio
async def test_password_reset_rotates_session_version(client: AsyncClient) -> None:
    email = unique_email("reset")
    await register(client, email)
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "password123"},
    )
    old_token = login_response.json()["access_token"]
    requested = await client.post("/api/v1/auth/password-reset", json={"email": email})
    assert requested.status_code == 200
    reset_token = requested.json()["reset_token"]
    confirm = await client.post(
        "/api/v1/auth/password-reset/confirm",
        json={"token": reset_token, "password": "new-password-1"},
    )
    assert confirm.status_code == 204
    stale = await client.get("/api/v1/me", headers={"Authorization": f"Bearer {old_token}"})
    assert_error(stale, 401, "unauthenticated")
    fresh = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "new-password-1"},
    )
    assert fresh.status_code == 200, fresh.text


@pytest.mark.asyncio
async def test_optional_totp_is_required_after_confirm(client: AsyncClient) -> None:
    import pyotp

    email = unique_email("totp")
    await register(client, email)
    token = await login(client, email)
    enabled = await client.post("/api/v1/auth/totp/enable", headers={"Authorization": f"Bearer {token}"})
    assert enabled.status_code == 200, enabled.text
    secret = enabled.json()["secret"]
    confirm = await client.post(
        "/api/v1/auth/totp/confirm",
        headers={"Authorization": f"Bearer {token}"},
        json={"code": pyotp.TOTP(secret).now()},
    )
    assert confirm.status_code == 204, confirm.text
    missing = await client.post("/api/v1/auth/login", json={"email": email, "password": "password123"})
    assert_error(missing, 401, "totp_required")
    ok = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "password123", "totp_code": pyotp.TOTP(secret).now()},
    )
    assert ok.status_code == 200, ok.text


@pytest.mark.asyncio
async def test_refresh_without_csrf_is_denied(client: AsyncClient) -> None:
    email = unique_email("csrf")
    await register(client, email)
    await client.post("/api/v1/auth/login", json={"email": email, "password": "password123"})
    denied = await client.post("/api/v1/auth/refresh")
    assert_error(denied, 403, "csrf_denied")
