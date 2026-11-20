import logging
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.errors import AppError
from app.core.ids import new_uuid
from app.modules.identity.models import User, UserActionToken, UserSession
from app.modules.identity.security import (
    aware,
    create_access_token,
    decode_access_token,
    dummy_verify,
    hash_password,
    hash_token,
    new_action_token,
    new_csrf_token,
    new_refresh_token,
    verify_password,
)
from app.modules.identity.totp import (
    decrypt_secret,
    encrypt_secret,
    new_secret,
    provisioning_uri,
    verify_code,
)

logger = logging.getLogger(__name__)

VERIFY_TTL = timedelta(hours=24)
RESET_TTL = timedelta(hours=1)


@dataclass
class LoginResult:
    user: User
    access_token: str | None
    refresh_token: str | None
    csrf_token: str | None
    totp_required: bool


async def register_user(
    session: AsyncSession,
    *,
    email: str,
    password: str,
    full_name: str,
) -> tuple[User, str]:
    user = User(
        email=email.strip().lower(),
        password_hash=hash_password(password),
        full_name=full_name.strip(),
    )
    session.add(user)
    try:
        await session.flush()
    except IntegrityError as exc:
        raise AppError(409, "An account with this email already exists", code="conflict") from exc
    token = await _issue_action_token(session, user.id, "verify_email", VERIFY_TTL)
    logger.info("email_event verify_email queued", extra={"email": user.email})
    return user, token


async def login_user(
    session: AsyncSession,
    *,
    email: str,
    password: str,
    totp_code: str | None,
    user_agent: str | None,
    ip: str | None,
) -> LoginResult:
    user = await session.scalar(select(User).where(User.email == email.strip().lower()))
    if user is None or not user.is_active:
        dummy_verify(password)
        raise AppError(401, "Invalid email or password", code="unauthenticated")
    if not verify_password(password, user.password_hash):
        raise AppError(401, "Invalid email or password", code="unauthenticated")
    if user.totp_secret_encrypted:
        if not totp_code:
            raise AppError(401, "Authenticator code required", code="totp_required")
        secret = decrypt_secret(user.totp_secret_encrypted)
        if not verify_code(secret, totp_code):
            raise AppError(401, "Invalid authenticator code", code="unauthenticated")

    refresh = new_refresh_token()
    csrf = new_csrf_token()
    settings = get_settings()
    session_row = UserSession(
        user_id=user.id,
        token_family_id=new_uuid(),
        refresh_token_hash=hash_token(refresh),
        expires_at=datetime.now(UTC) + timedelta(days=settings.refresh_token_ttl_days),
        user_agent=(user_agent or "")[:512] or None,
        ip=(ip or "")[:64] or None,
    )
    session.add(session_row)
    await session.flush()
    access = create_access_token(
        user_id=user.id,
        session_id=session_row.id,
        session_version=user.session_version,
    )
    return LoginResult(
        user=user,
        access_token=access,
        refresh_token=refresh,
        csrf_token=csrf,
        totp_required=False,
    )


async def refresh_session(session: AsyncSession, raw_token: str) -> LoginResult:
    token_hash = hash_token(raw_token)
    row = await session.scalar(select(UserSession).where(UserSession.refresh_token_hash == token_hash))
    now = datetime.now(UTC)
    if row is None:
        raise AppError(401, "Invalid or expired token", code="unauthenticated")
    if row.revoked_at is not None:
        await _revoke_family(session, row.token_family_id)
        raise AppError(401, "Refresh token reuse detected", code="unauthenticated")
    expires_at = aware(row.expires_at)
    if expires_at is None or expires_at <= now:
        raise AppError(401, "Invalid or expired token", code="unauthenticated")

    user = await session.get(User, row.user_id)
    if user is None or not user.is_active:
        raise AppError(401, "Invalid or expired token", code="unauthenticated")

    row.revoked_at = now
    refresh = new_refresh_token()
    csrf = new_csrf_token()
    settings = get_settings()
    rotated = UserSession(
        user_id=user.id,
        token_family_id=row.token_family_id,
        refresh_token_hash=hash_token(refresh),
        expires_at=now + timedelta(days=settings.refresh_token_ttl_days),
        rotated_from_id=row.id,
        user_agent=row.user_agent,
        ip=row.ip,
    )
    session.add(rotated)
    await session.flush()
    access = create_access_token(
        user_id=user.id,
        session_id=rotated.id,
        session_version=user.session_version,
    )
    return LoginResult(
        user=user,
        access_token=access,
        refresh_token=refresh,
        csrf_token=csrf,
        totp_required=False,
    )


async def logout_session(session: AsyncSession, raw_token: str) -> None:
    token_hash = hash_token(raw_token)
    row = await session.scalar(select(UserSession).where(UserSession.refresh_token_hash == token_hash))
    if row is None:
        return
    await _revoke_family(session, row.token_family_id)


async def authenticate_access_token(session: AsyncSession, token: str) -> User:
    payload = decode_access_token(token)
    try:
        user_id = UUID(str(payload["sub"]))
        session_id = UUID(str(payload["sid"]))
        version = int(payload["pv"])
    except (KeyError, ValueError) as exc:
        raise AppError(401, "Invalid or expired token", code="unauthenticated") from exc

    user = await session.get(User, user_id)
    if user is None or not user.is_active or user.session_version != version:
        raise AppError(401, "Invalid or expired token", code="unauthenticated")

    row = await session.get(UserSession, session_id)
    now = datetime.now(UTC)
    expires_at = aware(row.expires_at) if row is not None else None
    if (
        row is None
        or row.user_id != user.id
        or row.revoked_at is not None
        or expires_at is None
        or expires_at <= now
    ):
        raise AppError(401, "Invalid or expired token", code="unauthenticated")
    return user


async def verify_email(session: AsyncSession, raw_token: str) -> User:
    token_row = await _unused_token(session, raw_token, "verify_email")
    user = await session.get(User, token_row.user_id)
    if user is None:
        raise AppError(400, "Invalid or expired token", code="validation_error")
    user.email_verified_at = datetime.now(UTC)
    token_row.used_at = datetime.now(UTC)
    await session.flush()
    return user


async def resend_verification(session: AsyncSession, email: str) -> str | None:
    user = await session.scalar(select(User).where(User.email == email.strip().lower()))
    if user is None or not user.is_active:
        return None
    if user.email_verified_at is not None:
        raise AppError(409, "Email is already verified", code="conflict")
    token = await _issue_action_token(session, user.id, "verify_email", VERIFY_TTL)
    logger.info("email_event verify_email queued", extra={"email": user.email})
    return token


async def request_password_reset(session: AsyncSession, email: str) -> str | None:
    user = await session.scalar(select(User).where(User.email == email.strip().lower()))
    if user is None or not user.is_active:
        dummy_verify("password-reset")
        return None
    token = await _issue_action_token(session, user.id, "password_reset", RESET_TTL)
    logger.info("email_event password_reset queued", extra={"email": user.email})
    return token


async def confirm_password_reset(session: AsyncSession, raw_token: str, password: str) -> None:
    token_row = await _unused_token(session, raw_token, "password_reset")
    user = await session.get(User, token_row.user_id)
    if user is None or not user.is_active:
        raise AppError(400, "Invalid or expired token", code="validation_error")
    user.password_hash = hash_password(password)
    user.session_version += 1
    token_row.used_at = datetime.now(UTC)
    await session.execute(
        update(UserSession)
        .where(UserSession.user_id == user.id, UserSession.revoked_at.is_(None))
        .values(revoked_at=datetime.now(UTC))
    )
    await session.flush()


async def enable_totp(session: AsyncSession, user: User) -> tuple[str, str]:
    if user.totp_secret_encrypted:
        raise AppError(409, "Authenticator is already enabled", code="conflict")
    secret = new_secret()
    user.totp_pending_encrypted = encrypt_secret(secret)
    await session.flush()
    return secret, provisioning_uri(email=user.email, secret=secret)


async def confirm_totp(session: AsyncSession, user: User, code: str) -> None:
    if not user.totp_pending_encrypted:
        raise AppError(400, "No authenticator setup is in progress", code="validation_error")
    secret = decrypt_secret(user.totp_pending_encrypted)
    if not verify_code(secret, code):
        raise AppError(400, "Invalid authenticator code", code="validation_error")
    user.totp_secret_encrypted = user.totp_pending_encrypted
    user.totp_pending_encrypted = None
    await session.flush()


async def disable_totp(session: AsyncSession, user: User, password: str, code: str) -> None:
    if not user.totp_secret_encrypted:
        raise AppError(409, "Authenticator is not enabled", code="conflict")
    if not verify_password(password, user.password_hash):
        raise AppError(401, "Invalid email or password", code="unauthenticated")
    if not verify_code(decrypt_secret(user.totp_secret_encrypted), code):
        raise AppError(400, "Invalid authenticator code", code="validation_error")
    user.totp_secret_encrypted = None
    user.totp_pending_encrypted = None
    await session.flush()


def require_verified_email(user: User) -> None:
    if user.email_verified_at is None:
        raise AppError(
            403,
            "Verify your email before creating an organization",
            code="email_unverified",
        )


def expose_dev_token(token: str | None) -> str | None:
    if token is None:
        return None
    if get_settings().is_production:
        return None
    return token


async def _issue_action_token(
    session: AsyncSession,
    user_id: UUID,
    purpose: str,
    ttl: timedelta,
) -> str:
    await session.execute(
        update(UserActionToken)
        .where(
            UserActionToken.user_id == user_id,
            UserActionToken.purpose == purpose,
            UserActionToken.used_at.is_(None),
        )
        .values(used_at=datetime.now(UTC))
    )
    raw = new_action_token()
    session.add(
        UserActionToken(
            user_id=user_id,
            purpose=purpose,
            token_hash=hash_token(raw),
            expires_at=datetime.now(UTC) + ttl,
        )
    )
    await session.flush()
    return raw


async def _unused_token(session: AsyncSession, raw_token: str, purpose: str) -> UserActionToken:
    row = await session.scalar(
        select(UserActionToken).where(UserActionToken.token_hash == hash_token(raw_token))
    )
    now = datetime.now(UTC)
    expires_at = aware(row.expires_at) if row is not None else None
    if (
        row is None
        or row.purpose != purpose
        or row.used_at is not None
        or expires_at is None
        or expires_at <= now
    ):
        raise AppError(400, "Invalid or expired token", code="validation_error")
    return row


async def _revoke_family(session: AsyncSession, family_id: UUID) -> None:
    await session.execute(
        update(UserSession)
        .where(UserSession.token_family_id == family_id, UserSession.revoked_at.is_(None))
        .values(revoked_at=datetime.now(UTC))
    )
