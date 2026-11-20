from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.email import send_email
from app.core.errors import ApiError
from app.core.ids import new_uuid
from app.core.security import (
    create_access_token,
    hash_password,
    hash_token,
    new_url_token,
    verify_password_or_dummy,
)
from app.core.tenancy import apply_rls
from app.models.audit import AuditLog
from app.models.email import OutboundEmail
from app.models.session import UserSession
from app.models.token import UserToken
from app.models.user import User


def normalize_email(email: str) -> str:
    return email.strip().lower()


def to_public(user: User) -> dict:
    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "email_verified": user.email_verified_at is not None,
        "created_at": user.created_at,
    }


async def _audit(
    session: AsyncSession,
    *,
    actor_user_id: UUID | None,
    action: str,
    entity_type: str,
    entity_id: str,
    organization_id: UUID | None = None,
) -> None:
    session.add(
        AuditLog(
            id=new_uuid(),
            organization_id=organization_id,
            actor_user_id=actor_user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
        )
    )


async def register_user(
    session: AsyncSession,
    settings: Settings,
    *,
    email: str,
    password: str,
    full_name: str,
) -> tuple[User, str]:
    email_norm = normalize_email(email)
    existing = await session.scalar(select(User).where(User.email == email_norm))
    if existing:
        raise ApiError(409, "conflict", "An account with this email already exists")

    user = User(
        id=new_uuid(),
        email=email_norm,
        password_hash=hash_password(password),
        full_name=full_name.strip(),
    )
    session.add(user)
    await session.flush()

    raw_token = new_url_token()
    session.add(
        UserToken(
            id=new_uuid(),
            user_id=user.id,
            purpose="email_verify",
            token_hash=hash_token(raw_token),
            expires_at=datetime.now(UTC) + timedelta(hours=settings.email_token_hours),
        )
    )
    verify_url = f"{settings.public_app_url.rstrip('/')}/verify-email?token={raw_token}"
    await send_email(
        session,
        to_email=user.email,
        template="email_verify",
        payload={"verify_url": verify_url, "token": raw_token},
    )
    await _audit(session, actor_user_id=user.id, action="user.register", entity_type="user", entity_id=str(user.id))
    return user, raw_token


async def verify_email(session: AsyncSession, token: str) -> User:
    token_row = await session.scalar(
        select(UserToken).where(
            UserToken.token_hash == hash_token(token),
            UserToken.purpose == "email_verify",
        )
    )
    if (
        token_row is None
        or token_row.used_at is not None
        or token_row.expires_at < datetime.now(UTC)
    ):
        raise ApiError(400, "invalid_token", "This verification link is invalid or has expired")

    user = await session.get(User, token_row.user_id)
    if user is None:
        raise ApiError(400, "invalid_token", "This verification link is invalid or has expired")

    user.email_verified_at = datetime.now(UTC)
    token_row.used_at = datetime.now(UTC)
    await _audit(session, actor_user_id=user.id, action="user.verify_email", entity_type="user", entity_id=str(user.id))
    return user


async def authenticate(
    session: AsyncSession,
    settings: Settings,
    *,
    email: str,
    password: str,
    user_agent: str | None,
    ip: str | None,
) -> tuple[User, UserSession, str, str, str]:
    email_norm = normalize_email(email)
    user = await session.scalar(select(User).where(User.email == email_norm))
    if not verify_password_or_dummy(password, user.password_hash if user else None):
        raise ApiError(401, "unauthenticated", "Invalid email or password")
    if user is None or not user.is_active:
        raise ApiError(401, "unauthenticated", "Invalid email or password")

    return await issue_session(session, settings, user=user, user_agent=user_agent, ip=ip)


async def issue_session(
    session: AsyncSession,
    settings: Settings,
    *,
    user: User,
    user_agent: str | None,
    ip: str | None,
) -> tuple[User, UserSession, str, str, str]:
    refresh_raw = new_url_token()
    csrf_raw = new_url_token()
    family_id = new_uuid()
    db_session = UserSession(
        id=new_uuid(),
        user_id=user.id,
        token_family_id=family_id,
        refresh_token_hash=hash_token(refresh_raw),
        csrf_token_hash=hash_token(csrf_raw),
        expires_at=datetime.now(UTC) + timedelta(days=settings.refresh_token_days),
        user_agent=user_agent,
        ip=ip,
    )
    session.add(db_session)
    await session.flush()
    access = create_access_token(
        settings=settings,
        user_id=user.id,
        session_id=db_session.id,
        token_version=user.token_version,
    )
    await _audit(session, actor_user_id=user.id, action="user.login", entity_type="session", entity_id=str(db_session.id))
    return user, db_session, access, refresh_raw, csrf_raw


async def rotate_refresh(
    session: AsyncSession,
    settings: Settings,
    *,
    refresh_token: str,
    csrf_token: str,
    user_agent: str | None,
    ip: str | None,
) -> tuple[User, UserSession, str, str, str]:
    presented = hash_token(refresh_token)
    db_session = await session.scalar(select(UserSession).where(UserSession.refresh_token_hash == presented))
    if db_session is None:
        reused = await session.scalar(
            select(UserSession).where(UserSession.previous_token_hash == presented)
        )
        if reused is not None:
            reused.revoked_at = datetime.now(UTC)
            family = await session.scalars(
                select(UserSession).where(UserSession.token_family_id == reused.token_family_id)
            )
            now = datetime.now(UTC)
            for item in family:
                item.revoked_at = now
            raise ApiError(401, "unauthenticated", "Session is no longer valid")
        raise ApiError(401, "unauthenticated", "Session is no longer valid")

    if db_session.revoked_at is not None or db_session.expires_at < datetime.now(UTC):
        raise ApiError(401, "unauthenticated", "Session is no longer valid")
    if db_session.csrf_token_hash != hash_token(csrf_token):
        raise ApiError(403, "permission_denied", "Invalid CSRF token")

    user = await session.get(User, db_session.user_id)
    if user is None or not user.is_active:
        raise ApiError(401, "unauthenticated", "Session is no longer valid")

    new_refresh = new_url_token()
    new_csrf = new_url_token()
    db_session.previous_token_hash = db_session.refresh_token_hash
    db_session.refresh_token_hash = hash_token(new_refresh)
    db_session.csrf_token_hash = hash_token(new_csrf)
    db_session.expires_at = datetime.now(UTC) + timedelta(days=settings.refresh_token_days)
    db_session.user_agent = user_agent
    db_session.ip = ip

    access = create_access_token(
        settings=settings,
        user_id=user.id,
        session_id=db_session.id,
        token_version=user.token_version,
    )
    return user, db_session, access, new_refresh, new_csrf


async def logout(session: AsyncSession, db_session: UserSession) -> None:
    db_session.revoked_at = datetime.now(UTC)


async def request_password_reset(session: AsyncSession, settings: Settings, email: str) -> None:
    email_norm = normalize_email(email)
    user = await session.scalar(select(User).where(User.email == email_norm))
    if user is None:
        return
    raw_token = new_url_token()
    session.add(
        UserToken(
            id=new_uuid(),
            user_id=user.id,
            purpose="password_reset",
            token_hash=hash_token(raw_token),
            expires_at=datetime.now(UTC) + timedelta(hours=settings.password_reset_hours),
        )
    )
    reset_url = f"{settings.public_app_url.rstrip('/')}/reset-password?token={raw_token}"
    await send_email(
        session,
        to_email=user.email,
        template="password_reset",
        payload={"reset_url": reset_url, "token": raw_token},
    )


async def reset_password(session: AsyncSession, token: str, password: str) -> User:
    token_row = await session.scalar(
        select(UserToken).where(
            UserToken.token_hash == hash_token(token),
            UserToken.purpose == "password_reset",
        )
    )
    if (
        token_row is None
        or token_row.used_at is not None
        or token_row.expires_at < datetime.now(UTC)
    ):
        raise ApiError(400, "invalid_token", "This reset link is invalid or has expired")

    user = await session.get(User, token_row.user_id)
    if user is None:
        raise ApiError(400, "invalid_token", "This reset link is invalid or has expired")

    user.password_hash = hash_password(password)
    user.token_version += 1
    token_row.used_at = datetime.now(UTC)

    sessions = await session.scalars(select(UserSession).where(UserSession.user_id == user.id))
    now = datetime.now(UTC)
    for item in sessions:
        item.revoked_at = now
    await _audit(session, actor_user_id=user.id, action="user.reset_password", entity_type="user", entity_id=str(user.id))
    return user


async def latest_outbound_email(session: AsyncSession, email: str, template: str) -> OutboundEmail | None:
    return await session.scalar(
        select(OutboundEmail)
        .where(OutboundEmail.to_email == normalize_email(email), OutboundEmail.template == template)
        .order_by(OutboundEmail.created_at.desc())
    )


async def get_user_by_id(session: AsyncSession, user_id: UUID) -> User | None:
    await apply_rls(session, user_id)
    return await session.get(User, user_id)


def require_verified_email(user: User) -> None:
    if user.email_verified_at is None:
        raise ApiError(403, "email_unverified", "Verify your email before creating an organization")


def expose_dev_token(token: str | None) -> str | None:
    from app.core.config import get_settings

    if token is None or get_settings().is_production:
        return None
    return token
