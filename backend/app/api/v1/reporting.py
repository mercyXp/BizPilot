from datetime import date

from fastapi import APIRouter, Depends, Query
from fastapi.responses import PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.errors import AppError
from app.core.tenancy import TenantContext
from app.modules.authorization.deps import require_permission
from app.modules.reporting.service import KINDS, csv_from_report, run_report, summary

router = APIRouter(prefix="/reporting", tags=["reporting"])


@router.get("/summary")
async def reporting_summary(
    ctx: TenantContext = Depends(require_permission("reports.view")),
    session: AsyncSession = Depends(get_db),
) -> dict:
    return await summary(session, ctx)


@router.get("/{kind}")
async def reporting_kind(
    kind: str,
    from_date: date | None = Query(default=None),
    to_date: date | None = Query(default=None),
    export: str | None = Query(default=None),
    ctx: TenantContext = Depends(require_permission("reports.view")),
    session: AsyncSession = Depends(get_db),
):
    if kind not in KINDS:
        raise AppError(404, "Unknown report", code="not_found")
    payload = await run_report(session, ctx, kind, from_date=from_date, to_date=to_date)
    if export == "csv":
        return PlainTextResponse(
            csv_from_report(payload),
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{kind}.csv"'},
        )
    return payload
