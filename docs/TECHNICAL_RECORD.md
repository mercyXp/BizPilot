# BizPilot — Central Technical Record

**Product:** BizPilot  
**Status:** Phases 1–9 plus live demo, operational reporting, i18n/industry packs, and production checklist/CI  
**Last updated:** 2026-11-20  
**Market (initial):** Zambia  
**Default currency:** ZMW  

This file is the index of approved product and technical decisions. Do not contradict approved architecture without an explicit decision log entry.

## Document map

| Document | Purpose |
| --- | --- |
| [phase-0/00-product-requirements.md](phase-0/00-product-requirements.md) | Product requirements, users, modules, non-goals |
| [phase-0/01-system-architecture.md](phase-0/01-system-architecture.md) | Modular monolith, runtime, module boundaries, dependencies |
| [phase-0/02-database-specification.md](phase-0/02-database-specification.md) | ER design, table specs, constraints |
| [phase-0/03-security-tenancy-authorization.md](phase-0/03-security-tenancy-authorization.md) | Authn, RBAC, RLS, tenant isolation |
| [phase-0/04-accounting-inventory-pos.md](phase-0/04-accounting-inventory-pos.md) | Posting engine, inventory movements, POS integrity |
| [phase-0/05-ai-api-frontend.md](phase-0/05-ai-api-frontend.md) | Grok orchestration, API contracts, frontend IA |
| [phase-0/06-roadmap-decisions-gaps.md](phase-0/06-roadmap-decisions-gaps.md) | Phases, acceptance criteria, gaps, recommended decisions |
| [setup.md](setup.md) | Local development setup |
| [phase-1-notes.md](phase-1-notes.md) | Phase 1 runtime notes |

## Confirmed stack

- Frontend: Next.js App Router, React, TypeScript, Tailwind CSS (shadcn/ui, RHF, Zod, TanStack Query, Recharts in later UI phases)
- Backend: Python 3.12, FastAPI 0.115.6, Pydantic 2.10.3, SQLAlchemy 2.0.36, Alembic 1.14.0, REST, Pytest 8.3.4
- Data: PostgreSQL 18 (project-local cluster on 55432), Redis optional via `memory://` in development
- Auth: JWT access tokens + refresh-token rotation (Phase 2)
- AI: Grok API via orchestration (Phase 10)

## Implementation status

| Phase | Name | Status |
| --- | --- | --- |
| 0 | Product specification and architecture | Completed (approved by proceeding to Phase 1) |
| 1 | Project foundation | Completed |
| 2 | Authentication and multi-tenancy | Completed |
| 3 | RBAC | Completed (ported onto main auth/tenancy) |
| 4 | Org, branches, industry | Completed |
| 5 | Catalogue and inventory | Completed |
| 6 | Sales and POS | Completed |
| 7 | CRM and purchasing | Completed |
| 8 | Accounting | Completed |
| 9 | Payroll | Completed |
| 10 | Grok | Not started |
| 11 | Reporting | Completed (operational reports + dashboard) |
| 12 | i18n and industry packs | Completed (message catalogue + pharmacy/clothing config) |
| 13 | SaaS billing | Not started |
| 14 | Integrations | Not started |
| 15 | QA and production readiness | Completed (CI + production checklist; no fake ZRA/MoMo claims) |

## Implemented modules

- `backend/app/core` — config, logging, errors, DB, cache, middleware, JWT, RLS helpers
- `backend/app/api/v1/health` — live and ready checks
- `backend/app/api/v1/auth` — register, login, refresh, logout, verify, password reset
- `backend/app/api/v1/organizations` — create org, memberships, invitations
- `frontend` — sign-in/up, verify, reset, org switcher at `/app`, live `/app/reports`, dashboard KPIs from reporting API
- `backend/app/api/v1/reporting` — sales, inventory, movement, purchases, expenses, customers, shifts, tax, summary, CSV export (`reports.view`)
- `backend/app/api/v1/i18n` — message catalogue with `system` / `professional` provenance

## Completed migrations

- `20261120_0001` — `app_metadata` with `schema_phase=1`
- `20261120_0002` — users, sessions, orgs, memberships, invitations, RLS, `bizpilot_app`
- `20261120_0003` — organization SELECT policy so INSERT RETURNING works for the creator
- `20261120_0004` — RBAC, industries, branches (does not recreate users/orgs)
- `20261120_0005` — org settings, warehouses, catalogue, inventory
- `20261120_0006` — CRM, sales, purchasing, accounting, payroll
- `20261120_0007` — `translation_resources`, industry pack refresh, `schema_phase=11`

## Environment variables

See `.env.example`. Never commit `.env`.

| Variable | Purpose |
| --- | --- |
| `APP_ENV` | development / test / staging / production |
| `SECRET_KEY` | reserved for Phase 2 JWT; placeholder in development |
| `DATABASE_URL` | async SQLAlchemy URL |
| `DATABASE_URL_SYNC` | Alembic URL |
| `REDIS_URL` | `redis://...` or `memory://` |
| `CORS_ORIGINS` | comma-separated browser origins |
| `NEXT_PUBLIC_API_URL` | FastAPI origin for the Next.js app |
| `PUBLIC_APP_URL` | Origin used in verification and invite links |

## Decision log (binding)

Phase 0 D1–D25 are approved by the instruction to proceed to Phase 1. See `docs/phase-0/06-roadmap-decisions-gaps.md`.

See [production-checklist.md](production-checklist.md) for Phase 15 go-live gates.

Phase 1 additions:

- **D26:** Local PostgreSQL cluster in `.data/postgres` on port 55432 when Docker is unavailable.
- **D27:** Development may use `REDIS_URL=memory://`. Production must use Redis.
- **D28:** This workstation cannot reach `registry.npmjs.org` (HTTP 403). Frontend installs use `https://registry.npmmirror.com` via `frontend/.npmrc`.

- **D31:** Marketing header uses `Logo` / `frontend/public/logo/BizPilot_logo.png` only. Nav: Home (teal bar above the active item), Solutions and Industries with chevrons, Pricing, About Us, Contact, Login, and a rounded teal pill **See Demo** (not Book a Demo).
- **D32:** Palette updates flow through main tokens (`frontend/src/lib/colors.ts` and `globals.css`): ink `#0F172A`, canvas `#F1F5F9`, secondary `#334155`. Brand teal stays `#0D9488` / `#0F766E` / `#CCFBF1`.
