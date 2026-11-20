"""phase 4 org settings/warehouses and phase 5 catalogue on main scaffold

Revision ID: 20261120_0003
Revises: 20261120_0002
Create Date: 2026-11-20
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

from app.core.ids import new_uuid
from app.modules.industry.packs import PACKS

revision: str = "20261120_0005"
down_revision: Union[str, None] = "20261120_0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TENANT_TABLES = (
    "organization_settings",
    "organization_locales",
    "warehouses",
    "units_of_measure",
    "product_categories",
    "product_tax_categories",
    "products",
    "product_variants",
    "product_prices",
    "branch_products",
    "product_batches",
    "stock_balances",
    "stock_movements",
    "document_sequences",
    "stock_transfers",
    "stock_transfer_items",
    "stock_counts",
    "stock_count_items",
)

_POLICY = """
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

_BOOTSTRAP = r"""
DROP FUNCTION IF EXISTS app_bootstrap_organization(uuid, uuid, uuid, text, text, jsonb);

CREATE FUNCTION app_bootstrap_organization(
  p_org_id uuid,
  p_membership_id uuid,
  p_owner_membership_role_id uuid,
  p_name text,
  p_legal_name text,
  p_roles jsonb,
  p_industry_code text,
  p_timezone text,
  p_currency text,
  p_country text
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
  SELECT id INTO v_industry_id FROM industries WHERE code = p_industry_code AND is_active;
  IF v_industry_id IS NULL THEN
    RAISE EXCEPTION 'industry is not seeded' USING ERRCODE = '22023';
  END IF;
  INSERT INTO organizations (
    id, name, legal_name, industry_id, country_code, base_currency_code, timezone, status, created_by_user_id
  ) VALUES (
    p_org_id, btrim(p_name), NULLIF(btrim(p_legal_name), ''), v_industry_id,
    COALESCE(NULLIF(p_country, ''), 'ZM'),
    COALESCE(NULLIF(p_currency, ''), 'ZMW'),
    COALESCE(NULLIF(p_timezone, ''), 'Africa/Lusaka'),
    'active',
    v_user
  );
  FOR v_role IN SELECT value FROM jsonb_array_elements(p_roles)
  LOOP
    INSERT INTO roles (id, organization_id, code, name, is_system)
    VALUES ((v_role->>'id')::uuid, p_org_id, v_role->>'code', v_role->>'name', true);
    FOR v_perm IN SELECT value FROM jsonb_array_elements(v_role->'permissions')
    LOOP
      SELECT id INTO v_perm_id FROM permissions WHERE code = v_perm->>'code';
      IF v_perm_id IS NULL THEN
        RAISE EXCEPTION 'unknown permission %', v_perm->>'code' USING ERRCODE = '22023';
      END IF;
      INSERT INTO role_permissions (id, organization_id, role_id, permission_id)
      VALUES ((v_perm->>'id')::uuid, p_org_id, (v_role->>'id')::uuid, v_perm_id);
    END LOOP;
  END LOOP;
  INSERT INTO organization_memberships (id, organization_id, user_id, status, access_all_branches, is_owner)
  VALUES (p_membership_id, p_org_id, v_user, 'active', true, true);
  INSERT INTO membership_roles (id, organization_id, membership_id, role_id)
  SELECT p_owner_membership_role_id, p_org_id, p_membership_id, roles.id
  FROM roles WHERE roles.organization_id = p_org_id AND roles.code = 'owner';
  IF NOT FOUND THEN
    RAISE EXCEPTION 'owner role was not created';
  END IF;
  RETURN p_org_id;
END;
$$;
"""

_ACCEPT = r"""
CREATE FUNCTION app_accept_invitation(p_token_hash text, p_membership_id uuid) RETURNS uuid
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
  v_user uuid;
  v_email text;
  v_inv invitations%ROWTYPE;
  v_role uuid;
  v_branch uuid;
BEGIN
  v_user := app_current_user();
  IF v_user IS NULL THEN
    RAISE EXCEPTION 'unauthenticated' USING ERRCODE = '42501';
  END IF;
  SELECT email INTO v_email FROM users WHERE id = v_user AND is_active;
  IF v_email IS NULL THEN
    RAISE EXCEPTION 'unauthenticated' USING ERRCODE = '42501';
  END IF;
  SELECT * INTO v_inv FROM invitations WHERE token_hash = p_token_hash;
  IF NOT FOUND THEN
    RAISE EXCEPTION 'invitation not found' USING ERRCODE = 'P0002';
  END IF;
  IF v_inv.accepted_at IS NOT NULL OR v_inv.expires_at <= now() THEN
    RAISE EXCEPTION 'invitation expired' USING ERRCODE = '22023';
  END IF;
  IF v_inv.email <> v_email THEN
    RAISE EXCEPTION 'invitation email mismatch' USING ERRCODE = '42501';
  END IF;
  INSERT INTO organization_memberships (
    id, organization_id, user_id, status, access_all_branches
  ) VALUES (
    p_membership_id, v_inv.organization_id, v_user, 'active', v_inv.access_all_branches
  );
  FOREACH v_role IN ARRAY v_inv.role_ids
  LOOP
    INSERT INTO membership_roles (id, organization_id, membership_id, role_id)
    VALUES (gen_random_uuid(), v_inv.organization_id, p_membership_id, v_role);
  END LOOP;
  FOREACH v_branch IN ARRAY v_inv.branch_ids
  LOOP
    INSERT INTO membership_branches (id, organization_id, membership_id, branch_id)
    VALUES (gen_random_uuid(), v_inv.organization_id, p_membership_id, v_branch);
  END LOOP;
  UPDATE invitations SET accepted_at = now() WHERE id = v_inv.id;
  RETURN p_membership_id;
END;
$$;
"""


def upgrade() -> None:
    op.create_table(
        "organization_settings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("settings", postgresql.JSONB(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("organization_id", name="uq_organization_settings_org"),
    )
    op.create_table(
        "organization_locales",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("default_locale", sa.String(16), nullable=False, server_default=sa.text("'en'")),
        sa.Column(
            "enabled_locales",
            postgresql.ARRAY(sa.Text()),
            nullable=False,
            server_default=sa.text("ARRAY['en']::text[]"),
        ),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("organization_id", name="uq_organization_locales_org"),
    )
    op.create_table(
        "warehouses",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("branch_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["branch_id"], ["branches.id"]),
        sa.UniqueConstraint("organization_id", "code", name="uq_warehouses_org_code"),
    )
    op.create_index(
        "uq_warehouses_one_default_per_branch",
        "warehouses",
        ["branch_id"],
        unique=True,
        postgresql_where=sa.text("is_default"),
    )
    op.add_column(
        "invitations",
        sa.Column("role_ids", postgresql.ARRAY(postgresql.UUID(as_uuid=True)), nullable=False, server_default=sa.text("'{}'")),
    )
    op.add_column(
        "invitations",
        sa.Column("branch_ids", postgresql.ARRAY(postgresql.UUID(as_uuid=True)), nullable=False, server_default=sa.text("'{}'")),
    )
    op.add_column(
        "invitations",
        sa.Column("access_all_branches", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )

    op.create_table(
        "units_of_measure",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("code", sa.String(32), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("is_integer", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("organization_id", "code", name="uq_uom_org_code"),
    )
    op.create_table(
        "product_categories",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("parent_id", postgresql.UUID(as_uuid=True)),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("path", sa.String(512), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["parent_id"], ["product_categories.id"]),
    )
    op.create_table(
        "product_tax_categories",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("default_tax_rate_id", postgresql.UUID(as_uuid=True)),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
    )
    op.create_table(
        "products",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("category_id", postgresql.UUID(as_uuid=True)),
        sa.Column("type", sa.String(16), nullable=False, server_default=sa.text("'goods'")),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("sku", sa.String(64)),
        sa.Column("barcode", sa.String(64)),
        sa.Column("uom_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tax_category_id", postgresql.UUID(as_uuid=True)),
        sa.Column("track_inventory", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("track_batches", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("track_expiry", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("track_serials", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("restricted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("attributes", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
        sa.CheckConstraint("type IN ('goods', 'service', 'bundle')", name="ck_products_type"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["category_id"], ["product_categories.id"]),
        sa.ForeignKeyConstraint(["uom_id"], ["units_of_measure.id"]),
        sa.ForeignKeyConstraint(["tax_category_id"], ["product_tax_categories.id"]),
    )
    op.execute(
        """
        CREATE UNIQUE INDEX uq_products_org_sku_active
        ON products (organization_id, sku)
        WHERE sku IS NOT NULL AND deleted_at IS NULL
        """
    )
    op.create_table(
        "product_variants",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("sku", sa.String(64)),
        sa.Column("barcode", sa.String(64)),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("attributes", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="CASCADE"),
    )
    op.create_table(
        "product_prices",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("variant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("branch_id", postgresql.UUID(as_uuid=True)),
        sa.Column("price_list_code", sa.String(32), nullable=False, server_default=sa.text("'retail'")),
        sa.Column("amount", sa.Numeric(19, 4), nullable=False),
        sa.Column("currency_code", sa.String(3), nullable=False, server_default=sa.text("'ZMW'")),
        sa.Column("effective_from", sa.Date()),
        sa.Column("effective_to", sa.Date()),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["variant_id"], ["product_variants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["branch_id"], ["branches.id"]),
    )
    op.create_table(
        "branch_products",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("branch_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("variant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("is_sellable", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("reorder_level", sa.Numeric(19, 4)),
        sa.Column("reorder_qty", sa.Numeric(19, 4)),
        sa.Column("default_warehouse_id", postgresql.UUID(as_uuid=True)),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["branch_id"], ["branches.id"]),
        sa.ForeignKeyConstraint(["variant_id"], ["product_variants.id"]),
        sa.ForeignKeyConstraint(["default_warehouse_id"], ["warehouses.id"]),
        sa.UniqueConstraint("branch_id", "variant_id", name="uq_branch_products_branch_variant"),
    )
    op.create_table(
        "product_batches",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("variant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("batch_number", sa.String(64), nullable=False),
        sa.Column("expires_on", sa.Date()),
        sa.Column("manufactured_on", sa.Date()),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["variant_id"], ["product_variants.id"]),
        sa.UniqueConstraint(
            "organization_id", "variant_id", "batch_number", name="uq_batches_org_variant_number"
        ),
    )
    op.create_table(
        "stock_balances",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("warehouse_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("variant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("batch_id", postgresql.UUID(as_uuid=True)),
        sa.Column("qty_on_hand", sa.Numeric(19, 4), nullable=False, server_default=sa.text("0")),
        sa.Column("qty_reserved", sa.Numeric(19, 4), nullable=False, server_default=sa.text("0")),
        sa.Column("avg_unit_cost", sa.Numeric(19, 4), nullable=False, server_default=sa.text("0")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["warehouse_id"], ["warehouses.id"]),
        sa.ForeignKeyConstraint(["variant_id"], ["product_variants.id"]),
        sa.ForeignKeyConstraint(["batch_id"], ["product_batches.id"]),
    )
    op.execute(
        """
        CREATE UNIQUE INDEX uq_stock_balances_wh_var_batch
        ON stock_balances (
          warehouse_id,
          variant_id,
          COALESCE(batch_id, '00000000-0000-0000-0000-000000000000'::uuid)
        )
        """
    )
    op.create_table(
        "stock_movements",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("warehouse_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("branch_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("variant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("batch_id", postgresql.UUID(as_uuid=True)),
        sa.Column("qty_delta", sa.Numeric(19, 4), nullable=False),
        sa.Column("unit_cost", sa.Numeric(19, 4), nullable=False),
        sa.Column("movement_type", sa.String(32), nullable=False),
        sa.Column("source_type", sa.String(32), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("source_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["warehouse_id"], ["warehouses.id"]),
        sa.ForeignKeyConstraint(["branch_id"], ["branches.id"]),
        sa.ForeignKeyConstraint(["variant_id"], ["product_variants.id"]),
        sa.ForeignKeyConstraint(["batch_id"], ["product_batches.id"]),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"]),
    )
    op.create_index(
        "ix_stock_movements_org_variant_time",
        "stock_movements",
        ["organization_id", "variant_id", "occurred_at"],
    )
    op.create_index("ix_stock_movements_source", "stock_movements", ["source_type", "source_id"])
    op.create_table(
        "document_sequences",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("branch_id", postgresql.UUID(as_uuid=True)),
        sa.Column("document_type", sa.String(64), nullable=False),
        sa.Column("prefix", sa.String(16), nullable=False),
        sa.Column("next_value", sa.Integer(), nullable=False, server_default=sa.text("1")),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["branch_id"], ["branches.id"]),
    )
    op.execute(
        """
        CREATE UNIQUE INDEX uq_document_sequences_org_branch_type
        ON document_sequences (
          organization_id,
          document_type,
          COALESCE(branch_id, '00000000-0000-0000-0000-000000000000'::uuid)
        )
        """
    )
    op.create_table(
        "stock_transfers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_warehouse_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("dest_warehouse_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default=sa.text("'draft'")),
        sa.Column("document_number", sa.String(64), nullable=False),
        sa.Column("shipped_at", sa.DateTime(timezone=True)),
        sa.Column("received_at", sa.DateTime(timezone=True)),
        sa.CheckConstraint(
            "status IN ('draft', 'approved', 'dispatched', 'partially_received', 'completed', 'cancelled')",
            name="ck_transfers_status",
        ),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["source_warehouse_id"], ["warehouses.id"]),
        sa.ForeignKeyConstraint(["dest_warehouse_id"], ["warehouses.id"]),
        sa.UniqueConstraint("organization_id", "document_number", name="uq_transfers_org_number"),
    )
    op.create_table(
        "stock_transfer_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("transfer_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("variant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("batch_id", postgresql.UUID(as_uuid=True)),
        sa.Column("qty_sent", sa.Numeric(19, 4), nullable=False),
        sa.Column("qty_received", sa.Numeric(19, 4), nullable=False, server_default=sa.text("0")),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["transfer_id"], ["stock_transfers.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["variant_id"], ["product_variants.id"]),
        sa.ForeignKeyConstraint(["batch_id"], ["product_batches.id"]),
    )
    op.create_table(
        "stock_counts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("warehouse_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default=sa.text("'in_progress'")),
        sa.Column("counted_at", sa.DateTime(timezone=True)),
        sa.CheckConstraint("status IN ('in_progress', 'posted', 'cancelled')", name="ck_counts_status"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["warehouse_id"], ["warehouses.id"]),
    )
    op.create_table(
        "stock_count_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("count_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("variant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("batch_id", postgresql.UUID(as_uuid=True)),
        sa.Column("system_qty", sa.Numeric(19, 4), nullable=False),
        sa.Column("counted_qty", sa.Numeric(19, 4)),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["count_id"], ["stock_counts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["variant_id"], ["product_variants.id"]),
        sa.ForeignKeyConstraint(["batch_id"], ["product_batches.id"]),
    )

    op.execute(
        """
        CREATE FUNCTION app_reject_stock_movement_mutation() RETURNS trigger
        LANGUAGE plpgsql AS $$
        BEGIN
          RAISE EXCEPTION 'stock_movements are append-only' USING ERRCODE = 'P0001';
        END;
        $$;
        """
    )
    op.execute(
        """
        CREATE TRIGGER stock_movements_immutable
        BEFORE UPDATE OR DELETE ON stock_movements
        FOR EACH ROW EXECUTE FUNCTION app_reject_stock_movement_mutation();
        """
    )
    op.execute(
        """
        CREATE FUNCTION app_stock_balance_guard() RETURNS trigger
        LANGUAGE plpgsql AS $$
        DECLARE
          allow boolean;
        BEGIN
          IF NEW.qty_on_hand < 0 THEN
            SELECT COALESCE((settings->'inventory'->>'allow_negative_stock')::boolean, false)
              INTO allow
            FROM organization_settings
            WHERE organization_id = NEW.organization_id;
            IF allow IS NOT TRUE THEN
              RAISE EXCEPTION 'negative stock denied' USING ERRCODE = '23514';
            END IF;
          END IF;
          RETURN NEW;
        END;
        $$;
        """
    )
    op.execute(
        """
        CREATE TRIGGER stock_balances_non_negative
        BEFORE INSERT OR UPDATE ON stock_balances
        FOR EACH ROW EXECUTE FUNCTION app_stock_balance_guard();
        """
    )

    for table in TENANT_TABLES:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
        op.execute(_POLICY.format(table=table))

    for code, description in (
        ("catalogue.view", "View products, variants, and prices"),
        ("catalogue.manage", "Manage products, variants, and prices"),
    ):
        op.execute(
            sa.text(
                """
                INSERT INTO permissions (id, code, description, module)
                VALUES (CAST(:id AS uuid), :code, :description, 'catalogue')
                ON CONFLICT (code) DO NOTHING
                """
            ).bindparams(id=str(new_uuid()), code=code, description=description)
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
                config=_json(pack["config_schema"]),
                modules=_json(pack["default_modules"]),
                settings=_json(pack["default_settings"]),
            )
        )

    op.execute(_BOOTSTRAP)
    op.execute(_ACCEPT)
    op.execute("GRANT SELECT, INSERT ON stock_movements TO bizpilot_app")
    op.execute("REVOKE UPDATE, DELETE ON stock_movements FROM bizpilot_app")
    op.execute("REVOKE ALL ON FUNCTION app_accept_invitation(text, uuid) FROM PUBLIC")
    op.execute("GRANT EXECUTE ON FUNCTION app_accept_invitation(text, uuid) TO bizpilot_app")
    op.execute(
        "REVOKE ALL ON FUNCTION app_bootstrap_organization(uuid, uuid, uuid, text, text, jsonb, text, text, text, text) FROM PUBLIC"
    )
    op.execute(
        "GRANT EXECUTE ON FUNCTION app_bootstrap_organization(uuid, uuid, uuid, text, text, jsonb, text, text, text, text) TO bizpilot_app"
    )
    op.execute(
        "UPDATE app_metadata SET value = '5', updated_at = now() WHERE key = 'schema_phase'"
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS stock_balances_non_negative ON stock_balances")
    op.execute("DROP TRIGGER IF EXISTS stock_movements_immutable ON stock_movements")
    op.execute("DROP FUNCTION IF EXISTS app_stock_balance_guard()")
    op.execute("DROP FUNCTION IF EXISTS app_reject_stock_movement_mutation()")
    op.execute("DROP FUNCTION IF EXISTS app_accept_invitation(text, uuid)")
    op.execute(
        "DROP FUNCTION IF EXISTS app_bootstrap_organization(uuid, uuid, uuid, text, text, jsonb, text, text, text, text)"
    )
    # Restore the Phase 3 bootstrap signature so downgrade to 0002 stays usable.
    op.execute(
        """
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
        BEGIN
          RAISE EXCEPTION 'restored phase-3 bootstrap is a stub; upgrade to head';
        END;
        $$;
        """
    )
    for table in reversed(TENANT_TABLES):
        op.execute(f"DROP POLICY IF EXISTS {table}_tenant_isolation ON {table}")
        op.drop_table(table)
    op.drop_column("invitations", "access_all_branches")
    op.drop_column("invitations", "branch_ids")
    op.drop_column("invitations", "role_ids")
    op.execute(
        "UPDATE app_metadata SET value = '3', updated_at = now() WHERE key = 'schema_phase'"
    )


def _json(value: object) -> str:
    import json

    return json.dumps(value)
