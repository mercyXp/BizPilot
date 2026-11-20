from uuid import UUID

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import TenantContext
from app.core.db import get_db
from app.core.errors import AppError
from app.modules.authorization.service import load_tenant_context
from app.modules.identity.models import User
from app.modules.identity.service import authenticate_access_token

_bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    session: AsyncSession = Depends(get_db),
) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise AppError(401, "Authentication required", code="unauthenticated")
    return await authenticate_access_token(session, credentials.credentials)


async def get_tenant_context(
    request: Request,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> TenantContext:
    organization_id = _uuid_header(request.headers.get("x-organization-id"), "X-Organization-Id")
    if organization_id is None:
        raise AppError(422, "X-Organization-Id is required", code="validation_error")
    branch_id = _uuid_header(request.headers.get("x-branch-id"), "X-Branch-Id")
    return await load_tenant_context(
        session,
        user,
        organization_id=organization_id,
        branch_id=branch_id,
    )


def require_permission(permission: str, *, branch_scoped: bool = False):
    async def dependency(ctx: TenantContext = Depends(get_tenant_context)) -> TenantContext:
        if permission not in ctx.permissions:
            raise AppError(403, f"Missing permission {permission}", code="permission_denied")
        if branch_scoped and ctx.branch_id is None:
            raise AppError(422, "X-Branch-Id is required", code="validation_error")
        return ctx

    return dependency


def _uuid_header(value: str | None, name: str) -> UUID | None:
    if value is None or not value.strip():
        return None
    try:
        return UUID(value.strip())
    except ValueError as exc:
        raise AppError(422, f"{name} must be a UUID", code="validation_error") from exc
