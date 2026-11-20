# BizPilot development setup

Phase 1 runs a Next.js app, a FastAPI API, PostgreSQL, and an optional Redis server. Phases 2–9 add authentication, RBAC, onboarding, catalogue, inventory, POS, purchasing, accounting, and payroll on that same API.

## Prerequisites

- Python 3.12+
- Node.js 20+
- PostgreSQL 16+ client/server binaries (Docker **or** a local install)

Docker is optional. This machine’s Phase 1 path uses a **project-local PostgreSQL cluster** on port `55432` so it does not collide with other Postgres instances.

## Environment

```powershell
copy .env.example .env
```

Do not commit `.env`. `SECRET_KEY` in the example is for local development only.

`REDIS_URL=memory://` is allowed in development when Redis is not installed. Production must use a real Redis URL.

If you use `docker compose up -d`, keep the database URLs from `.env.example` and point Redis at the Compose service:

```
DATABASE_URL=postgresql+asyncpg://bizpilot_app:bizpilot@127.0.0.1:55432/bizpilot
DATABASE_URL_SYNC=postgresql+psycopg://bizpilot:bizpilot@127.0.0.1:55432/bizpilot
REDIS_URL=redis://127.0.0.1:6379/0
```

## PostgreSQL (local, no Docker)

Windows:

```powershell
.\scripts\start-local-postgres.ps1
```

Linux:

```bash
./scripts/start-local-postgres.sh
```

Creates `.data/postgres` (gitignored), superuser `bizpilot`, database `bizpilot`, port `55432`, trust auth on localhost. The Phase 3 migration creates the non-superuser role `bizpilot_app`.

The API must use `bizpilot_app`. Alembic must use the owner role (`bizpilot` locally) so it can create tables and policies. A superuser connection bypasses row-level security.

## Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
alembic upgrade head
pytest
uvicorn app.main:app --reload --port 8000
```

Checks:

- `GET http://localhost:8000/health`
- `GET http://localhost:8000/api/v1/health`
- `GET http://localhost:8000/api/v1/health/ready` (`schema_phase` is `9` after the Phase 9 migration)

Email verification is required before `POST /api/v1/organizations` or `/organizations/onboarding`. Login is allowed unverified. In development and test, register/invite/reset responses include the token so you can complete the flow without SMTP.

Refresh and logout use cookies `bp_refresh` (httpOnly) and `bp_csrf`. Send header `X-CSRF-Token` with the csrf cookie value.

## Phase 2–9 API

Access tokens are bearer tokens. They do not contain an organization id. Send `X-Organization-Id` on tenant routes and `X-Branch-Id` when a route is branch-scoped.

```http
POST /api/v1/auth/register
POST /api/v1/auth/login
POST /api/v1/auth/refresh
POST /api/v1/auth/logout
POST /api/v1/auth/verify-email
POST /api/v1/auth/password-reset
GET  /api/v1/me
POST /api/v1/organizations
POST /api/v1/organizations/onboarding
GET  /api/v1/organizations
GET  /api/v1/organizations/current
GET  /api/v1/organization-settings
PUT  /api/v1/organization-settings
GET  /api/v1/industries
POST /api/v1/invitations
POST /api/v1/invitations/accept
POST /api/v1/branches
GET  /api/v1/branches
GET  /api/v1/branches/{branch_id}
GET  /api/v1/memberships
POST /api/v1/memberships
PATCH /api/v1/memberships/{membership_id}
PUT  /api/v1/memberships/{membership_id}/branches
PUT  /api/v1/memberships/{membership_id}/overrides
POST /api/v1/authorization/gates/journal-post
POST /api/v1/authorization/gates/inventory-adjust
POST /api/v1/warehouses
GET  /api/v1/warehouses
POST /api/v1/products
POST /api/v1/product-prices
GET  /api/v1/product-prices/resolve
POST /api/v1/inventory/adjustments
GET  /api/v1/stock-balances
POST /api/v1/stock-transfers
POST /api/v1/stock-counts
POST /api/v1/customers
POST /api/v1/pos/sessions
POST /api/v1/pos/sessions/{id}/sales
POST /api/v1/sales/{id}/refunds
POST /api/v1/payments/{id}/confirm
POST /api/v1/suppliers
POST /api/v1/purchase-orders
POST /api/v1/purchase-orders/{id}/approve
POST /api/v1/goods-receipts
POST /api/v1/supplier-invoices
POST /api/v1/supplier-payments
GET  /api/v1/accounts
POST /api/v1/journals
POST /api/v1/journals/{id}/reverse
POST /api/v1/periods/{id}/close
GET  /api/v1/reports/trial-balance
POST /api/v1/expenses
POST /api/v1/employees
POST /api/v1/payroll-runs
```

Sale complete, refunds, GRN post, journal post, and payroll run require header `Idempotency-Key`.

The two gate routes only check permissions. Creating an organization copies the system roles onto that organization, seeds a generic chart of accounts and fiscal periods, and makes the caller the owner. Owners have `access_all_branches`. A cashier or viewer only sees branches listed on `membership_branches` unless `access_all_branches` is set.

Denied requests return `403` with `error.code` of `permission_denied` and no stack trace.

## Frontend

```powershell
cd frontend
npm install
npm test
npm run dev
```

Open `http://localhost:3000`. The home page fetches FastAPI readiness over `NEXT_PUBLIC_API_URL`.

## API versioning

Business routes live under `/api/v1`. Additive changes stay on v1. Breaking changes require `/api/v2`.
