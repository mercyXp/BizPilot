"""allow creator to select organization during insert returning

Revision ID: 20261120_0003
Revises: 20261120_0002
Create Date: 2026-11-20
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20261120_0003"
down_revision: Union[str, None] = "20261120_0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(sa.text("DROP POLICY IF EXISTS organizations_select ON organizations"))
    op.execute(
        sa.text(
            """
            CREATE POLICY organizations_select ON organizations
            FOR SELECT
            USING (
                id = NULLIF(current_setting('app.current_organization_id', true), '')::uuid
                OR created_by_user_id = NULLIF(current_setting('app.current_user_id', true), '')::uuid
                OR EXISTS (
                    SELECT 1 FROM organization_memberships m
                    WHERE m.organization_id = organizations.id
                      AND m.user_id = NULLIF(current_setting('app.current_user_id', true), '')::uuid
                      AND m.status = 'active'
                )
            )
            """
        )
    )


def downgrade() -> None:
    op.execute(sa.text("DROP POLICY IF EXISTS organizations_select ON organizations"))
    op.execute(
        sa.text(
            """
            CREATE POLICY organizations_select ON organizations
            FOR SELECT
            USING (
                id = NULLIF(current_setting('app.current_organization_id', true), '')::uuid
                OR EXISTS (
                    SELECT 1 FROM organization_memberships m
                    WHERE m.organization_id = organizations.id
                      AND m.user_id = NULLIF(current_setting('app.current_user_id', true), '')::uuid
                      AND m.status = 'active'
                )
            )
            """
        )
    )
