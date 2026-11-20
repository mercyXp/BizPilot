import json
import uuid

from httpx import AsyncClient


def unique_email(prefix: str = "user") -> str:
    return f"{prefix}.{uuid.uuid4().hex[:10]}@example.com"


async def register_user(client: AsyncClient, email: str, password: str = "correct-horse-1") -> dict:
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "full_name": "Test User"},
    )
    assert response.status_code == 201, response.text
    return response.json()


async def latest_email_token(email: str, template: str) -> str:
    from sqlalchemy import select

    from app.core.db import SessionLocal
    from app.models.email import OutboundEmail

    async with SessionLocal() as session:
        row = await session.scalar(
            select(OutboundEmail)
            .where(OutboundEmail.to_email == email.lower(), OutboundEmail.template == template)
            .order_by(OutboundEmail.created_at.desc())
        )
    assert row is not None
    payload = json.loads(row.payload_json)
    return payload["token"]


async def verify_user(client: AsyncClient, email: str) -> None:
    token = await latest_email_token(email, "email_verify")
    response = await client.post("/api/v1/auth/verify-email", json={"token": token})
    assert response.status_code == 200, response.text


async def login_user(client: AsyncClient, email: str, password: str = "correct-horse-1") -> dict:
    response = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200, response.text
    return response.json()


def auth_headers(login_body: dict, organization_id: str | None = None) -> dict[str, str]:
    headers = {
        "Authorization": f"Bearer {login_body['access_token']}",
        "X-CSRF-Token": login_body["csrf_token"],
    }
    if organization_id:
        headers["X-Organization-Id"] = organization_id
    return headers
