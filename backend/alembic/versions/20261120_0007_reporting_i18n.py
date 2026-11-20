"""phase 11-12 translation resources and industry pack refresh

Revision ID: 20261120_0007
Revises: 20261120_0006
Create Date: 2026-11-20
"""

import json
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

from app.core.ids import new_uuid
from app.modules.i18n.catalog import MESSAGES
from app.modules.industry.packs import PACKS

revision: str = "20261120_0007"
down_revision: Union[str, None] = "20261120_0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

UUID = postgresql.UUID(as_uuid=True)


def upgrade() -> None:
    op.create_table(
        "translation_resources",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("locale", sa.String(16), nullable=False),
        sa.Column("key", sa.String(200), nullable=False),
        sa.Column("value", sa.Text(), nullable=False),
        sa.Column("provenance", sa.String(16), nullable=False, server_default=sa.text("'system'")),
        sa.CheckConstraint("provenance IN ('system', 'professional')", name="ck_translation_provenance"),
        sa.UniqueConstraint("locale", "key", name="uq_translation_resources_locale_key"),
    )
    op.execute("GRANT SELECT, INSERT, UPDATE ON translation_resources TO bizpilot_app")

    for locale, key, value in MESSAGES:
        op.execute(
            sa.text(
                """
                INSERT INTO translation_resources (id, locale, key, value, provenance)
                VALUES (CAST(:id AS uuid), :locale, :key, :value, 'system')
                ON CONFLICT (locale, key) DO UPDATE SET
                  value = EXCLUDED.value
                WHERE translation_resources.provenance <> 'professional'
                """
            ).bindparams(id=str(new_uuid()), locale=locale, key=key, value=value)
        )

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

    op.execute(
        "UPDATE app_metadata SET value = '11', updated_at = now() WHERE key = 'schema_phase'"
    )


def downgrade() -> None:
    op.execute(
        "UPDATE app_metadata SET value = '9', updated_at = now() WHERE key = 'schema_phase'"
    )
    op.drop_table("translation_resources")
