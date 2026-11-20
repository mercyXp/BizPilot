from uuid import UUID

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.ops_schemas import (
    ComponentIn,
    ComponentOut,
    EmployeeIn,
    EmployeeOut,
    LeaveDecisionIn,
    LeaveIn,
    LeaveOut,
    PayrollPeriodIn,
    PayrollPeriodOut,
    PayrollRunIn,
    PayrollRunOut,
)
from app.core.context import TenantContext
from app.core.db import get_db
from app.modules.audit.service import require_idempotency_key
from app.modules.authorization.deps import require_permission
from app.modules.payroll.service import (
    create_component,
    create_employee,
    create_leave,
    create_period,
    decide_leave,
    list_employees,
    process_run,
    run_items,
)

router = APIRouter(tags=["payroll"])


@router.post("/employees", response_model=EmployeeOut, status_code=201)
async def employee(
    body: EmployeeIn,
    ctx: TenantContext = Depends(require_permission("employees.manage")),
    session: AsyncSession = Depends(get_db),
) -> EmployeeOut:
    row = await create_employee(
        session,
        ctx,
        full_name=body.full_name,
        hire_on=body.hire_on,
        job_title=body.job_title,
        department_id=body.department_id,
        base_salary=body.base_salary,
        employee_number=body.employee_number,
    )
    return EmployeeOut(
        id=row.id,
        employee_number=row.employee_number,
        full_name=row.full_name,
        status=row.status,
        base_salary=float(row.base_salary),
    )


@router.get("/employees", response_model=list[EmployeeOut])
async def employees(
    ctx: TenantContext = Depends(require_permission("employees.manage")),
    session: AsyncSession = Depends(get_db),
) -> list[EmployeeOut]:
    return [
        EmployeeOut(
            id=row.id,
            employee_number=row.employee_number,
            full_name=row.full_name,
            status=row.status,
            base_salary=float(row.base_salary),
        )
        for row in await list_employees(session, ctx)
    ]


@router.post("/leave-requests", response_model=LeaveOut, status_code=201)
async def leave(
    body: LeaveIn,
    ctx: TenantContext = Depends(require_permission("employees.manage")),
    session: AsyncSession = Depends(get_db),
) -> LeaveOut:
    row = await create_leave(
        session,
        ctx,
        employee_id=body.employee_id,
        type=body.type,
        starts_on=body.starts_on,
        ends_on=body.ends_on,
    )
    return LeaveOut(id=row.id, employee_id=row.employee_id, status=row.status, type=row.type)


@router.post("/leave-requests/{leave_id}/decision", response_model=LeaveOut)
async def leave_decision(
    leave_id: UUID,
    body: LeaveDecisionIn,
    ctx: TenantContext = Depends(require_permission("employees.manage")),
    session: AsyncSession = Depends(get_db),
) -> LeaveOut:
    row = await decide_leave(session, ctx, leave_id, body.status)
    return LeaveOut(id=row.id, employee_id=row.employee_id, status=row.status, type=row.type)


@router.post("/payroll-components", response_model=ComponentOut, status_code=201)
async def component(
    body: ComponentIn,
    ctx: TenantContext = Depends(require_permission("payroll.process")),
    session: AsyncSession = Depends(get_db),
) -> ComponentOut:
    row = await create_component(
        session,
        ctx,
        code=body.code,
        name=body.name,
        kind=body.kind,
        calculation=body.calculation,
        effective_from=body.effective_from,
        effective_to=body.effective_to,
    )
    return ComponentOut(
        id=row.id, code=row.code, name=row.name, kind=row.kind, calculation=row.calculation
    )


@router.post("/payroll-periods", response_model=PayrollPeriodOut, status_code=201)
async def period(
    body: PayrollPeriodIn,
    ctx: TenantContext = Depends(require_permission("payroll.process")),
    session: AsyncSession = Depends(get_db),
) -> PayrollPeriodOut:
    row = await create_period(session, ctx, body.starts_on, body.ends_on)
    return PayrollPeriodOut(
        id=row.id, starts_on=row.starts_on, ends_on=row.ends_on, status=row.status
    )


@router.post("/payroll-runs", response_model=PayrollRunOut, status_code=201)
async def run(
    body: PayrollRunIn,
    request: Request,
    ctx: TenantContext = Depends(require_permission("payroll.process")),
    session: AsyncSession = Depends(get_db),
) -> PayrollRunOut:
    key = require_idempotency_key(request)
    row = await process_run(session, ctx, period_id=body.period_id, idempotency_key=key)
    return PayrollRunOut(id=row.id, period_id=row.period_id, status=row.status)


@router.get("/payroll-runs/{run_id}")
async def run_detail(
    run_id: UUID,
    ctx: TenantContext = Depends(require_permission("payroll.view")),
    session: AsyncSession = Depends(get_db),
) -> dict:
    items = await run_items(session, run_id)
    return {
        "id": str(run_id),
        "items": [
            {
                "employee_id": str(row.employee_id),
                "component_id": str(row.component_id),
                "amount": float(row.amount),
            }
            for row in items
        ],
    }
