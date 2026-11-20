# BizPilot — Central Technical Record

**Product:** BizPilot  
**Status:** Phase 0 in review — awaiting approval before Phase 1  
**Last updated:** 2026-11-20  
**Market (initial):** Zambia  
**Default currency:** ZMW  

This file is the index of approved product and technical decisions. Phase documents live under `docs/phase-0/`. After each completed phase, this record must be updated. Do not contradict approved architecture without an explicit decision log entry.

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

## Confirmed stack

- Frontend: Next.js App Router, React, TypeScript, Tailwind CSS, shadcn/ui, React Hook Form, Zod, TanStack Query, Recharts
- Backend: Python, FastAPI, Pydantic, SQLAlchemy 2.x, Alembic, REST, Pytest
- Data: PostgreSQL (shared schema + RLS), Redis, Celery, S3-compatible object storage
- Auth: JWT access tokens + refresh-token rotation
- AI: Grok API via a dedicated orchestration service; backend-executed tools only

## Implementation status

| Phase | Name | Status |
| --- | --- | --- |
| 0 | Product specification and architecture | In progress — pending approval |
| 1–15 | See roadmap document | Not started |

## Decision log

Decisions taken during Phase 0 (subject to your approval) are listed in `docs/phase-0/06-roadmap-decisions-gaps.md`. After approval they are copied here as binding.

## Environment and secrets

No application environment files exist yet. Secrets must never be committed. Phase 1 will introduce `.env.example` only.
