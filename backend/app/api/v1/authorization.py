from fastapi import APIRouter, Depends

from app.api.v1.schemas import AuthorizationContextOut, GateOut
from app.core.context import TenantContext
from app.modules.authorization.deps import get_tenant_context, require_permission

router = APIRouter(prefix="/authorization", tags=["authorization"])


def _context(ctx: TenantContext) -> AuthorizationContextOut:
    return AuthorizationContextOut(
        organization_id=ctx.organization_id,
        membership_id=ctx.membership_id,
        branch_id=ctx.branch_id,
        access_all_branches=ctx.access_all_branches,
        branch_ids=sorted(ctx.branch_ids, key=str),
        permissions=sorted(ctx.permissions),
        is_platform_admin=ctx.is_platform_admin,
    )


@router.get("/context", response_model=AuthorizationContextOut)
async def context(ctx: TenantContext = Depends(get_tenant_context)) -> AuthorizationContextOut:
    return _context(ctx)


@router.post("/gates/journal-post", response_model=GateOut)
async def journal_post(
    _ctx: TenantContext = Depends(require_permission("accounting.journal.post")),
) -> GateOut:
    return GateOut(
        status="authorized",
        action="accounting.journal.post",
        effect="authorization_only",
    )


@router.post("/gates/inventory-adjust", response_model=GateOut)
async def inventory_adjust(
    _ctx: TenantContext = Depends(require_permission("inventory.adjust", branch_scoped=True)),
) -> GateOut:
    return GateOut(
        status="authorized",
        action="inventory.adjust",
        effect="authorization_only",
    )
