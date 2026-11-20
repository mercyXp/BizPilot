"""phase 3 roles, permissions, branch grants on main scaffold

Revision ID: 20261120_0002
Revises: 20261120_0001
Create Date: 2026-11-20
"""

from typing import Sequence, Union
from uuid import UUID

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

from app.core.ids import new_uuid
from app.modules.authorization.catalog import PERMISSIONS

revision: str = "20261120_0004"
down_revision: Union[str, None] = "20261120_0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

GENERAL_INDUSTRY_ID = "018f5c3a-7b2e-7c1a-8d10-6a1f0b9c3e21"

TENANT_TABLES = (
    "branches",
    "roles",
    "role_permissions",
    "membership_roles",
    "membership_branches",
    "user_permission_overrides",
)

_BOOTSTRAP_SQL = """
CREATE FUNCTION app_current_user() RETURNS uuid
LANGUAGE sql
STABLE
SET search_path = public
AS $$
  SELECT NULLIF(current_setting('app.current_user_id', true), '')::uuid
$$;

CREATE FUNCTION app_current_org() RETURNS uuid
LANGUAGE sql
STABLE
SET search_path = public
AS $$
  SELECT NULLIF(current_setting('app.current_organization_id', true), '')::uuid
$$;

CREATE FUNCTION app_user_is_active_member_internal(p_org uuid, p_user uuid) RETURNS boolean
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public
AS $$
  SELECT EXISTS (
    SELECT 1
    FROM organization_memberships
    WHERE organization_id = p_org
      AND user_id = p_user
      AND status = 'active'
  )
$$;

CREATE FUNCTION app_user_is_active_member(p_org uuid, p_user uuid) RETURNS boolean
LANGUAGE plpgsql
STABLE
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
  IF p_org IS NULL OR p_user IS NULL OR app_current_user() IS NULL THEN
    RETURN false;
  END IF;
  IF p_user IS DISTINCT FROM app_current_user()
     AND NOT app_user_is_active_member_internal(p_org, app_current_user()) THEN
    RETURN false;
  END IF;
  RETURN app_user_is_active_member_internal(p_org, p_user);
END;
$$;

CREATE FUNCTION app_bootstrap_organization(
  p_org_id uuid,
  p_membership_id uuid,
  p_owner_membership_role_id uuid,
  p_name text,
  p_legal_name text,
  p_roles jsonb
) RETURNS uuid
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
  v_user uuid;
  v_active boolean;
  v_industry_id uuid;
  v_role jsonb;
  v_perm jsonb;
  v_perm_id uuid;
BEGIN
  v_user := app_current_user();
  IF v_user IS NULL THEN
    RAISE EXCEPTION 'missing user context' USING ERRCODE = '42501';
  END IF;

  SELECT is_active INTO v_active FROM users WHERE id = v_user;
  IF v_active IS DISTINCT FROM true THEN
    RAISE EXCEPTION 'inactive user' USING ERRCODE = '42501';
  END IF;

  SELECT id INTO v_industry_id FROM industries WHERE code = 'general';
  IF v_industry_id IS NULL THEN
    RAISE EXCEPTION 'general industry is not seeded';
  END IF;

  INSERT INTO organizations (
    id, name, legal_name, industry_id, country_code, base_currency_code, timezone, status, created_by_user_id
  ) VALUES (
    p_org_id, btrim(p_name), NULLIF(btrim(p_legal_name), ''), v_industry_id,
    'ZM', 'ZMW', 'Africa/Lusaka', 'active', v_user
  );

  FOR v_role IN
    SELECT value FROM jsonb_array_elements(p_roles)
  LOOP
    INSERT INTO roles (id, organization_id, code, name, is_system)
    VALUES (
      (v_role->>'id')::uuid,
      p_org_id,
      v_role->>'code',
      v_role->>'name',
      true
    );

    FOR v_perm IN
      SELECT value FROM jsonb_array_elements(v_role->'permissions')
    LOOP
      SELECT id INTO v_perm_id FROM permissions WHERE code = v_perm->>'code';
      IF v_perm_id IS NULL THEN
        RAISE EXCEPTION 'unknown permission %', v_perm->>'code' USING ERRCODE = '22023';
      END IF;
      INSERT INTO role_permissions (id, organization_id, role_id, permission_id)
      VALUES (
        (v_perm->>'id')::uuid,
        p_org_id,
        (v_role->>'id')::uuid,
        v_perm_id
      );
    END LOOP;
  END LOOP;

  INSERT INTO organization_memberships (
    id, organization_id, user_id, status, access_all_branches, is_owner
  ) VALUES (
    p_membership_id, p_org_id, v_user, 'active', true, true
  );

  INSERT INTO membership_roles (id, organization_id, membership_id, role_id)
  SELECT p_owner_membership_role_id, p_org_id, p_membership_id, roles.id
  FROM roles
  WHERE roles.organization_id = p_org_id AND roles.code = 'owner';

  IF NOT FOUND THEN
    RAISE EXCEPTION 'owner role was not created';
  END IF;

  RETURN p_org_id;
END;
$$;
"""

_POLICY_STANDARD = """
CREATE POLICY {table}_tenant_isolation ON {table}
USING (
  organization_id = app_current_org()
  AND app_user_is_active_member(app_current_org(), app_current_user())
)
WITH CHECK (
  organization_id = app_current_org()
  AND app_user_is_active_member(app_current_org(), app_current_user())
)
"""

_POLICY_MEMBERSHIPS = """
CREATE POLICY organization_memberships_tenant_isolation ON organization_memberships
USING (
  user_id = app_current_user()
  OR (
    organization_id = app_current_org()
    AND app_user_is_active_member(app_current_org(), app_current_user())
  )
)
WITH CHECK (
  organization_id = app_current_org()
  AND app_user_is_active_member(app_current_org(), app_current_user())
)
"""


def upgrade() -> None:
    op.create_table(
        "industries",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("config_schema", postgresql.JSONB(), nullable=False),
        sa.Column("default_modules", postgresql.JSONB(), nullable=False),
        sa.Column("default_settings", postgresql.JSONB(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.UniqueConstraint("code", name="uq_industries_code"),
    )
    op.create_table(
        "permissions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("code", sa.String(128), nullable=False),
        sa.Column("description", sa.String(255), nullable=False),
        sa.Column("module", sa.String(64), nullable=False),
        sa.UniqueConstraint("code", name="uq_permissions_code"),
    )
    op.create_table(
        "branches",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("address_json", postgresql.JSONB()),
        sa.Column("phone", sa.String(32)),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("code = upper(code)", name="ck_branches_code_upper"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("organization_id", "code", name="uq_branches_org_code"),
    )
    op.create_table(
        "roles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("is_system", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("organization_id", "code", name="uq_roles_org_code"),
    )
    op.create_table(
        "role_permissions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("permission_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["permission_id"], ["permissions.id"]),
        sa.UniqueConstraint("role_id", "permission_id", name="uq_role_permissions_role_perm"),
    )
    op.create_index("ix_role_permissions_org", "role_permissions", ["organization_id"])
    op.create_table(
        "membership_roles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("membership_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["membership_id"], ["organization_memberships.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("membership_id", "role_id", name="uq_membership_roles_member_role"),
    )
    op.create_index("ix_membership_roles_org", "membership_roles", ["organization_id"])
    op.create_table(
        "membership_branches",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("membership_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("branch_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["membership_id"], ["organization_memberships.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["branch_id"], ["branches.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("membership_id", "branch_id", name="uq_membership_branches_member_branch"),
    )
    op.create_index("ix_membership_branches_org", "membership_branches", ["organization_id"])
    op.create_table(
        "user_permission_overrides",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("membership_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("permission_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("effect", sa.String(8), nullable=False),
        sa.CheckConstraint("effect IN ('allow', 'deny')", name="ck_overrides_effect"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["membership_id"], ["organization_memberships.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["permission_id"], ["permissions.id"]),
        sa.UniqueConstraint("membership_id", "permission_id", name="uq_overrides_member_perm"),
    )
    op.create_index("ix_overrides_org", "user_permission_overrides", ["organization_id"])

    op.bulk_insert(
        sa.table(
            "permissions",
            sa.column("id", postgresql.UUID(as_uuid=True)),
            sa.column("code", sa.String()),
            sa.column("description", sa.String()),
            sa.column("module", sa.String()),
        ),
        [
            {"id": new_uuid(), "code": code, "description": description, "module": module}
            for code, module, description in PERMISSIONS
        ],
    )
    op.bulk_insert(
        sa.table(
            "industries",
            sa.column("id", postgresql.UUID(as_uuid=True)),
            sa.column("code", sa.String()),
            sa.column("name", sa.String()),
            sa.column("config_schema", postgresql.JSONB()),
            sa.column("default_modules", postgresql.JSONB()),
            sa.column("default_settings", postgresql.JSONB()),
            sa.column("is_active", sa.Boolean()),
        ),
        [
            {
                "id": UUID(GENERAL_INDUSTRY_ID),
                "code": "general",
                "name": "General",
                "config_schema": {},
                "default_modules": {},
                "default_settings": {},
                "is_active": True,
            }
        ],
    )

    op.add_column(
        "organizations",
        sa.Column("industry_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.execute(
        sa.text(
            "UPDATE organizations SET industry_id = CAST(:id AS uuid) WHERE industry_id IS NULL"
        ).bindparams(id=GENERAL_INDUSTRY_ID)
    )
    op.alter_column("organizations", "industry_id", nullable=False)
    op.create_foreign_key(
        "fk_organizations_industry",
        "organizations",
        "industries",
        ["industry_id"],
        ["id"],
    )

    op.execute(_BOOTSTRAP_SQL)
    for table in TENANT_TABLES:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
        op.execute(_POLICY_STANDARD.format(table=table))

    op.execute("GRANT SELECT ON permissions, industries TO bizpilot_app")
    op.execute("GRANT SELECT ON roles, role_permissions TO bizpilot_app")
    op.execute("GRANT SELECT, INSERT, DELETE ON membership_roles, membership_branches TO bizpilot_app")
    op.execute(
        "GRANT SELECT, INSERT, UPDATE, DELETE ON user_permission_overrides TO bizpilot_app"
    )
    op.execute(
        """
        ALTER DEFAULT PRIVILEGES IN SCHEMA public
        GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO bizpilot_app
        """
    )
    op.execute("REVOKE ALL ON FUNCTION app_current_user() FROM PUBLIC")
    op.execute("REVOKE ALL ON FUNCTION app_current_org() FROM PUBLIC")
    op.execute("REVOKE ALL ON FUNCTION app_user_is_active_member_internal(uuid, uuid) FROM PUBLIC")
    op.execute("REVOKE ALL ON FUNCTION app_user_is_active_member(uuid, uuid) FROM PUBLIC")
    op.execute(
        "REVOKE ALL ON FUNCTION app_bootstrap_organization(uuid, uuid, uuid, text, text, jsonb) FROM PUBLIC"
    )
    op.execute("GRANT EXECUTE ON FUNCTION app_current_user() TO bizpilot_app")
    op.execute("GRANT EXECUTE ON FUNCTION app_current_org() TO bizpilot_app")
    op.execute("GRANT EXECUTE ON FUNCTION app_user_is_active_member(uuid, uuid) TO bizpilot_app")
    op.execute(
        "GRANT EXECUTE ON FUNCTION app_bootstrap_organization(uuid, uuid, uuid, text, text, jsonb) TO bizpilot_app"
    )
    op.execute(
        "UPDATE app_metadata SET value = '3', updated_at = now() WHERE key = 'schema_phase'"
    )


def downgrade() -> None:
    for table in TENANT_TABLES:
        op.execute(f"DROP POLICY IF EXISTS {table}_tenant_isolation ON {table}")
    op.execute(
        "DROP FUNCTION IF EXISTS app_bootstrap_organization(uuid, uuid, uuid, text, text, jsonb)"
    )
    op.execute("DROP FUNCTION IF EXISTS app_user_is_active_member(uuid, uuid)")
    op.execute("DROP FUNCTION IF EXISTS app_user_is_active_member_internal(uuid, uuid)")
    op.execute("DROP FUNCTION IF EXISTS app_current_org()")
    op.execute("DROP FUNCTION IF EXISTS app_current_user()")
    op.drop_constraint("fk_organizations_industry", "organizations", type_="foreignkey")
    op.drop_column("organizations", "industry_id")
    for table in (
        "user_permission_overrides",
        "membership_branches",
        "membership_roles",
        "role_permissions",
        "roles",
        "branches",
        "permissions",
        "industries",
    ):
        op.drop_table(table)
    op.execute(
        "UPDATE app_metadata SET value = '2', updated_at = now() WHERE key = 'schema_phase'"
    )
