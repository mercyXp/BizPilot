"""hardware, restaurant, and electronics industry packs for the demo centre

Revision ID: 20261120_0008
Revises: 20261120_0007
Create Date: 2026-11-20
"""

import json
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

from app.core.ids import new_uuid
from app.modules.industry.packs import PACKS

revision: str = "20261120_0008"
down_revision: Union[str, None] = "20261120_0007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    for pack in PACKS:
        op.execute(
            sa.text(
                """
                INSERT INTO industries (id, code, name, config_schema, default_modules, default_settings, is_active)
                VALUES (CAST(:id AS uuid), :code, :name, CAST(:config AS jsonb), CAST(:modules AS jsonb), CAST(:settings AS jsonb), true)
                ON CONFLICT (code) DO UPDATE SET
                  name = EXCLUDED.name,
                  config_schema = EXCLUDED.config_schema,
                  default_modules = EXCLUDED.default_modules,
                  default_settings = EXCLUDED.default_settings
                """
            ).bindparams(
                id=str(new_uuid()),
                code=pack["code"],
                name=pack["name"],
                config=json.dumps(pack["config_schema"]),
                modules=json.dumps(pack["default_modules"]),
                settings=json.dumps(pack["default_settings"]),
            )
        )


def downgrade() -> None:
    op.execute("DELETE FROM industries WHERE code IN ('hardware', 'restaurant', 'electronics')")
