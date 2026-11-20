# BizPilot — Central Technical Record

**Product:** BizPilot  
**Status:** Phases 2–9 implemented through sales, purchasing, accounting, and payroll  
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
| 0 | Product specification and architecture | Recorded in `docs/phase-0/` |
| 1 | Foundation | Scaffold was in place; health, config, logging, and Alembic still run |
| 2 | Auth and tenancy | Implemented. Refresh rotation, logout, email verification, password reset, invitations, optional TOTP. See `docs/phase-2-4-5-report.md` |
| 3 | RBAC | Implemented. See `docs/phase-3-report.md` |
| 4 | Org, branches, industry | Implemented. Onboarding, settings, warehouses, industry packs |
| 5 | Catalogue and inventory | Implemented. Products, prices, movements, transfers, counts, batches |
| 6 | Sales and POS | Implemented. Sessions, payments, receipts, refunds, idempotency. See `docs/phase-6-9-report.md` |
| 7 | CRM and purchasing | Implemented. Customers, PO/GRN/invoices/payments |
| 8 | Accounting | Implemented. COA, periods, PostingEngine, AR/AP, expenses, banks, statements |
| 9 | Payroll | Implemented. Employees, leave, configurable components, runs |
| 10–15 | See roadmap document | Not started |

## Decision log

Decisions taken during Phase 0 are listed in `docs/phase-0/06-roadmap-decisions-gaps.md`.

| ID | Decision | Why |
| --- | --- | --- |
| P3-1 | Phase 3 started on the Phase 1 scaffold, with only the Phase 2 tables and routes RBAC needs | The requested work was Phase 3. Forbidden-action and branch-leak tests need users, memberships, organizations, branches, and RLS. Refresh rotation, email verification, and invitations stay in the Phase 2 backlog |
| P3-2 | API connects as `bizpilot_app` (`NOBYPASSRLS`). Alembic connects as the database owner | Superusers bypass row-level security even when it is forced. Isolation tests use the app role |
| P3-3 | `organization_memberships` policy allows a row when `user_id` is the current user, or when the current user is an active member of the row's organization | The spec's org-only policy cannot list "my organizations" before an org is selected. Other tenant tables stay org-scoped and require an active membership |
| P3-4 | Organization bootstrap is a `SECURITY DEFINER` function | The first membership and system roles must be inserted before the caller is a member. The app role has no insert grant on `organizations` or `roles` |
| P3-5 | `users.session_version` backs the access-token `pv` claim | The security spec requires `pv`. Password reset increments the version and revokes sessions |
| P3-6 | System roles are copied per organization. `platform.orgs.manage` is never copied. Cashiers do not get `accounting.journal.post`. Viewers do not get `inventory.adjust` | Phase 0 role matrix. Cashier `sales.refund` is present as the limited refund grant; amount limits wait for the sales module |
| P3-7 | Journal-post and inventory-adjust routes are authorization gates only | Phase 3 has to prove 403s. It does not create journals or stock movements |
| P2-1 | Refresh token is an httpOnly cookie; CSRF is a non-httpOnly cookie plus `X-CSRF-Token` | Decision D3 |
| P2-2 | Invitations include `access_all_branches` in addition to `branch_ids` | Otherwise an invited manager cannot be granted every branch without listing them |
| P2-3 | Email/invite/reset token values are returned in non-production responses | There is no SMTP adapter yet. Production omits the values |
| P4-1 | Creating a branch also creates a default warehouse `{branch_code}-WH` | Phase 4 requires warehouses; stock cannot exist without one |
| P5-1 | `InventoryService` is the only writer of `stock_movements` / `stock_balances`. Source type `purchase_order` is rejected | Matches “PO does not receive stock”. GRN is Phase 7 |
| P6-1 | Mobile money uses `mock_mobile_pending` until `POST /payments/{id}/confirm` | Decision D22. Selecting the method never completes the payment |
| P6-2 | `awaiting_payment` sales do not issue stock | Stock and journals wait until allocated completed payments equal the total |
| P7-1 | Over-receive is blocked | Safer default than a permissioned exception |
| P8-1 | COA, maps, fiscal year, and periods are seeded at organization create | Decision D14 |
| P8-2 | Domain modules call `PostingEngine` in the same transaction and write `accounting_post_requested` | Decision D13 |
| P9-1 | `employees.base_salary` is stored on the employee | Phase 0 had no assignment table; a run still needs a base |
| P9-2 | Statutory components are configurable rows and cannot be labelled official | Decision D16 |

## Environment and secrets

`.env.example` is the committed template. `.env` is gitignored. The local database password in Compose and the example file is a development credential, not a production secret. Production must replace `SECRET_KEY`, the database passwords, and `REDIS_URL`.
