from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_tenant_context
from app.core.db import get_db
from app.core.tenancy import TenantContext
from app.modules.authorization.deps import require_permission
from app.modules.i18n import service as i18n

router = APIRouter(tags=["i18n"])


class LocaleOut(BaseModel):
    default_locale: str
    enabled_locales: list[str]


class LocaleIn(BaseModel):
    default_locale: str = Field(min_length=2, max_length=16)
    enabled_locales: list[str] = Field(default_factory=list)


class MessageIn(BaseModel):
    locale: str = Field(min_length=2, max_length=16)
    key: str = Field(min_length=1, max_length=200)
    value: str = Field(min_length=1)
    provenance: str = "system"


@router.get("/i18n/messages")
async def messages(
    locale: str = Query(default="en"),
    session: AsyncSession = Depends(get_db),
) -> dict:
    return await i18n.list_messages(session, locale)


@router.put("/i18n/messages")
async def put_message(
    body: MessageIn,
    ctx: TenantContext = Depends(require_permission("org.settings")),
    session: AsyncSession = Depends(get_db),
) -> dict:
    _ = ctx
    row = await i18n.upsert_message(
        session,
        locale=body.locale,
        key=body.key,
        value=body.value,
        provenance=body.provenance,
    )
    return {
        "locale": row.locale,
        "key": row.key,
        "value": row.value,
        "provenance": row.provenance,
    }


@router.get("/organization-locale", response_model=LocaleOut)
async def read_locale(
    ctx: TenantContext = Depends(get_tenant_context),
    session: AsyncSession = Depends(get_db),
) -> LocaleOut:
    row = await i18n.get_locale(session, ctx.organization_id)
    if row is None:
        return LocaleOut(default_locale="en", enabled_locales=["en"])
    return LocaleOut(default_locale=row.default_locale, enabled_locales=list(row.enabled_locales or ["en"]))


@router.put("/organization-locale", response_model=LocaleOut)
async def write_locale(
    body: LocaleIn,
    ctx: TenantContext = Depends(require_permission("org.settings")),
    session: AsyncSession = Depends(get_db),
) -> LocaleOut:
    row = await i18n.set_locale(
        session,
        ctx.organization_id,
        default_locale=body.default_locale,
        enabled_locales=body.enabled_locales,
    )
    return LocaleOut(default_locale=row.default_locale, enabled_locales=list(row.enabled_locales))
