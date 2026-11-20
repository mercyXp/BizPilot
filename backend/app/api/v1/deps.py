from uuid import UUID

import jwt
from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.db import get_db
from app.core.errors import ApiError
from app.core.security import decode_access_token
from app.core.tenancy import TenantContext, apply_rls
from app.models.session import UserSession
from app.models.user import User
from app.modules.tenancy.service import get_active_membership, get_organization


def _bearer_token(request: Request) -> str:
    header = request.headers.get("authorization") or ""
    if not header.lower().startswith("bearer "):
        raise ApiError(401, "unauthenticated", "Authentication required")
    token = header.split(" ", 1)[1].strip()
    if not token:
        raise ApiError(401, "unauthenticated", "Authentication required")
    return token


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> User:
    token = _bearer_token(request)
    try:
        payload = decode_access_token(token, settings)
    except jwt.ExpiredSignatureError as exc:
        raise ApiError(401, "unauthenticated", "Access token expired") from exc
    except jwt.InvalidTokenError as exc:
        raise ApiError(401, "unauthenticated", "Invalid access token") from exc

    if payload.get("typ") != "access":
        raise ApiError(401, "unauthenticated", "Invalid access token")

    try:
        user_id = UUID(str(payload["sub"]))
        session_id = UUID(str(payload["sid"]))
        token_version = int(payload["pv"])
    except (KeyError, ValueError) as exc:
        raise ApiError(401, "unauthenticated", "Invalid access token") from exc

    await apply_rls(db, user_id)
    user = await db.get(User, user_id)
    if user is None or not user.is_active or user.token_version != token_version:
        raise ApiError(401, "unauthenticated", "Invalid access token")

    db_session = await db.get(UserSession, session_id)
    if db_session is None or db_session.revoked_at is not None:
        raise ApiError(401, "unauthenticated", "Session is no longer valid")

    request.state.user = user
    request.state.session = db_session
    return user


async def get_tenant_context(
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> TenantContext:
    raw_org = request.headers.get("x-organization-id")
    if not raw_org:
        raise ApiError(400, "organization_required", "X-Organization-Id header is required")
    try:
        organization_id = UUID(raw_org)
    except ValueError as exc:
        raise ApiError(400, "validation_error", "X-Organization-Id is not a valid UUID") from exc

    membership = await get_active_membership(db, user, organization_id)
    request.state.organization = await get_organization(db, organization_id)
    context = TenantContext(
        user_id=user.id,
        session_id=request.state.session.id,
        organization_id=organization_id,
        membership_id=membership.id,
        is_owner=membership.is_owner,
        access_all_branches=membership.access_all_branches,
    )
    request.state.tenant = context
    return context
