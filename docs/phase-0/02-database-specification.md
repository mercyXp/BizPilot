# Phase 0 — Database Specification

**Engine:** PostgreSQL 16  
**ORM:** SQLAlchemy 2.x (mapped, typed)  
**Migrations:** Alembic  
**PKs:** UUID (UUIDv7 preferred for time-ordering; fallback uuid4)  
**Time:** `TIMESTAMPTZ` UTC  
**Money:** `NUMERIC(19,4)`  
**Quantities:** `NUMERIC(19,4)`  
**Percent/rates:** `NUMERIC(10,6)`  
**Soft delete:** master data only (`deleted_at`); ledgers and movements are immutable  

Conventions on tenant tables: `organization_id NOT NULL`, RLS forced, index `(organization_id, …)`.

Branch-scoped operational tables also have `branch_id`.

`created_at`, `updated_at`, `created_by_user_id` on mutable masters. Ledgers: `created_at`, `created_by_user_id` only.

---

## 1. Entity relationship (logical)

### Identity, tenancy, authz

```
users ||--o{ user_sessions
users ||--o{ organization_memberships
organizations ||--o{ organization_memberships
organizations ||--o{ branches
organizations ||--o{ organization_settings
industries ||--o{ organizations
organization_memberships ||--o{ membership_roles
organization_memberships ||--o{ membership_branches
roles ||--o{ membership_roles
roles ||--o{ role_permissions
permissions ||--o{ role_permissions
organization_memberships ||--o{ user_permission_overrides
organizations ||--o{ invitations
branches ||--o{ membership_branches
```

### Catalogue and inventory

```
organizations ||--o{ product_categories
product_categories ||--o{ products
units_of_measure ||--o{ products
products ||--o{ product_variants
products ||--o{ product_batches
tax_rates ||--o{ product_tax_categories
product_variants ||--o{ product_prices
product_variants ||--o{ branch_products
branches ||--o{ warehouses
warehouses ||--o{ stock_balances
product_variants ||--o{ stock_balances
stock_movements }o--|| warehouses
stock_transfers ||--o{ stock_transfer_items
stock_counts ||--o{ stock_count_items
```

### Sales, purchasing, CRM

```
customers ||--o{ sales
pos_sessions ||--o{ sales
sales ||--o{ sale_items
sales ||--o{ payments
payments ||--o{ payment_allocations
sales ||--o{ refunds
refunds ||--o{ refund_items
suppliers ||--o{ purchase_orders
purchase_orders ||--o{ purchase_order_items
purchase_orders ||--o{ goods_received_notes
goods_received_notes ||--o{ goods_received_items
suppliers ||--o{ supplier_invoices
```

### Accounting

```
organizations ||--o{ fiscal_years ||--o{ accounting_periods
organizations ||--o{ chart_of_accounts
journal_entries ||--o{ journal_lines
journal_lines }o--|| chart_of_accounts
journal_entries }o--|| accounting_periods
bank_accounts ||--o{ bank_transactions
bank_reconciliations ||--o{ reconciliation_items
```

### Payroll, AI, SaaS

```
organizations ||--o{ employees ||--o{ payroll_items
payroll_runs ||--o{ payroll_items
ai_conversations ||--o{ ai_messages
ai_messages ||--o{ ai_tool_calls
subscription_plans ||--o{ subscriptions
organizations ||--|| subscriptions
```

---

## 2. Table specifications

RLS: **T** = tenant isolated. **G** = global/platform. **S** = seed/catalog.

### 2.1 Identity and tenancy

#### users (G)

Purpose: global login identity.  
Columns: `id`, `email` unique, `password_hash`, `full_name`, `phone`, `email_verified_at`, `platform_role` (`null | super_admin`), `is_active`, `totp_secret_encrypted` null, `created_at`, `updated_at`.  
Notes: never store org_id here.

#### user_sessions (G)

Purpose: refresh-token families and revocation.  
Columns: `id`, `user_id` FK, `token_family_id`, `refresh_token_hash`, `expires_at`, `rotated_from_id` null, `revoked_at`, `user_agent`, `ip`, `created_at`.  
Index: `(user_id, revoked_at)`, `refresh_token_hash` unique.

#### industries (S)

Purpose: industry packs.  
Columns: `id`, `code` unique (`grocery`, `pharmacy`, …), `name`, `config_schema` JSONB, `default_modules` JSONB, `default_settings` JSONB, `is_active`.

#### organizations (G with access via membership)

Purpose: tenant root.  
Columns: `id`, `name`, `legal_name`, `industry_id` FK, `country_code` default `ZM`, `base_currency_code` default `ZMW`, `timezone` default `Africa/Lusaka`, `status` (`active | suspended | pending`), `created_at`, `updated_at`.  
No RLS on the table for “list my orgs”; **all business child tables** use RLS. Application still never returns orgs the user does not belong to (and platform admin list is a platform route).

#### organization_settings (T)

Purpose: key-value/JSON settings (modules enabled, POS, inventory policies, document sequences config).  
Columns: `id`, `organization_id` unique, `settings` JSONB, `updated_at`.

#### organization_locales (T)

Purpose: language preference.  
Columns: `id`, `organization_id`, `default_locale` default `en`, `enabled_locales` text[].

#### branches (T)

Purpose: physical/logical locations.  
Columns: `id`, `organization_id`, `code`, `name`, `address_json`, `phone`, `is_active`, `created_at`.  
Unique: `(organization_id, code)`.

#### warehouses (T)

Purpose: stock locations.  
Columns: `id`, `organization_id`, `branch_id` FK, `code`, `name`, `is_default`, `is_active`.  
Unique: `(organization_id, code)`. Partial unique: one default warehouse per branch.

#### organization_memberships (T-ish: org_id RLS)

Purpose: user↔org.  
Columns: `id`, `organization_id`, `user_id`, `status`, `access_all_branches` bool, `created_at`.  
Unique: `(organization_id, user_id)`.

#### membership_branches (T)

Purpose: branch grants when not all-branches.  
Columns: `id`, `organization_id`, `membership_id`, `branch_id`.  
Unique: `(membership_id, branch_id)`.

#### invitations (T)

Columns: `id`, `organization_id`, `email`, `role_ids` UUID[], `branch_ids` UUID[], `token_hash`, `expires_at`, `accepted_at`, `invited_by_user_id`.

### 2.2 Authorization

#### permissions (S)

Columns: `id`, `code` unique, `description`, `module`.

#### roles (T)

Columns: `id`, `organization_id`, `code`, `name`, `is_system` (seeded templates), `created_at`.  
Unique: `(organization_id, code)`.

#### role_permissions (T)

Columns: `id`, `organization_id`, `role_id`, `permission_id`. Unique `(role_id, permission_id)`.

#### membership_roles (T)

Columns: `id`, `organization_id`, `membership_id`, `role_id`. Unique `(membership_id, role_id)`.

#### user_permission_overrides (T)

Columns: `id`, `organization_id`, `membership_id`, `permission_id`, `effect` (`allow | deny`). Unique `(membership_id, permission_id)`.

### 2.3 Catalogue

#### units_of_measure (T)

Columns: `id`, `organization_id`, `code`, `name`, `is_integer`. Unique `(organization_id, code)`.

#### uom_conversions (T)

Columns: `id`, `organization_id`, `from_uom_id`, `to_uom_id`, `factor` NUMERIC. Unique pair.

#### product_categories (T)

Columns: `id`, `organization_id`, `parent_id` self FK null, `name`, `path`, `is_active`.

#### product_tax_categories (T)

Columns: `id`, `organization_id`, `name`, `default_tax_rate_id` null.

#### products (T)

Columns: `id`, `organization_id`, `category_id`, `type` (`goods | service | bundle`), `name`, `description`, `sku` null, `barcode` null, `uom_id`, `tax_category_id`, `track_inventory` bool, `track_batches` bool, `track_expiry` bool, `track_serials` bool default false, `restricted` bool, `attributes` JSONB default `{}`, `is_active`, `deleted_at`.  
Unique partial: `(organization_id, sku) WHERE sku IS NOT NULL AND deleted_at IS NULL`.

#### product_variants (T)

Columns: `id`, `organization_id`, `product_id`, `sku`, `barcode`, `name`, `attributes` JSONB (size, colour), `is_active`.  
Unique sku per org when present.

#### product_prices (T)

Columns: `id`, `organization_id`, `variant_id`, `branch_id` null (null = org default), `price_list_code` default `retail`, `amount`, `currency_code`, `effective_from`, `effective_to`.  
Lookup: most specific branch + date.

#### branch_products (T)

Columns: `id`, `organization_id`, `branch_id`, `variant_id`, `is_sellable`, `reorder_level`, `reorder_qty`, `default_warehouse_id`. Unique `(branch_id, variant_id)`.

### 2.4 Inventory

#### stock_balances (T)

Purpose: current qty and weighted-average cost.  
Columns: `id`, `organization_id`, `warehouse_id`, `variant_id`, `batch_id` null, `qty_on_hand`, `qty_reserved`, `avg_unit_cost`, `updated_at`.  
Unique: `(warehouse_id, variant_id, COALESCE(batch_id, '00000000-…'))` — use `batch_id` with sentinel or partial unique indexes for null batches.

#### stock_movements (T, append-only)

Columns: `id`, `organization_id`, `warehouse_id`, `branch_id`, `variant_id`, `batch_id` null, `qty_delta` (signed), `unit_cost`, `movement_type`, `source_type`, `source_id`, `occurred_at`, `created_by_user_id`.  
**No updates.** Index `(organization_id, variant_id, occurred_at)`, `(source_type, source_id)`.

#### stock_transfers (T)

Columns: `id`, `organization_id`, `source_warehouse_id`, `dest_warehouse_id`, `status`, `document_number`, `shipped_at`, `received_at`. Unique `(organization_id, document_number)`.

#### stock_transfer_items (T)

Columns: `id`, `organization_id`, `transfer_id`, `variant_id`, `batch_id`, `qty_sent`, `qty_received`.

#### stock_counts (T)

Columns: `id`, `organization_id`, `warehouse_id`, `status`, `counted_at`.

#### stock_count_items (T)

Columns: `id`, `organization_id`, `count_id`, `variant_id`, `batch_id`, `system_qty`, `counted_qty`.

#### product_batches (T)

Columns: `id`, `organization_id`, `variant_id`, `batch_number`, `expires_on`, `manufactured_on`. Unique `(organization_id, variant_id, batch_number)`.

### 2.5 Customers and suppliers

#### customers (T)

Columns: `id`, `organization_id`, `code`, `name`, `phone`, `email`, `tax_id`, `address_json`, `is_active`. Unique `(organization_id, code)`.

#### customer_addresses (T)

Columns: `id`, `organization_id`, `customer_id`, `label`, `address_json`, `is_default`.

#### customer_credit_accounts (T)

Columns: `id`, `organization_id`, `customer_id` unique, `credit_limit`, `status`. Balance is **derived** from invoices/payments, with optional cached `balance` updated in transaction.

#### customer_loyalty_accounts (T)

Foundation: `id`, `organization_id`, `customer_id`, `points_balance`.

#### loyalty_transactions (T, append-only)

Columns: `id`, `organization_id`, `account_id`, `delta`, `source_type`, `source_id`.

#### customer_notes (T)

Columns: `id`, `organization_id`, `customer_id`, `body`, `created_by_user_id`, `created_at`.

#### suppliers (T)

Columns: `id`, `organization_id`, `code`, `name`, `phone`, `email`, `tax_id`, `address_json`, `payment_terms_days`, `is_active`.

### 2.6 Sales and POS

#### pos_sessions (T)

Columns: `id`, `organization_id`, `branch_id`, `warehouse_id`, `opened_by_user_id`, `closed_by_user_id`, `status`, `opening_float`, `closing_counted_cash`, `opened_at`, `closed_at`.

#### pos_cash_movements (T)

Columns: `id`, `organization_id`, `session_id`, `type` (`in | out | sale | refund | variance`), `amount`, `reason`.

#### sales (T)

Columns: `id`, `organization_id`, `branch_id`, `session_id` null (back-office sale), `customer_id` null, `document_number`, `status` (`draft | awaiting_payment | completed | voided | refunded | partially_refunded`), `sale_type` (`pos | invoice`), `subtotal`, `discount_total`, `tax_total`, `total`, `currency_code`, `idempotency_key`, `completed_at`.  
Unique `(organization_id, document_number)`, unique `(organization_id, idempotency_key)` where key not null.

#### sale_items (T)

Columns: `id`, `organization_id`, `sale_id`, `variant_id`, `description`, `qty`, `uom_id`, `unit_price`, `discount_amount`, `tax_rate_id`, `tax_amount`, `line_total`.

#### payments (T)

Columns: `id`, `organization_id`, `sale_id` null, `customer_id` null, `method` (`cash | mobile_money | card | bank_transfer | store_credit`), `status` (`pending | completed | failed | cancelled`), `amount`, `provider`, `provider_ref`, `received_at`.

#### payment_allocations (T)

Columns: `id`, `organization_id`, `payment_id`, `source_type` (`sale | invoice`), `source_id`, `amount`.

#### refunds (T)

Columns: `id`, `organization_id`, `sale_id`, `reason`, `status`, `total`, `restock`, `idempotency_key`.

#### refund_items (T)

Columns: `id`, `organization_id`, `refund_id`, `sale_item_id`, `qty`, `amount`.

#### receipts (T)

Columns: `id`, `organization_id`, `sale_id`, `document_number`, `payload_json`, `pdf_object_key` null.

### 2.7 Purchasing

#### purchase_requisitions (T)

Columns: `id`, `organization_id`, `branch_id`, `status`, `requested_by`, `document_number`.

#### purchase_requisition_items (T)

Columns: `id`, `organization_id`, `requisition_id`, `variant_id`, `qty`.

#### purchase_orders (T)

Columns: `id`, `organization_id`, `branch_id`, `supplier_id`, `status` (`draft | pending_approval | approved | sent | partial | received | cancelled`), `document_number`, `ordered_at`, `expected_at`.  
Constraint: creating a PO does not touch stock.

#### purchase_order_items (T)

Columns: `id`, `organization_id`, `purchase_order_id`, `variant_id`, `qty_ordered`, `qty_received`, `unit_cost`.

#### goods_received_notes (T)

Columns: `id`, `organization_id`, `purchase_order_id`, `warehouse_id`, `status`, `document_number`, `received_at`.

#### goods_received_items (T)

Columns: `id`, `organization_id`, `grn_id`, `purchase_order_item_id`, `qty_accepted`, `qty_rejected`.

#### supplier_invoices (T)

Columns: `id`, `organization_id`, `supplier_id`, `purchase_order_id` null, `document_number`, `status`, `subtotal`, `tax_total`, `total`, `due_at`.

#### supplier_payments (T)

Columns: `id`, `organization_id`, `supplier_id`, `amount`, `status`, `method`, `paid_at`.

### 2.8 Accounting

#### fiscal_years (T)

Columns: `id`, `organization_id`, `name`, `starts_on`, `ends_on`, `status`.

#### accounting_periods (T)

Columns: `id`, `organization_id`, `fiscal_year_id`, `name`, `starts_on`, `ends_on`, `status` (`open | closed | locked`).

#### chart_of_accounts (T)

Columns: `id`, `organization_id`, `code`, `name`, `type` (`asset | liability | equity | income | expense`), `subtype`, `parent_id`, `is_postable`, `is_system`, `currency_code`. Unique `(organization_id, code)`.

#### tax_rates (T)

Columns: `id`, `organization_id`, `code`, `name`, `rate`, `inclusive`, `effective_from`, `effective_to`.

#### journal_entries (T, posted immutable)

Columns: `id`, `organization_id`, `period_id`, `entry_number`, `status`, `source_type`, `source_id`, `reverses_journal_id` null, `description`, `posted_at`, `idempotency_key`.  
Check: application + trigger: posted ⇒ balanced.  
Trigger: prevent UPDATE/DELETE of posted rows (except `status` to `reversed` metadata — prefer no column changes; set `reversed_by_id` on original only via controlled function).

#### journal_lines (T)

Columns: `id`, `organization_id`, `journal_id`, `account_id`, `branch_id`, `debit`, `credit`, `party_type` null, `party_id` null, `memo`.  
Check: `(debit = 0 AND credit > 0) OR (credit = 0 AND debit > 0)`.

#### bank_accounts (T)

Columns: `id`, `organization_id`, `account_id` (GL), `name`, `bank_name`, `account_number_masked`, `currency_code`.

#### bank_transactions (T)

Columns: `id`, `organization_id`, `bank_account_id`, `posted_on`, `amount`, `description`, `external_ref`, `status`.

#### bank_reconciliations (T)

Columns: `id`, `organization_id`, `bank_account_id`, `statement_date`, `status`.

#### reconciliation_items (T)

Columns: `id`, `organization_id`, `reconciliation_id`, `bank_transaction_id`, `journal_line_id` null.

#### expenses (T)

Columns: `id`, `organization_id`, `branch_id`, `vendor_name`, `supplier_id` null, `amount`, `tax_amount`, `status`, `incurred_on`, `payment_method`, `document_number`.

#### expense_lines (T)

Columns: `id`, `organization_id`, `expense_id`, `account_id`, `amount`, `memo`.

#### document_sequences (T)

Purpose: gap-safe numbering.  
Columns: `id`, `organization_id`, `branch_id` null, `document_type`, `prefix`, `next_value`. Unique `(organization_id, branch_id, document_type)`. Updates with row lock.

### 2.9 Employees and payroll

#### departments (T)

Columns: `id`, `organization_id`, `name`.

#### employees (T)

Columns: `id`, `organization_id`, `branch_id` null, `user_id` null, `employee_number`, `full_name`, `hire_on`, `status`, `department_id`, `job_title`. Unique `(organization_id, employee_number)`.

#### attendance_records (T)

Columns: `id`, `organization_id`, `employee_id`, `work_on`, `status`. Unique `(employee_id, work_on)` unless multiple shifts.

#### employee_shifts (T)

Columns: `id`, `organization_id`, `employee_id`, `starts_at`, `ends_at`, `branch_id`.

#### leave_requests (T)

Columns: `id`, `organization_id`, `employee_id`, `type`, `starts_on`, `ends_on`, `status`.

#### payroll_components (T)

Columns: `id`, `organization_id`, `code`, `name`, `kind` (`earning | deduction | employer_contribution`), `calculation` JSONB (percent of base, fixed), `effective_from`, `effective_to`.  
Statutory components stored here — **not** in code constants.

#### payroll_periods (T)

Columns: `id`, `organization_id`, `starts_on`, `ends_on`, `status`.

#### payroll_runs (T)

Columns: `id`, `organization_id`, `period_id`, `status`, `processed_at`, `idempotency_key`.

#### payroll_items (T)

Columns: `id`, `organization_id`, `run_id`, `employee_id`, `component_id`, `amount`.

### 2.10 AI and audit

#### ai_conversations (T)

Columns: `id`, `organization_id`, `user_id`, `branch_id` null, `title`, `created_at`.

#### ai_messages (T)

Columns: `id`, `organization_id`, `conversation_id`, `role`, `content`, `data_mode`, `created_at`.

#### ai_tool_calls (T)

Columns: `id`, `organization_id`, `message_id`, `tool_name`, `arguments_json`, `result_json`, `status`, `permission_code`.

#### ai_action_approvals (T)

Columns: `id`, `organization_id`, `tool_call_id`, `status` (`pending | approved | rejected | expired`), `decided_by`, `decided_at`.

#### ai_action_logs (T)

Columns: `id`, `organization_id`, `tool_call_id`, `outcome`.

#### audit_logs (T, append-only)

Columns: `id`, `organization_id` null (null only for platform events), `actor_user_id`, `action`, `entity_type`, `entity_id`, `before_json`, `after_json`, `ip`, `created_at`.  
No UPDATE/DELETE granted to app role.

#### outbox_events (T)

Columns: `id`, `organization_id`, `event_type`, `payload_json`, `status` (`pending | published | failed`), `attempts`, `available_at`, `created_at`.

#### idempotency_keys (T)

Columns: `id`, `organization_id`, `key`, `request_hash`, `response_json`, `created_at`. Unique `(organization_id, key)`.

### 2.11 SaaS platform (not in tenant COA)

#### subscription_plans (G)

Columns: `id`, `code`, `name`, `limits_json`, `features_json`, `is_active`.

#### subscriptions (G)

Columns: `id`, `organization_id` unique, `plan_id`, `status`, `current_period_end`.

#### subscription_features / subscription_limits

May be JSON on plan; extra tables only if querying requires it. Prefer JSON on plan + `usage_records`.

#### usage_records (T or G with org_id)

Columns: `id`, `organization_id`, `metric` (`ai_tokens`, `pos_receipts`, …), `quantity`, `period_start`.

#### platform_billing_events (G)

Columns: `id`, `organization_id`, `type`, `amount`, `currency_code`, `provider_ref`, `occurred_at`.  
**Never** posted to the tenant’s `journal_entries`.

### 2.12 Localization

#### translation_resources (G)

Columns: `id`, `locale`, `key`, `value`, `provenance` (`system | professional`), unique `(locale, key)`.

---

## 3. Supporting rules

### Document numbers

Allocated from `document_sequences` with `SELECT … FOR UPDATE` in the business transaction (or `INSERT … ON CONFLICT` increment).

### Integrity triggers (Phase 1–8 as tables appear)

1. `journal_entries` posted: sum debit = sum credit.  
2. Disallow UPDATE/DELETE on `journal_lines` of posted journals, `stock_movements`, `audit_logs`.  
3. `stock_balances.qty_on_hand` cannot go negative unless org setting `allow_negative_stock`.  
4. Sale completed ⇒ at least one payment allocation or credit sale flag.  
5. GRN cannot exceed PO remaining unless over-receive allowed.

### Indexes (minimum)

Every tenant table: `organization_id`.  
FK columns indexed.  
Time-series: `(organization_id, occurred_at DESC)` on movements, sales, journals.  
Barcodes: `(organization_id, barcode)` on products/variants.

### What was omitted on purpose

- Separate `pharmacy_products` table  
- Per-tenant database  
- FIFO layer table (reserved in docs only)  
- Multi-currency journals  
- Soft delete on journals  

If a table has no purpose beyond “might need it”, it is not listed. `purchase_requisition_items`, `expense_lines`, `uom_conversions`, `outbox_events`, `idempotency_keys`, `document_sequences` were added as necessary supporting tables.
