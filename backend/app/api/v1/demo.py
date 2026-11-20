from fastapi import APIRouter, Depends, Request, Response
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth import _token_response
from app.api.v1.deps import get_current_user
from app.core.config import Settings, get_settings
from app.core.context import TenantContext
from app.core.db import get_db
from app.core.errors import AppError
from app.core.rate_limit import allow_attempt
from app.models.user import User
from app.modules.authorization.deps import get_tenant_context, require_permission
from app.modules.demo import service as demo

router = APIRouter(prefix="/demo", tags=["demo"])


class EnterIn(BaseModel):
    role: str = Field(min_length=2, max_length=32)


class EventIn(BaseModel):
    module: str = Field(min_length=1, max_length=64)
    action: str = Field(default="view", max_length=32)
    role: str | None = None


class AskIn(BaseModel):
    question: str = Field(min_length=3, max_length=500)


def _client_ip(request: Request) -> str | None:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else None


@router.get("/roles")
async def roles(settings: Settings = Depends(get_settings)) -> dict:
    demo.assert_demo_enabled(settings)
    return {
        "business": {
            "name": "Mwamba Retail Group",
            "tagline": "Retail and wholesale · Lusaka, Zambia",
            "currency": "ZMW",
        },
        "roles": demo.public_roles(),
    }


@router.post("/enter")
async def enter(
    payload: EnterIn,
    request: Request,
    response: Response,
    session: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> dict:
    key = f"demo-enter:{_client_ip(request)}"
    if not await allow_attempt(key, 20, 60):
        raise AppError(429, "Too many demo attempts. Try again shortly.", code="rate_limited")
    user, access, refresh, csrf, snapshot = await demo.enter_role(
        session,
        settings,
        role_key=payload.role,
        user_agent=request.headers.get("user-agent"),
        ip=_client_ip(request),
    )
    tokens = _token_response(response, settings, user, access, refresh, csrf)
    return {**tokens.model_dump(mode="json"), "demo": snapshot}


@router.post("/switch")
async def switch(
    payload: EnterIn,
    request: Request,
    response: Response,
    session: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
    current: User = Depends(get_current_user),
) -> dict:
    user, access, refresh, csrf, snapshot = await demo.switch_role(
        session,
        settings,
        current=current,
        role_key=payload.role,
        user_agent=request.headers.get("user-agent"),
        ip=_client_ip(request),
    )
    tokens = _token_response(response, settings, user, access, refresh, csrf)
    return {**tokens.model_dump(mode="json"), "demo": snapshot}


@router.post("/reset")
async def reset(
    payload: EnterIn,
    request: Request,
    response: Response,
    session: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
    current: User = Depends(get_current_user),
) -> dict:
    user, access, refresh, csrf, snapshot = await demo.reset_demo(
        session,
        settings,
        current=current,
        role_key=payload.role,
        user_agent=request.headers.get("user-agent"),
        ip=_client_ip(request),
    )
    tokens = _token_response(response, settings, user, access, refresh, csrf)
    return {**tokens.model_dump(mode="json"), "demo": snapshot}


@router.post("/events")
async def events(
    payload: EventIn,
    session: AsyncSession = Depends(get_db),
    ctx: TenantContext = Depends(get_tenant_context),
) -> dict:
    await demo.require_demo_org(session, ctx)
    await demo.track_event(
        session,
        ctx.organization_id,
        ctx.user_id,
        role=payload.role,
        module=payload.module,
        action=payload.action,
    )
    return {"ok": True}


@router.get("/snapshot")
async def snapshot(
    session: AsyncSession = Depends(get_db),
    ctx: TenantContext = Depends(get_tenant_context),
    user: User = Depends(get_current_user),
) -> dict:
    await demo.require_demo_org(session, ctx)
    return await demo.snapshot_for(session, ctx.organization_id, user_id=user.id, email=user.email)


@router.get("/catalog")
async def catalog(
    session: AsyncSession = Depends(get_db),
    ctx: TenantContext = Depends(require_permission("catalogue.view")),
) -> dict:
    return {"items": await demo.catalog(session, ctx)}


@router.get("/audit")
async def audit(
    session: AsyncSession = Depends(get_db),
    ctx: TenantContext = Depends(get_tenant_context),
) -> dict:
    if "accounting.reports.view" not in ctx.permissions and "reports.view" not in ctx.permissions:
        raise AppError(403, "Missing permission reports.view", code="permission_denied")
    return {"items": await demo.list_audit(session, ctx)}


@router.get("/expenses")
async def expenses(
    session: AsyncSession = Depends(get_db),
    ctx: TenantContext = Depends(get_tenant_context),
) -> dict:
    if "expenses.create" not in ctx.permissions and "accounting.reports.view" not in ctx.permissions:
        raise AppError(403, "Missing permission expenses.create", code="permission_denied")
    return {"items": await demo.list_expenses(session, ctx)}


@router.post("/ask")
async def ask(
    payload: AskIn,
    session: AsyncSession = Depends(get_db),
    ctx: TenantContext = Depends(require_permission("ai.use")),
) -> dict:
    await demo.require_demo_org(session, ctx)
    return {"answer": await demo.answer_question(session, ctx, payload.question)}
