from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.tenancy import apply_rls


async def set_request_context(
    session: AsyncSession,
    *,
    user_id: UUID | None,
    organization_id: UUID | None,
) -> None:
    await apply_rls(session, user_id, organization_id)
