from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.core.ids import new_uuid
from app.modules.i18n.catalog import MESSAGES
from app.modules.i18n.models import TranslationResource
from app.modules.tenancy.models import OrganizationLocale


async def list_messages(session: AsyncSession, locale: str) -> dict:
    rows = list(
        await session.scalars(
            select(TranslationResource).where(TranslationResource.locale == locale).order_by(
                TranslationResource.key
            )
        )
    )
    fallback = []
    if locale != "en":
        fallback = list(
            await session.scalars(
                select(TranslationResource).where(TranslationResource.locale == "en")
            )
        )
    messages: dict[str, dict] = {}
    if not rows and not fallback:
        for catalog_locale, key, value in MESSAGES:
            if catalog_locale in {locale, "en"} and (
                catalog_locale == locale or key not in messages
            ):
                messages[key] = {"value": value, "provenance": "system", "locale": catalog_locale}
    for row in fallback:
        messages[row.key] = {"value": row.value, "provenance": row.provenance, "locale": "en"}
    for row in rows:
        messages[row.key] = {"value": row.value, "provenance": row.provenance, "locale": row.locale}
    return {
        "locale": locale,
        "messages": {key: item["value"] for key, item in messages.items()},
        "provenance": {key: item["provenance"] for key, item in messages.items()},
        "professional_keys": [key for key, item in messages.items() if item["provenance"] == "professional"],
    }


async def upsert_message(
    session: AsyncSession,
    *,
    locale: str,
    key: str,
    value: str,
    provenance: str,
) -> TranslationResource:
    if provenance not in {"system", "professional"}:
        raise AppError(422, "provenance must be system or professional", code="validation_error")
    row = await session.scalar(
        select(TranslationResource).where(
            TranslationResource.locale == locale, TranslationResource.key == key
        )
    )
    if row is None:
        row = TranslationResource(
            id=new_uuid(), locale=locale, key=key, value=value, provenance=provenance
        )
        session.add(row)
        await session.flush()
        return row
    if row.provenance == "professional" and provenance != "professional":
        raise AppError(409, "Professional translation is locked", code="conflict")
    row.value = value
    row.provenance = provenance
    await session.flush()
    return row


async def seed_system_messages(session: AsyncSession) -> None:
    for locale, key, value in MESSAGES:
        existing = await session.scalar(
            select(TranslationResource).where(
                TranslationResource.locale == locale, TranslationResource.key == key
            )
        )
        if existing is None:
            session.add(
                TranslationResource(locale=locale, key=key, value=value, provenance="system")
            )
        elif existing.provenance != "professional":
            existing.value = value
    await session.flush()


async def get_locale(session: AsyncSession, organization_id) -> OrganizationLocale | None:
    return await session.scalar(
        select(OrganizationLocale).where(OrganizationLocale.organization_id == organization_id)
    )


async def set_locale(
    session: AsyncSession, organization_id, *, default_locale: str, enabled_locales: list[str]
) -> OrganizationLocale:
    row = await get_locale(session, organization_id)
    enabled = enabled_locales or [default_locale]
    if default_locale not in enabled:
        enabled = [default_locale, *enabled]
    if row is None:
        row = OrganizationLocale(
            organization_id=organization_id,
            default_locale=default_locale,
            enabled_locales=enabled,
        )
        session.add(row)
    else:
        row.default_locale = default_locale
        row.enabled_locales = enabled
    await session.flush()
    return row
