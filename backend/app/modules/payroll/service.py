from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import TenantContext
from app.core.errors import AppError
from app.core.money import ZERO, money
from app.modules.accounting.posting import post_payroll_run
from app.modules.audit.service import get_idempotent, request_hash, store_idempotent, write_audit
from app.modules.inventory.service import next_document_number
from app.modules.payroll.models import (
    Department,
    Employee,
    LeaveRequest,
    PayrollComponent,
    PayrollItem,
    PayrollPeriod,
    PayrollRun,
)


def _assert_not_official(calculation: dict, name: str) -> None:
    blob = f"{name} {calculation}".lower()
    if calculation.get("official") is True or "official zambia" in blob or "zambia statutory" in blob:
        raise AppError(
            422,
            "Statutory rates must stay configurable and cannot be labelled official",
            code="validation_error",
        )


async def create_department(session: AsyncSession, ctx: TenantContext, name: str) -> Department:
    row = Department(organization_id=ctx.organization_id, name=name.strip())
    session.add(row)
    await session.flush()
    return row


async def create_employee(
    session: AsyncSession,
    ctx: TenantContext,
    *,
    full_name: str,
    hire_on: date,
    job_title: str | None,
    department_id: UUID | None,
    base_salary: Decimal,
    employee_number: str | None,
) -> Employee:
    number = employee_number or await next_document_number(
        session, ctx, document_type="employee", prefix="EMP"
    )
    row = Employee(
        organization_id=ctx.organization_id,
        branch_id=ctx.branch_id,
        employee_number=number,
        full_name=full_name.strip(),
        hire_on=hire_on,
        status="active",
        department_id=department_id,
        job_title=job_title,
        base_salary=money(base_salary),
    )
    session.add(row)
    try:
        await session.flush()
    except IntegrityError as exc:
        raise AppError(409, "Employee number already exists", code="conflict") from exc
    return row


async def list_employees(session: AsyncSession, ctx: TenantContext) -> list[Employee]:
    rows = await session.scalars(
        select(Employee).where(Employee.organization_id == ctx.organization_id).order_by(Employee.employee_number)
    )
    return list(rows)


async def create_leave(
    session: AsyncSession,
    ctx: TenantContext,
    *,
    employee_id: UUID,
    type: str,
    starts_on: date,
    ends_on: date,
) -> LeaveRequest:
    employee = await session.get(Employee, employee_id)
    if employee is None:
        raise AppError(404, "Employee not found", code="not_found")
    row = LeaveRequest(
        organization_id=ctx.organization_id,
        employee_id=employee.id,
        type=type,
        starts_on=starts_on,
        ends_on=ends_on,
        status="pending",
    )
    session.add(row)
    await session.flush()
    return row


async def decide_leave(
    session: AsyncSession, ctx: TenantContext, leave_id: UUID, status: str
) -> LeaveRequest:
    row = await session.get(LeaveRequest, leave_id)
    if row is None:
        raise AppError(404, "Leave request not found", code="not_found")
    if status not in {"approved", "rejected"}:
        raise AppError(422, "Leave decision must be approved or rejected", code="validation_error")
    row.status = status
    await session.flush()
    return row


async def create_component(
    session: AsyncSession,
    ctx: TenantContext,
    *,
    code: str,
    name: str,
    kind: str,
    calculation: dict,
    effective_from: date | None,
    effective_to: date | None,
) -> PayrollComponent:
    _assert_not_official(calculation, name)
    row = PayrollComponent(
        organization_id=ctx.organization_id,
        code=code.strip().upper(),
        name=name.strip(),
        kind=kind,
        calculation=calculation,
        effective_from=effective_from,
        effective_to=effective_to,
    )
    session.add(row)
    try:
        await session.flush()
    except IntegrityError as exc:
        raise AppError(409, "Component code already exists", code="conflict") from exc
    return row


async def create_period(
    session: AsyncSession, ctx: TenantContext, starts_on: date, ends_on: date
) -> PayrollPeriod:
    row = PayrollPeriod(
        organization_id=ctx.organization_id,
        starts_on=starts_on,
        ends_on=ends_on,
        status="open",
    )
    session.add(row)
    await session.flush()
    return row


def calculate_component(component: PayrollComponent, base: Decimal, on: date) -> Decimal:
    if component.effective_from and on < component.effective_from:
        return ZERO
    if component.effective_to and on > component.effective_to:
        return ZERO
    calc = component.calculation if isinstance(component.calculation, dict) else {}
    kind = calc.get("type")
    if kind == "fixed":
        return money(calc.get("amount") or 0)
    if kind == "percent_of_base":
        return money(base * Decimal(str(calc.get("rate") or 0)))
    if kind == "percent_of_gross":
        return money(base * Decimal(str(calc.get("rate") or 0)))
    raise AppError(422, f"Unknown payroll calculation for {component.code}", code="validation_error")


async def process_run(
    session: AsyncSession,
    ctx: TenantContext,
    *,
    period_id: UUID,
    idempotency_key: str,
) -> PayrollRun:
    digest = request_hash({"period_id": str(period_id)})
    cached = await get_idempotent(session, ctx, idempotency_key, digest)
    if cached:
        existing = await session.get(PayrollRun, UUID(cached["id"]))
        if existing is not None:
            return existing
    existing_key = await session.scalar(
        select(PayrollRun).where(
            PayrollRun.organization_id == ctx.organization_id,
            PayrollRun.idempotency_key == idempotency_key,
        )
    )
    if existing_key is not None:
        return existing_key
    period = await session.get(PayrollPeriod, period_id)
    if period is None or period.status != "open":
        raise AppError(409, "Payroll period is not open", code="conflict")
    run = PayrollRun(
        organization_id=ctx.organization_id,
        period_id=period.id,
        status="processed",
        processed_at=datetime.now(UTC),
        idempotency_key=idempotency_key,
    )
    session.add(run)
    await session.flush()
    employees = await list_employees(session, ctx)
    components = list(
        await session.scalars(
            select(PayrollComponent).where(PayrollComponent.organization_id == ctx.organization_id)
        )
    )
    posted_items: list[tuple[str, str, Decimal]] = []
    on = period.ends_on
    for employee in employees:
        if employee.status != "active":
            continue
        gross = employee.base_salary
        posted_items.append(("earning", "BASE", employee.base_salary))
        for component in components:
            if component.code == "BASE":
                continue
            amount = calculate_component(component, employee.base_salary, on)
            if component.kind != "earning" and component.calculation.get("type") == "percent_of_gross":
                amount = calculate_component(component, gross, on)
            if component.kind == "earning":
                gross += amount
            session.add(
                PayrollItem(
                    organization_id=ctx.organization_id,
                    run_id=run.id,
                    employee_id=employee.id,
                    component_id=component.id,
                    amount=amount,
                )
            )
            posted_items.append((component.kind, component.code, amount))
    await post_payroll_run(session, ctx, run_id=run.id, items=posted_items)
    period.status = "closed"
    await session.flush()
    await store_idempotent(
        session, ctx, idempotency_key, digest, {"id": str(run.id), "status": run.status}
    )
    await write_audit(session, ctx, action="payroll.process", entity_type="payroll_run", entity_id=run.id)
    return run


async def run_items(session: AsyncSession, run_id: UUID) -> list[PayrollItem]:
    return list(await session.scalars(select(PayrollItem).where(PayrollItem.run_id == run_id)))
