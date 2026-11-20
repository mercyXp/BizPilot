from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession


@dataclass
class TenantContext:
    user_id: UUID
    session_id: UUID
    organization_id: UUID | None
    membership_id: UUID | None
    is_owner: bool
    access_all_branches: bool


def _quote_guc(value: str) -> str:
    return value.replace("'", "''")


async def apply_rls(
    session: AsyncSession,
    user_id: UUID | None,
    organization_id: UUID | None = None,
) -> None:
    user_value = _quote_guc(str(user_id) if user_id else "")
    org_value = _quote_guc(str(organization_id) if organization_id else "")
    connection = await session.connection()
    await connection.exec_driver_sql(f"SET LOCAL app.current_user_id = '{user_value}'")
    await connection.exec_driver_sql(
        f"SET LOCAL app.current_organization_id = '{org_value}'"
    )
    await connection.exec_driver_sql(
        f"SELECT set_config('app.current_user_id', '{user_value}', true)"
    )
    await connection.exec_driver_sql(
        f"SELECT set_config('app.current_organization_id', '{org_value}', true)"
    )
