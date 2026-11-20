from datetime import date

import pytest
from httpx import AsyncClient

from tests.helpers import onboard_shop


@pytest.mark.asyncio
async def test_payroll_run_is_auditable_and_journals_balance(client: AsyncClient) -> None:
    shop = await onboard_shop(client, "Pay Shop")
    employee = await client.post(
        "/api/v1/employees",
        headers=shop["headers"],
        json={
            "full_name": "Grace Banda",
            "hire_on": date.today().isoformat(),
            "job_title": "Cashier",
            "base_salary": 1000,
        },
    )
    assert employee.status_code == 201, employee.text
    component = await client.post(
        "/api/v1/payroll-components",
        headers=shop["headers"],
        json={
            "code": "DEV_TAX",
            "name": "DEV_ONLY placeholder deduction",
            "kind": "deduction",
            "calculation": {"type": "percent_of_base", "rate": "0.05", "official": False},
        },
    )
    assert component.status_code == 201, component.text
    assert "official zambia" not in str(component.json()).lower()
    period = await client.post(
        "/api/v1/payroll-periods",
        headers=shop["headers"],
        json={"starts_on": date.today().replace(day=1).isoformat(), "ends_on": date.today().isoformat()},
    )
    assert period.status_code == 201, period.text
    run = await client.post(
        "/api/v1/payroll-runs",
        headers={**shop["headers"], "Idempotency-Key": "pay-1"},
        json={"period_id": period.json()["id"]},
    )
    assert run.status_code == 201, run.text
    detail = await client.get(f"/api/v1/payroll-runs/{run.json()['id']}", headers=shop["headers"])
    assert detail.status_code == 200, detail.text
    amounts = [item["amount"] for item in detail.json()["items"]]
    assert 50 in amounts
    journals = await client.get("/api/v1/journals", headers=shop["headers"])
    payroll = next(row for row in journals.json() if row["source_type"] == "payroll_run")
    lines = await client.get(f"/api/v1/journals/{payroll['id']}", headers=shop["headers"])
    debit = sum(line["debit"] for line in lines.json()["lines"])
    credit = sum(line["credit"] for line in lines.json()["lines"])
    assert debit == credit
    again = await client.post(
        "/api/v1/payroll-runs",
        headers={**shop["headers"], "Idempotency-Key": "pay-1"},
        json={"period_id": period.json()["id"]},
    )
    assert again.json()["id"] == run.json()["id"]
    denied = await client.post(
        "/api/v1/payroll-components",
        headers=shop["headers"],
        json={
            "code": "PAYE",
            "name": "Official Zambia statutory PAYE",
            "kind": "deduction",
            "calculation": {"type": "percent_of_base", "rate": "0.25", "official": True},
        },
    )
    assert denied.status_code == 422, denied.text
