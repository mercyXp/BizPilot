import json

import pytest
from httpx import AsyncClient
from app.core.config import Settings
from app.core.db import SessionLocal
from app.core.email import email_delivery_mode, render_email, send_email
from app.core.errors import ApiError
from app.models.email import OutboundEmail
from tests.helpers import latest_email_token, register_user, unique_email


def test_email_templates_put_links_not_raw_tokens() -> None:
    verify_html = render_email(
        "email_verify",
        {"verify_url": "https://app.example/verify-email?token=secret-token", "token": "secret-token"},
    )[1]
    assert "https://app.example/verify-email?token=secret-token" in verify_html
    assert "secret-token" in verify_html
    invite_subject, invite_html = render_email(
        "organization_invite",
        {
            "accept_url": "https://app.example/accept-invite?token=abc",
            "organization_name": "Mwamba <script>",
        },
    )
    assert "Mwamba" in invite_subject
    assert "&lt;script&gt;" in invite_html
    assert "<script>" not in invite_html


def test_delivery_mode_never_live_in_test() -> None:
    assert (
        email_delivery_mode(
            Settings(app_env="test", resend_api_key="re_should_not_send", resend_from_email="a@b.c")
        )
        == "log_only"
    )
    assert (
        email_delivery_mode(Settings(app_env="development", resend_api_key="", resend_from_email="a@b.c"))
        == "log_only"
    )
    assert (
        email_delivery_mode(
            Settings(
                app_env="production",
                resend_api_key="re_live",
                resend_from_email="BizPilot <a@b.c>",
                bizpilot_app_password="app-secret",
            )
        )
        == "resend"
    )
    assert (
        email_delivery_mode(
            Settings(
                app_env="production",
                resend_api_key="",
                resend_from_email="a@b.c",
                bizpilot_app_password="app-secret",
            )
        )
        == "missing"
    )


@pytest.mark.asyncio
async def test_register_records_outbound_email_without_resend(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    def boom(**_kwargs):
        raise AssertionError("Resend must not be called in APP_ENV=test")

    monkeypatch.setattr("app.core.email.deliver_via_resend", boom)
    email = unique_email("resend-skip")
    await register_user(client, email)
    token = await latest_email_token(email, "email_verify")
    assert len(token) > 10


@pytest.mark.asyncio
async def test_send_email_calls_resend_outside_test(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict = {}

    def fake_send(*, api_key: str, from_email: str, to_email: str, subject: str, html_body: str) -> str:
        captured.update(
            {
                "api_key": api_key,
                "from_email": from_email,
                "to_email": to_email,
                "subject": subject,
                "html_body": html_body,
            }
        )
        return "re_test_id"

    monkeypatch.setattr("app.core.email.deliver_via_resend", fake_send)
    settings = Settings(
        app_env="development",
        resend_api_key="re_test_key",
        resend_from_email="BizPilot <noreply@example.com>",
        public_app_url="https://app.example",
    )
    async with SessionLocal() as session:
        record = await send_email(
            session,
            to_email="owner@example.com",
            template="email_verify",
            payload={
                "verify_url": "https://app.example/verify-email?token=abc",
                "token": "abc",
            },
            settings=settings,
        )
        await session.commit()
        stored = await session.get(OutboundEmail, record.id)
    assert stored is not None
    assert json.loads(stored.payload_json)["token"] == "abc"
    assert captured["api_key"] == "re_test_key"
    assert captured["to_email"] == "owner@example.com"
    assert "Verify" in captured["subject"]
    assert "https://app.example/verify-email?token=abc" in captured["html_body"]


@pytest.mark.asyncio
async def test_production_send_without_key_fails() -> None:
    settings = Settings(
        app_env="production",
        resend_api_key="",
        resend_from_email="a@b.c",
        bizpilot_app_password="app-secret",
    )
    async with SessionLocal() as session:
        with pytest.raises(ApiError) as exc:
            await send_email(
                session,
                to_email="owner@example.com",
                template="email_verify",
                payload={"verify_url": "https://x/y", "token": "t"},
                settings=settings,
            )
        await session.rollback()
    assert exc.value.status_code == 503


@pytest.mark.asyncio
async def test_ready_reports_email_log_only(client: AsyncClient) -> None:
    response = await client.get("/api/v1/health/ready")
    assert response.status_code == 200
    assert response.json()["checks"]["email"] == "log_only"
