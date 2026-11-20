import pytest
from httpx import AsyncClient

from tests.helpers import onboard_shop


@pytest.mark.asyncio
async def test_english_messages_and_professional_lock(client: AsyncClient) -> None:
    public = await client.get("/api/v1/i18n/messages", params={"locale": "en"})
    assert public.status_code == 200, public.text
    body = public.json()
    assert body["messages"]["reports.title"] == "Reports"
    assert body["provenance"]["reports.title"] == "system"

    shop = await onboard_shop(client, "Locale Shop")
    professional = await client.put(
        "/api/v1/i18n/messages",
        headers=shop["headers"],
        json={
            "locale": "en",
            "key": "test.professional.lock",
            "value": "Locked copy",
            "provenance": "professional",
        },
    )
    assert professional.status_code == 200, professional.text
    locked = await client.put(
        "/api/v1/i18n/messages",
        headers=shop["headers"],
        json={
            "locale": "en",
            "key": "test.professional.lock",
            "value": "System copy",
            "provenance": "system",
        },
    )
    assert locked.status_code == 409, locked.text
    after = await client.get("/api/v1/i18n/messages", params={"locale": "en"})
    assert after.json()["messages"]["test.professional.lock"] == "Locked copy"
    assert after.json()["provenance"]["test.professional.lock"] == "professional"
    assert "test.professional.lock" in after.json()["professional_keys"]


@pytest.mark.asyncio
async def test_org_locale_and_industry_pack_config(client: AsyncClient) -> None:
    shop = await onboard_shop(client, "Pack Shop")
    locale = await client.get("/api/v1/organization-locale", headers=shop["headers"])
    assert locale.status_code == 200, locale.text
    assert locale.json()["default_locale"] == "en"
    saved = await client.put(
        "/api/v1/organization-locale",
        headers=shop["headers"],
        json={"default_locale": "ny", "enabled_locales": ["en", "ny"]},
    )
    assert saved.status_code == 200, saved.text
    assert saved.json()["default_locale"] == "ny"
    packs = await client.get("/api/v1/industries")
    by_code = {row["code"]: row for row in packs.json()}
    pharmacy = by_code["pharmacy"]
    clothing = by_code["clothing"]
    assert "generic_name" in pharmacy["default_settings"]["catalogue"]["attribute_schema"]
    assert clothing["default_settings"]["catalogue"]["variant_axes"] == ["size", "colour"]
    assert "restricted_dispense" in pharmacy["config_schema"]["properties"]
