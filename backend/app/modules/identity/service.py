from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.errors import AppError
from app.core.ids import new_uuid
from app.modules.identity.models import User, UserSession
from app.modules.identity.security import (
    create_access_token,
    decode_access_token,
    dummy_verify,
    hash_password,
    hash_token,
    new_refresh_token,
    verify_password,
)


async def register_user(
    session: AsyncSession,
    *,
    email: str,
    password: str,
    full_name: str,
) -> User:
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
    return user


async def login_user(
    session: AsyncSession,
    *,
    email: str,
    password: str,
    user_agent: str | None,
    ip: str | None,
) -> tuple[User, str]:
    user = await session.scalar(select(User).where(User.email == email.strip().lower()))
    if user is None or not user.is_active:
        dummy_verify(password)
        raise AppError(401, "Invalid email or password", code="unauthenticated")
    if not verify_password(password, user.password_hash):
        raise AppError(401, "Invalid email or password", code="unauthenticated")

    settings = get_settings()
    session_row = UserSession(
        user_id=user.id,
        token_family_id=new_uuid(),
        refresh_token_hash=hash_token(new_refresh_token()),
        expires_at=datetime.now(UTC) + timedelta(days=settings.refresh_token_ttl_days),
        user_agent=(user_agent or "")[:512] or None,
        ip=(ip or "")[:64] or None,
    )
    session.add(session_row)
    await session.flush()
    token = create_access_token(
        user_id=user.id,
        session_id=session_row.id,
        session_version=user.session_version,
    )
    return user, token


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
    expires_at = row.expires_at if row is not None else None
    if expires_at is not None and expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)
    if (
        row is None
        or row.user_id != user.id
        or row.revoked_at is not None
        or expires_at is None
        or expires_at <= now
    ):
        raise AppError(401, "Invalid or expired token", code="unauthenticated")
    return user
