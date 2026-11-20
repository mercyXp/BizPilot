# Phase 0 — System Architecture

## 1. Style: modular monolith

One deployable **API** (FastAPI) and one deployable **web app** (Next.js). One PostgreSQL database. Redis + Celery for jobs. S3-compatible storage for files.

Modules are **Python packages with explicit public services**. They may share the database and a request-scoped `TenantContext`. They must not import another module’s tables or repositories directly except through published service interfaces (or shared kernel types).

```
┌─────────────────────────────────────────────────────────────┐
│                     Next.js (App Router)                    │
│  Auth pages · App shell · Module routes · TanStack Query    │
└────────────────────────────┬────────────────────────────────┘
                             │ HTTPS / REST /api/v1
┌────────────────────────────▼────────────────────────────────┐
│                     API Gateway layer                       │
│  AuthN · TenantContext · RBAC · Rate limit · Idempotency    │
├─────────────────────────────────────────────────────────────┤
│ Identity │ Tenancy │ AuthZ │ Org/Industry │ Catalogue       │
│ Inventory│ Sales/POS│ Purchasing │ CRM │ Accounting Engine  │
│ Payroll  │ Reporting│ AI Orchestrator │ Notifications       │
│ Platform Billing │ Integrations (adapters) │ Audit/Outbox   │
├─────────────────────────────────────────────────────────────┤
│ SQLAlchemy 2 · PostgreSQL + RLS · Redis · Celery · S3       │
└─────────────────────────────────────────────────────────────┘
```

Next.js does **not** own business writes. Server Actions, if used, only proxy to the API with the user token. This keeps a single authorization and posting path.

## 2. Proposed repository layout (Phase 1)

```
BizPilot/
  docs/                      # this technical record
  frontend/                  # Next.js app
  backend/                   # FastAPI app
    app/
      main.py
      api/v1/                # routers only
      core/                  # config, logging, security, db, errors
      modules/<name>/        # domain packages
      workers/               # Celery tasks
    alembic/
    tests/
  docker-compose.yml         # Postgres, Redis, API, worker, web (Phase 1+)
```

No extra packages (pnpm workspaces, service meshes) until needed.

## 3. Shared kernel

Cross-cutting types used by every module:

- `TenantContext`: `user_id`, `organization_id`, `membership_id`, `branch_id | None`, `permissions: set[str]`, `is_platform_admin`
- `Money`: `Decimal` + `currency_code` (org functional currency enforced)
- `AuditActor`: user or system job
- `SourceDocumentRef`: `(document_type, document_id)`
- `IdempotencyKey`
- Result/error types mapped to HTTP (validation, forbidden, conflict, unprocessable)

## 4. Module boundaries

| Module | Owns | Must not |
| --- | --- | --- |
| `identity` | users, sessions, password/email flows | org business data |
| `tenancy` | organizations, memberships, invitations, branches access lists | products, journals |
| `authorization` | roles, permissions, overrides, branch grants | feature business rules |
| `organization` | org profile, settings, fiscal calendar, industry assignment | |
| `industry` | pack registry, JSON schemas, default module flags | forked entity tables |
| `catalogue` | products, variants, categories, UoM, prices | stock qty (inventory owns qty) |
| `inventory` | warehouses, balances, movements, transfers, counts, batches | journals |
| `sales` | POS sessions, sales, payments, refunds, receipts | posting math |
| `purchasing` | suppliers, PR/PO/GRN, supplier invoices/payments | posting math |
| `crm` | customers, credit accounts, loyalty foundation | |
| `expenses` | expense documents | posting math |
| `accounting` | COA, periods, journals, banks, tax rates, reports, **posting engine** | POS UI |
| `payroll` | employees, attendance, leave, payroll runs | hardcoded statutory rates |
| `reporting` | dashboards/read models, exports | write paths for money/stock |
| `ai` | conversations, tool dispatch, approvals, usage | raw SQL, unrestricted DB |
| `notifications` | outbox consumers, email/SMS adapters | |
| `documents` | PDF generation, object storage keys | |
| `platform_billing` | plans, subscriptions, usage, platform invoices | tenant COA |
| `integrations` | ZRA, mobile money, banks — adapters | domain entities |
| `audit` | audit_logs append-only | |

## 5. Module dependency map

Allowed compile-time / import direction (arrows mean “depends on”):

```
identity
tenancy → identity
authorization → tenancy, identity
organization → tenancy, industry
industry → (kernel only)
catalogue → organization
inventory → catalogue, organization
crm → organization
sales → catalogue, inventory, crm, accounting(posting interface)
purchasing → catalogue, inventory, accounting(posting interface)
expenses → accounting(posting interface)
payroll → organization, accounting(posting interface)
accounting → organization, tenancy
reporting → (read services of domain modules; no writes)
ai → (tool facades on domain modules)
notifications → audit/outbox
platform_billing → tenancy (org id only)
integrations → sales/accounting document interfaces
```

**Cycle break:** domain modules depend on `accounting.PostingEngine` as an **interface** defined in a thin `app/modules/accounting/contracts.py` (or `app/kernel/posting.py`). The implementation lives in accounting. Sales never imports journal table models.

Inventory exposes `InventoryService.receive / dispatch / adjust` only. Sales and purchasing call that service inside the same database transaction as their document write.

## 6. Request lifecycle

1. Authenticate JWT → `user_id`.
2. Resolve `X-Organization-Id` (required for tenant routes) against `organization_memberships` (active).
3. Resolve optional `X-Branch-Id` against `membership_branches` (or all branches if membership flag `all_branches`).
4. Load permission set (roles ∪ overrides) minus denials.
5. `SET LOCAL app.current_organization_id` and `app.current_user_id` for RLS.
6. Authorize permission for the route/command.
7. Execute service in a transaction; write outbox + audit.
8. Commit. Celery reads outbox.

Platform admin routes skip tenant RLS by using a dedicated DB role **only** after `is_platform_admin` is verified, and still never mix platform queries with tenant document updates in the same session without resetting context.

## 7. Background jobs

Celery tasks:

- Email verification, password reset, invitations
- Outbox dispatcher (notifications, webhooks, ZRA later)
- Report generation / PDF
- AI long-running tool aggregations
- Subscription usage rollups
- Low-stock alert evaluation
- Payment provider reconciliation polls (adapter)

Jobs receive `organization_id` and set RLS context at start. A job without tenant context cannot query tenant tables.

## 8. Caching

Redis:

- Refresh-token family / session revocation set
- Rate-limit counters
- Permission set cache keyed by `membership_id` (invalidate on role change)
- Idempotency response cache (short TTL) in addition to DB uniqueness
- Optional read-through for tax rates and COA (invalidate on write)

Do not cache tenant lists across users.

## 9. API architecture

- Prefix: `/api/v1`
- JSON only for v1
- Errors: `{ "error": { "code": "permission_denied", "message": "...", "details": [] } }` — no stack traces
- Pagination: cursor or limit/offset with max limit; list endpoints default 50, max 200
- Filtering: explicit query params, not arbitrary SQL
- `Idempotency-Key` required on: sales complete, payments, refunds, journal post, stock adjust, GRN post, payroll run
- File uploads: presign to S3 or upload via API with MIME/size checks; store only object keys in DB

Versioning: breaking changes go to `/api/v2`. Additive fields are allowed in v1.

## 10. Frontend application structure

Route groups:

- `(marketing)` — later
- `(auth)` — sign in/up, reset, verify
- `(app)` — authenticated tenant shell: org + branch switchers, module nav
- `(platform)` — super admin

Data: TanStack Query against FastAPI. Forms: RHF + Zod matching API schemas where practical (OpenAPI codegen may be added later; not required in Phase 1).

## 11. Environment topology

| Env | Purpose |
| --- | --- |
| local | docker-compose Postgres 16, Redis, Mailhog/dev SMTP, MinIO |
| staging | production-like RLS, no real money movers until adapters certified |
| production | managed Postgres, Redis, object storage, secrets manager |

## 12. What we are deliberately not building

- GraphQL (REST is specified)
- Event sourcing as the system of record (outbox is for integration, not replacing tables)
- Separate database per tenant (operationally heavier than required at this stage; RLS + `organization_id` is the isolation model)
- Direct Grok-to-database
