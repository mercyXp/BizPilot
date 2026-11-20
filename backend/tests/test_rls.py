import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

from app.core.config import get_settings
from app.core.db import SessionLocal
from app.main import app
from tests.helpers import auth_headers, login_user, register_user, unique_email, verify_user


@pytest.mark.asyncio
async def test_app_role_sees_no_tenant_rows_without_rls_settings() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        email = unique_email("rls")
        await register_user(client, email)
        await verify_user(client, email)
        body = await login_user(client, email)
        created = await client.post(
            "/api/v1/organizations",
            headers=auth_headers(body),
            json={"name": "RLS Probe"},
        )
        assert created.status_code == 201, created.text

    settings = get_settings()
    assert "bizpilot_app" in settings.database_url

    async with SessionLocal() as session:
        orgs = (await session.execute(text("SELECT id FROM organizations"))).all()
        memberships = (await session.execute(text("SELECT id FROM organization_memberships"))).all()
        invitations = (await session.execute(text("SELECT id FROM invitations"))).all()

    assert orgs == []
    assert memberships == []
    assert invitations == []
