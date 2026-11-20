"""phase2 authentication and tenancy

Revision ID: 20261120_0002
Revises: 20261120_0001
Create Date: 2026-11-20
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20261120_0002"
down_revision: Union[str, None] = "20261120_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        sa.text(
            """
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'bizpilot_app') THEN
                    CREATE ROLE bizpilot_app LOGIN NOSUPERUSER NOBYPASSRLS
                        NOCREATEDB NOCREATEROLE NOINHERIT;
                END IF;
            END
            $$;
            """
        )
    )
    op.execute(sa.text("GRANT CONNECT ON DATABASE bizpilot TO bizpilot_app"))
    op.execute(sa.text("GRANT USAGE ON SCHEMA public TO bizpilot_app"))
    op.execute(
        sa.text(
            "ALTER DEFAULT PRIVILEGES IN SCHEMA public "
            "GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO bizpilot_app"
        )
    )
    op.execute(
        sa.text(
            "GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE app_metadata TO bizpilot_app"
        )
    )

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(200), nullable=False),
        sa.Column("phone", sa.String(32)),
        sa.Column("email_verified_at", sa.DateTime(timezone=True)),
        sa.Column("platform_role", sa.String(32)),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("token_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("totp_secret_encrypted", sa.String(255)),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )

    op.create_table(
        "user_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token_family_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("refresh_token_hash", sa.String(64), nullable=False),
        sa.Column("previous_token_hash", sa.String(64)),
        sa.Column("csrf_token_hash", sa.String(64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True)),
        sa.Column("user_agent", sa.String(512)),
        sa.Column("ip", sa.String(64)),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("refresh_token_hash", name="uq_sessions_refresh_hash"),
    )
    op.create_index("ix_user_sessions_user_id", "user_sessions", ["user_id"])
    op.create_index("ix_user_sessions_family", "user_sessions", ["token_family_id"])

    op.create_table(
        "user_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("purpose", sa.String(32), nullable=False),
        sa.Column("token_hash", sa.String(64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True)),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("token_hash", name="uq_user_tokens_hash"),
    )

    op.create_table(
        "organizations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("legal_name", sa.String(200)),
        sa.Column("country_code", sa.String(2), nullable=False, server_default="ZM"),
        sa.Column("base_currency_code", sa.String(3), nullable=False, server_default="ZMW"),
        sa.Column("timezone", sa.String(64), nullable=False, server_default="Africa/Lusaka"),
        sa.Column("status", sa.String(32), nullable=False, server_default="active"),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    op.create_table(
        "organization_memberships",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("status", sa.String(32), nullable=False, server_default="active"),
        sa.Column("is_owner", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("access_all_branches", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("organization_id", "user_id", name="uq_membership_org_user"),
    )
    op.create_index("ix_memberships_user_id", "organization_memberships", ["user_id"])

    op.create_table(
        "invitations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("token_hash", sa.String(64), nullable=False),
        sa.Column("invited_by_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("accepted_at", sa.DateTime(timezone=True)),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("token_hash", name="uq_invitations_token_hash"),
    )
    op.create_index("ix_invitations_org_email", "invitations", ["organization_id", "email"])

    op.create_table(
        "outbound_emails",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True)),
        sa.Column("to_email", sa.String(320), nullable=False),
        sa.Column("template", sa.String(64), nullable=False),
        sa.Column("payload_json", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_outbound_emails_to", "outbound_emails", ["to_email", "created_at"])

    op.create_table(
        "audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True)),
        sa.Column("actor_user_id", postgresql.UUID(as_uuid=True)),
        sa.Column("action", sa.String(64), nullable=False),
        sa.Column("entity_type", sa.String(64), nullable=False),
        sa.Column("entity_id", sa.String(64), nullable=False),
        sa.Column("metadata_json", sa.Text()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    op.execute(
        sa.text(
            """
            GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE
                users, user_sessions, user_tokens, organizations,
                organization_memberships, invitations, outbound_emails, audit_logs
            TO bizpilot_app
            """
        )
    )

    op.execute(sa.text("ALTER TABLE organizations ENABLE ROW LEVEL SECURITY"))
    op.execute(sa.text("ALTER TABLE organizations FORCE ROW LEVEL SECURITY"))
    op.execute(sa.text("ALTER TABLE organization_memberships ENABLE ROW LEVEL SECURITY"))
    op.execute(sa.text("ALTER TABLE organization_memberships FORCE ROW LEVEL SECURITY"))
    op.execute(sa.text("ALTER TABLE invitations ENABLE ROW LEVEL SECURITY"))
    op.execute(sa.text("ALTER TABLE invitations FORCE ROW LEVEL SECURITY"))

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
    op.execute(
        sa.text(
            """
            CREATE POLICY organizations_insert ON organizations
            FOR INSERT
            WITH CHECK (NULLIF(current_setting('app.current_user_id', true), '') IS NOT NULL)
            """
        )
    )
    op.execute(
        sa.text(
            """
            CREATE POLICY organizations_update ON organizations
            FOR UPDATE
            USING (
                id = NULLIF(current_setting('app.current_organization_id', true), '')::uuid
            )
            WITH CHECK (
                id = NULLIF(current_setting('app.current_organization_id', true), '')::uuid
            )
            """
        )
    )

    op.execute(
        sa.text(
            """
            CREATE POLICY memberships_select ON organization_memberships
            FOR SELECT
            USING (
                user_id = NULLIF(current_setting('app.current_user_id', true), '')::uuid
                OR organization_id = NULLIF(current_setting('app.current_organization_id', true), '')::uuid
            )
            """
        )
    )
    op.execute(
        sa.text(
            """
            CREATE POLICY memberships_insert ON organization_memberships
            FOR INSERT
            WITH CHECK (
                user_id = NULLIF(current_setting('app.current_user_id', true), '')::uuid
                OR organization_id = NULLIF(current_setting('app.current_organization_id', true), '')::uuid
            )
            """
        )
    )
    op.execute(
        sa.text(
            """
            CREATE POLICY memberships_update ON organization_memberships
            FOR UPDATE
            USING (
                organization_id = NULLIF(current_setting('app.current_organization_id', true), '')::uuid
                OR user_id = NULLIF(current_setting('app.current_user_id', true), '')::uuid
            )
            """
        )
    )

    op.execute(
        sa.text(
            """
            CREATE POLICY invitations_tenant ON invitations
            FOR ALL
            USING (
                organization_id = NULLIF(current_setting('app.current_organization_id', true), '')::uuid
            )
            WITH CHECK (
                organization_id = NULLIF(current_setting('app.current_organization_id', true), '')::uuid
            )
            """
        )
    )
    op.execute(
        sa.text(
            """
            CREATE POLICY invitations_by_email ON invitations
            FOR SELECT
            USING (
                email IN (
                    SELECT u.email FROM users u
                    WHERE u.id = NULLIF(current_setting('app.current_user_id', true), '')::uuid
                )
            )
            """
        )
    )

    op.execute(
        sa.text(
            """
            CREATE OR REPLACE FUNCTION lookup_invitation_by_hash(p_hash text)
            RETURNS invitations
            LANGUAGE sql
            SECURITY DEFINER
            SET search_path = public
            STABLE
            AS $$
                SELECT * FROM invitations WHERE token_hash = p_hash LIMIT 1
            $$;
            """
        )
    )
    op.execute(
        sa.text("GRANT EXECUTE ON FUNCTION lookup_invitation_by_hash(text) TO bizpilot_app")
    )

    op.execute(sa.text("UPDATE app_metadata SET value = '2' WHERE key = 'schema_phase'"))


def downgrade() -> None:
    op.execute(sa.text("DROP POLICY IF EXISTS invitations_by_email ON invitations"))
    op.execute(sa.text("DROP POLICY IF EXISTS invitations_tenant ON invitations"))
    op.execute(sa.text("DROP POLICY IF EXISTS memberships_update ON organization_memberships"))
    op.execute(sa.text("DROP POLICY IF EXISTS memberships_insert ON organization_memberships"))
    op.execute(sa.text("DROP POLICY IF EXISTS memberships_select ON organization_memberships"))
    op.execute(sa.text("DROP POLICY IF EXISTS organizations_update ON organizations"))
    op.execute(sa.text("DROP POLICY IF EXISTS organizations_insert ON organizations"))
    op.execute(sa.text("DROP POLICY IF EXISTS organizations_select ON organizations"))
    op.drop_table("audit_logs")
    op.drop_table("outbound_emails")
    op.drop_table("invitations")
    op.drop_table("organization_memberships")
    op.drop_table("organizations")
    op.drop_table("user_tokens")
    op.drop_table("user_sessions")
    op.drop_table("users")
    op.execute(sa.text("UPDATE app_metadata SET value = '1' WHERE key = 'schema_phase'"))
