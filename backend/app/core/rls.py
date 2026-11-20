from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def set_request_context(
    session: AsyncSession,
    *,
    user_id: UUID | None,
    organization_id: UUID | None,
) -> None:
    """Set transaction-local GUCs used by row-level security policies."""

    await session.execute(
        text("SELECT set_config('app.current_user_id', :user_id, true)"),
        {"user_id": "" if user_id is None else str(user_id)},
    )
    await session.execute(
        text("SELECT set_config('app.current_organization_id', :organization_id, true)"),
        {"organization_id": "" if organization_id is None else str(organization_id)},
    )
