# Phase 0 — AI, API, and Frontend Structure

## 1. Grok AI orchestration

Grok is a **reasoning client**, not a data plane.

```
User message
  → AuthN + TenantContext + permission `ai.use`
  → Load conversation (org-scoped)
  → Build tool list filtered by user permissions and subscription
  → Send to Grok: system prompt + tool schemas + **no raw DB**
  → For each tool call: validate name/args schema → authorize → execute domain service → return **tool result JSON**
  → Model drafts user-visible answer
  → Orchestrator **grounds** numeric claims: if a figure did not come from a tool result this turn, mark as unverified / omit
  → Persist messages, tool calls, token usage
  → Sensitive tools (`create_*`, `draft` that will become records) require `ai.act` and `ai_action_approvals` before commit
```

### 1.1 System rules (enforced in code, not only prompt)

- Tools always run with the user’s `TenantContext`.
- No `execute_sql`, no generic “query table”.
- No tool to post journals, close periods, initiate payouts, delete audit, or change memberships.
- Write tools create **drafts** (PO, invoice, reminder) until the user confirms.
- Usage: `usage_records` against plan limits; over-quota → 402.
- Prompt injection: tool args validated by Pydantic; the model cannot set `organization_id`.

### 1.2 Initial tools

| Tool | Permission | Side effect |
| --- | --- | --- |
| `get_sales_summary` | `sales.view` or `reports.view` | read |
| `compare_sales_periods` | `reports.view` | read |
| `compare_branch_performance` | `reports.view` | read; only allowed branches |
| `get_inventory_status` | `inventory.view` | read |
| `get_low_stock_products` | `inventory.view` | read |
| `get_expense_summary` | `accounting.reports.view` or expenses view | read |
| `get_customer_balance` | `customers.manage` or AR view | read |
| `get_supplier_balance` | `purchases.view` or AP view | read |
| `generate_business_report` | `reports.view` | read + stored document |
| `create_purchase_order_draft` | `purchases.create` + `ai.act` | draft PO |
| `create_invoice_draft` | `sales.create` + `ai.act` | draft invoice |
| `draft_payment_reminder` | `customers.manage` + `ai.act` | draft notification, not send until confirm |

Verified vs suggestion: UI and API flag `data_mode: verified | model_commentary`.

### 1.3 Grok API

Use official xAI/Grok API as documented at implementation time (Phase 10). Phase 0 does not invent URLs. The orchestrator is an adapter: `LLMClient.complete(messages, tools)`.

Secrets: `GROK_API_KEY` on the server only.

## 2. API surface (logical)

All under `/api/v1`. Resource names are plural. Tenant header required except auth and platform-admin-as-user org list.

| Area | Examples |
| --- | --- |
| Health | `GET /health`, `GET /health/ready` (db + redis) |
| Auth | `/auth/register`, `/login`, `/logout`, `/refresh`, `/verify-email`, `/password-reset` |
| Me | `/me`, `/me/memberships` |
| Orgs | `/organizations`, `/organizations/{id}/invitations` |
| Branches | `/branches`, `/warehouses` |
| RBAC | `/roles`, `/permissions`, `/memberships/{id}/roles` |
| Catalogue | `/products`, `/variants`, `/categories`, `/uom` |
| Inventory | `/stock-balances`, `/stock-movements`, `/stock-transfers`, `/stock-counts`, `/adjustments` |
| POS | `/pos/sessions`, `/pos/sessions/{id}/sales` |
| Sales | `/sales`, `/sales/{id}/refunds`, `/receipts/{id}` |
| Customers | `/customers`, `/customers/{id}/credit` |
| Purchasing | `/suppliers`, `/purchase-orders`, `/goods-receipts`, `/supplier-invoices` |
| Accounting | `/accounts`, `/journals`, `/periods`, `/reports/trial-balance`, … |
| Employees | `/employees`, `/leave-requests`, `/payroll-runs` |
| AI | `/ai/conversations`, `/ai/conversations/{id}/messages`, `/ai/approvals/{id}` |
| Platform | `/platform/organizations`, `/platform/plans` |

OpenAPI generated from FastAPI. Frontend consumes `/api/v1/openapi.json` in development.

## 3. Frontend information architecture

### 3.1 Shell

- Left nav (collapsible), top bar: org selector, branch selector, user menu, notifications
- Nav items filtered by **enabled modules ∩ permissions**
- Mobile: bottom or hamburger nav; POS optimized for tablet width

### 3.2 Primary routes (`(app)`)

| Nav item | Route | Default permission |
| --- | --- | --- |
| Dashboard | `/` | authenticated membership |
| Point of Sale | `/pos` | `sales.create` |
| Sales | `/sales` | `sales.view` |
| Products | `/products` | catalogue view |
| Inventory | `/inventory` | `inventory.view` |
| Purchasing | `/purchasing` | purchases view |
| Customers | `/customers` | customers |
| Suppliers | `/suppliers` | purchases |
| Accounting | `/accounting` | accounting view |
| Expenses | `/expenses` | expenses |
| Employees | `/employees` | employees |
| Payroll | `/payroll` | payroll |
| Reports | `/reports` | reports |
| AI Assistant | `/assistant` | `ai.use` |
| Branches | `/branches` | `branches.manage` or view |
| Settings | `/settings` | `org.settings` or own profile |

Platform: `/platform/*`.

Auth: `/sign-in`, `/sign-up`, `/verify-email`, `/reset-password`.

Onboarding: `/onboarding` — create org, industry, currency ZMW, timezone (Africa/Lusaka default), first branch, first warehouse, optional invite.

### 3.3 UX standards

- Professional SaaS: clear type, consistent spacing, shadcn components
- Tables: sort, filter, pagination, empty/error/loading
- Destructive actions: dialog confirm
- Toasts for success/failure; form-level Zod errors
- Charts: Recharts on dashboard/reports
- POS: large targets, barcode input focus, cart always visible

### 3.4 Dashboard widgets (permission and industry filtered)

Sales today vs period, low stock, open sessions, cash position (if accounting), AR/AP snapshot, branch comparison (if multi-branch), AI suggested attention list (from verified tools, not hallucinations).

## 4. Localization architecture

- `next-intl` or equivalent **later** (Phase 12). Phase 1–11 ship English message keys in source.
- Resource tables: `translation_resources` (locale, key, value, provenance `system | professional`)
- Org `locale`, `date_format`, `number_format`; currency format from currency code
- Do not machine-translate production Zambian languages without professional review flag

## 5. Document and receipt formatting

Templates stored as org settings + industry defaults. Fields reserved for ZRA (taxpayer IDs, QR placeholders) **without** claiming certification. PDF renderer in documents module; files in S3.
