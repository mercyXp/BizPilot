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


@pytest.mark.asyncio
async def test_register_login_and_me(client: AsyncClient) -> None:
    email = unique_email("reg")
    await register_user(client, email)
    body = await login_user(client, email)
    me = await client.get("/api/v1/auth/me", headers=auth_headers(body))
    assert me.status_code == 200
    data = me.json()
    assert data["email"] == email
    assert data["email_verified"] is False


@pytest.mark.asyncio
async def test_login_rejects_wrong_password(client: AsyncClient) -> None:
    email = unique_email("badpw")
    await register_user(client, email)
    response = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": "wrong-password"}
    )
    assert response.status_code == 401
    assert "Traceback" not in response.text


@pytest.mark.asyncio
async def test_email_verification(client: AsyncClient) -> None:
    email = unique_email("verify")
    await register_user(client, email)
    await verify_user(client, email)
    body = await login_user(client, email)
    me = await client.get("/api/v1/auth/me", headers=auth_headers(body))
    assert me.json()["email_verified"] is True


@pytest.mark.asyncio
async def test_refresh_rotation_and_reuse_revokes_family(client: AsyncClient) -> None:
    email = unique_email("refresh")
    await register_user(client, email)
    first = await login_user(client, email)
    old_cookie = client.cookies.get("bp_refresh")
    assert old_cookie

    refresh = await client.post(
        "/api/v1/auth/refresh",
        headers={"X-CSRF-Token": first["csrf_token"]},
    )
    assert refresh.status_code == 200
    new_cookie = client.cookies.get("bp_refresh")
    assert new_cookie
    assert new_cookie != old_cookie

    client.cookies.set("bp_refresh", old_cookie, path="/api/v1/auth")
    reused = await client.post(
        "/api/v1/auth/refresh",
        headers={"X-CSRF-Token": first["csrf_token"]},
    )
    assert reused.status_code == 401


@pytest.mark.asyncio
async def test_password_reset_revokes_sessions(client: AsyncClient) -> None:
    email = unique_email("reset")
    password = "correct-horse-1"
    await register_user(client, email, password)
    body = await login_user(client, email, password)

    forgot = await client.post("/api/v1/auth/forgot-password", json={"email": email})
    assert forgot.status_code == 200
    token = await latest_email_token(email, "password_reset")
    reset = await client.post(
        "/api/v1/auth/reset-password",
        json={"token": token, "password": "new-password-9"},
    )
    assert reset.status_code == 200

    me = await client.get("/api/v1/auth/me", headers=auth_headers(body))
    assert me.status_code == 401

    old_login = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": password}
    )
    assert old_login.status_code == 401
    new_login = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": "new-password-9"}
    )
    assert new_login.status_code == 200


@pytest.mark.asyncio
async def test_logout(client: AsyncClient) -> None:
    email = unique_email("logout")
    await register_user(client, email)
    body = await login_user(client, email)
    response = await client.post("/api/v1/auth/logout", headers=auth_headers(body))
    assert response.status_code == 204
    me = await client.get("/api/v1/auth/me", headers=auth_headers(body))
    assert me.status_code == 401
