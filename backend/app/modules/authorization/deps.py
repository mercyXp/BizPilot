from uuid import UUID

from fastapi import Depends, Request

from app.api.v1.deps import get_current_user, get_tenant_context
from app.core.errors import AppError
from app.core.tenancy import TenantContext
from app.models.user import User

__all__ = ["get_current_user", "get_tenant_context", "require_permission", "User"]


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


def parse_branch_header(request: Request) -> UUID | None:
    return _uuid_header(request.headers.get("x-branch-id"), "X-Branch-Id")
