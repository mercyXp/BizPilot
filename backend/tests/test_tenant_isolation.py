import pytest
from httpx import AsyncClient
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import get_settings
from tests.helpers import (
    assert_error,
    create_branch,
    create_organization,
    login,
    register,
    tenant_headers,
    unique_email,
)


@pytest.mark.asyncio
async def test_cross_tenant_requests_fail_closed(client: AsyncClient) -> None:
    email_a = unique_email("org-a")
    email_b = unique_email("org-b")
    await register(client, email_a, "User A")
    await register(client, email_b, "User B")
    token_a = await login(client, email_a)
    token_b = await login(client, email_b)
    org_a = await create_organization(client, token_a, "Org A")
    org_b = await create_organization(client, token_b, "Org B")
    branch_a = await create_branch(client, token_a, org_a["id"], "A", "A")
    branch_b = await create_branch(client, token_b, org_b["id"], "B", "B")

    listing = await client.get("/api/v1/organizations", headers={"Authorization": f"Bearer {token_a}"})
    assert listing.status_code == 200, listing.text
    assert {row["id"] for row in listing.json()} == {org_a["id"]}

    foreign_org = await client.get(
        "/api/v1/branches",
        headers=tenant_headers(token_a, org_b["id"]),
    )
    assert_error(foreign_org, 403, "permission_denied")

    swapped = await client.get(
        f"/api/v1/branches/{branch_b['id']}",
        headers=tenant_headers(token_a, org_a["id"]),
    )
    assert_error(swapped, 404, "not_found")

    own = await client.get(
        f"/api/v1/branches/{branch_a['id']}",
        headers=tenant_headers(token_a, org_a["id"]),
    )
    assert own.status_code == 200, own.text

    switched = await client.get(
        "/api/v1/branches",
        headers=tenant_headers(token_b, org_b["id"]),
    )
    assert [row["id"] for row in switched.json()] == [branch_b["id"]]


@pytest.mark.asyncio
async def test_app_role_cannot_read_tenant_rows_without_context(client: AsyncClient) -> None:
    email = unique_email("rls")
    user = await register(client, email, "RLS User")
    token = await login(client, email)
    org = await create_organization(client, token, "RLS Shop")
    branch = await create_branch(client, token, org["id"], "MAIN", "Main")

    settings = get_settings()
    superuser = create_engine(settings.database_url_sync)
    with superuser.connect() as connection:
        visible = connection.execute(
            text("SELECT count(*) FROM branches WHERE id = CAST(:branch_id AS uuid)"),
            {"branch_id": branch["id"]},
        ).scalar_one()
    superuser.dispose()
    assert visible == 1

    app_engine = create_async_engine(settings.database_url)
    async with app_engine.connect() as connection:
        hidden = (
            await connection.execute(text("SELECT count(*) FROM branches"))
        ).scalar_one()
    assert hidden == 0

    async with app_engine.connect() as connection:
        await connection.execute(
            text("SELECT set_config('app.current_user_id', :user_id, true)"),
            {"user_id": user["id"]},
        )
        await connection.execute(
            text("SELECT set_config('app.current_organization_id', :org_id, true)"),
            {"org_id": org["id"]},
        )
        visible_to_member = (
            await connection.execute(
                text("SELECT count(*) FROM branches WHERE id = CAST(:branch_id AS uuid)"),
                {"branch_id": branch["id"]},
            )
        ).scalar_one()
        await connection.rollback()
    assert visible_to_member == 1

    other_email = unique_email("rls-other")
    other = await register(client, other_email, "Other")
    other_token = await login(client, other_email)
    other_org = await create_organization(client, other_token, "Other Shop")
    await create_branch(client, other_token, other_org["id"], "OTHER", "Other")

    async with app_engine.connect() as connection:
        await connection.execute(
            text("SELECT set_config('app.current_user_id', :user_id, true)"),
            {"user_id": user["id"]},
        )
        await connection.execute(
            text("SELECT set_config('app.current_organization_id', :org_id, true)"),
            {"org_id": other_org["id"]},
        )
        leaked = (await connection.execute(text("SELECT count(*) FROM branches"))).scalar_one()
        await connection.rollback()
    await app_engine.dispose()
    assert leaked == 0
    assert other["id"] != user["id"]
