from datetime import date

import pytest
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import get_settings
from tests.helpers import onboard_shop


@pytest.mark.asyncio
async def test_balanced_post_immutability_reversal_and_closed_period(client: AsyncClient) -> None:
    shop = await onboard_shop(client, "Books Shop")
    accounts = await client.get("/api/v1/accounts", headers=shop["headers"])
    assert accounts.status_code == 200, accounts.text
    by_code = {row["code"]: row["id"] for row in accounts.json()}
    posted = await client.post(
        "/api/v1/journals",
        headers={**shop["headers"], "Idempotency-Key": "je-1"},
        json={
            "description": "Open cash",
            "lines": [
                {"account_id": by_code["1000"], "debit": 50},
                {"account_id": by_code["3000"], "credit": 50},
            ],
        },
    )
    assert posted.status_code == 201, posted.text
    journal_id = posted.json()["id"]
    detail = await client.get(f"/api/v1/journals/{journal_id}", headers=shop["headers"])
    assert detail.status_code == 200, detail.text
    debit = sum(line["debit"] for line in detail.json()["lines"])
    credit = sum(line["credit"] for line in detail.json()["lines"])
    assert debit == credit

    settings = get_settings()
    engine = create_async_engine(settings.database_url)
    async with engine.connect() as connection:
        await connection.execute(
            text("SELECT set_config('app.current_user_id', :user, true)"),
            {"user": "00000000-0000-0000-0000-000000000001"},
        )
        try:
            await connection.execute(
                text("UPDATE journal_entries SET description = 'hack' WHERE id = CAST(:id AS uuid)"),
                {"id": journal_id},
            )
            raise AssertionError("posted journal update should have been rejected")
        except Exception as exc:
            assert "immutable" in str(exc) or "journal" in str(exc)
        await connection.rollback()
    await engine.dispose()

    reversed_row = await client.post(
        f"/api/v1/journals/{journal_id}/reverse",
        headers={**shop["headers"], "Idempotency-Key": "je-rev"},
    )
    assert reversed_row.status_code == 200, reversed_row.text
    original = await client.get(f"/api/v1/journals/{journal_id}", headers=shop["headers"])
    assert original.json()["status"] == "reversed"

    periods = await client.get("/api/v1/periods", headers=shop["headers"])
    today = date.today().isoformat()
    current = next(
        row
        for row in periods.json()
        if row["starts_on"] <= today <= row["ends_on"]
    )
    closed = await client.post(
        f"/api/v1/periods/{current['id']}/close",
        headers=shop["headers"],
    )
    assert closed.status_code == 200, closed.text
    rejected = await client.post(
        "/api/v1/journals",
        headers={**shop["headers"], "Idempotency-Key": "je-closed"},
        json={
            "description": "After close",
            "lines": [
                {"account_id": by_code["1000"], "debit": 10},
                {"account_id": by_code["3000"], "credit": 10},
            ],
        },
    )
    assert rejected.status_code == 409, rejected.text
    assert rejected.json()["error"]["code"] == "conflict"


@pytest.mark.asyncio
async def test_sale_posts_and_reports_reconcile(client: AsyncClient) -> None:
    shop = await onboard_shop(client, "Report Shop")
    opened = await client.post(
        "/api/v1/pos/sessions",
        headers=shop["headers"],
        json={"warehouse_id": shop["warehouse_id"], "opening_float": 0},
    )
    sale = await client.post(
        f"/api/v1/pos/sessions/{opened.json()['id']}/sales",
        headers={**shop["headers"], "Idempotency-Key": "rep-sale"},
        json={
            "items": [{"variant_id": shop["variant_id"], "qty": 2}],
            "payments": [{"method": "cash", "amount": 20}],
        },
    )
    assert sale.status_code == 201, sale.text
    tb = await client.get("/api/v1/reports/trial-balance", headers=shop["headers"])
    assert tb.status_code == 200, tb.text
    debit = sum(row["debit"] for row in tb.json())
    credit = sum(row["credit"] for row in tb.json())
    assert round(debit, 4) == round(credit, 4)
    pnl = await client.get("/api/v1/reports/profit-and-loss", headers=shop["headers"])
    assert pnl.status_code == 200, pnl.text
    assert pnl.json()["income"] > 0
    sheet = await client.get("/api/v1/reports/balance-sheet", headers=shop["headers"])
    assert sheet.status_code == 200, sheet.text
    assert sheet.json()["balanced"] is True
    expense = await client.post(
        "/api/v1/expenses",
        headers=shop["headers"],
        json={
            "vendor_name": "Zesco",
            "amount": 5,
            "incurred_on": date.today().isoformat(),
            "payment_method": "cash",
        },
    )
    assert expense.status_code == 201, expense.text
    posted = await client.post(
        f"/api/v1/expenses/{expense.json()['id']}/approve",
        headers=shop["headers"],
    )
    assert posted.status_code == 200, posted.text
    assert posted.json()["status"] == "posted"
