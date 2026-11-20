import asyncio
import html
import json
import logging
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.errors import ApiError
from app.core.ids import new_uuid
from app.models.email import OutboundEmail

logger = logging.getLogger(__name__)

_BRAND = "BizPilot"


def render_email(template: str, payload: dict) -> tuple[str, str]:
    if template == "email_verify":
        url = html.escape(str(payload["verify_url"]))
        return (
            f"Verify your {_BRAND} email",
            _wrap(
                "<p>Confirm your email address to finish creating your account.</p>"
                f'<p><a href="{url}">Verify email</a></p>'
                "<p>If you did not create this account, you can ignore this message.</p>"
            ),
        )
    if template == "password_reset":
        url = html.escape(str(payload["reset_url"]))
        return (
            f"Reset your {_BRAND} password",
            _wrap(
                "<p>We received a request to reset your password.</p>"
                f'<p><a href="{url}">Reset password</a></p>'
                "<p>If you did not ask for this, you can ignore this message.</p>"
            ),
        )
    if template == "organization_invite":
        url = html.escape(str(payload["accept_url"]))
        org = html.escape(str(payload.get("organization_name") or _BRAND))
        return (
            f"You are invited to {org} on {_BRAND}",
            _wrap(
                f"<p>You have been invited to join <strong>{org}</strong> on {_BRAND}.</p>"
                f'<p><a href="{url}">Accept invitation</a></p>'
                "<p>Sign in (or create an account with this email) before opening the link.</p>"
            ),
        )
    return (
        f"{_BRAND} notification",
        _wrap("<p>You have a new notification in BizPilot.</p>"),
    )


def _wrap(inner: str) -> str:
    return (
        "<!DOCTYPE html><html><body style=\"font-family:system-ui,sans-serif;"
        'color:#1a1a1a;line-height:1.5">'
        f"<p><strong>{_BRAND}</strong></p>{inner}"
        f"<p style=\"color:#666;font-size:12px\">Sent by {_BRAND}</p>"
        "</body></html>"
    )


def email_delivery_mode(settings: Settings) -> str:
    if settings.app_env == "test":
        return "log_only"
    if settings.resend_api_key.strip():
        return "resend"
    if settings.requires_email_provider:
        return "missing"
    return "log_only"


def deliver_via_resend(
    *,
    api_key: str,
    from_email: str,
    to_email: str,
    subject: str,
    html_body: str,
) -> str | None:
    import resend

    resend.api_key = api_key
    result: Any = resend.Emails.send(
        {
            "from": from_email,
            "to": [to_email],
            "subject": subject,
            "html": html_body,
        }
    )
    if isinstance(result, dict):
        message_id = result.get("id")
        return str(message_id) if message_id else None
    message_id = getattr(result, "id", None)
    return str(message_id) if message_id else None


async def send_email(
    session: AsyncSession,
    *,
    to_email: str,
    template: str,
    payload: dict,
    organization_id: UUID | None = None,
    settings: Settings | None = None,
) -> OutboundEmail:
    resolved = settings or get_settings()
    record = OutboundEmail(
        id=new_uuid(),
        organization_id=organization_id,
        to_email=to_email,
        template=template,
        payload_json=json.dumps(payload),
    )
    session.add(record)
    logger.info("outbound_email template=%s to=%s", template, to_email)

    mode = email_delivery_mode(resolved)
    if mode == "log_only":
        return record
    if mode == "missing":
        raise ApiError(
            503,
            "unavailable",
            "Email delivery is not configured. Set RESEND_API_KEY and RESEND_FROM_EMAIL.",
        )

    subject, html_body = render_email(template, payload)
    try:
        message_id = await asyncio.to_thread(
            deliver_via_resend,
            api_key=resolved.resend_api_key.strip(),
            from_email=resolved.resend_from_email.strip(),
            to_email=to_email,
            subject=subject,
            html_body=html_body,
        )
    except ApiError:
        raise
    except Exception as exc:
        logger.exception("resend_send_failed template=%s to=%s", template, to_email)
        raise ApiError(502, "email_delivery_failed", "Could not send email") from exc

    if message_id:
        logger.info("resend_sent template=%s to=%s", template, to_email)
    return record
