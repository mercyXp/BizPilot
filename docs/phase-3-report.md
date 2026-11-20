# Phase 3 report

## Status

Phase 3 RBAC is implemented and verified against PostgreSQL 16. The Phase 2 identity and tenancy pieces required to enforce it are included. Refresh-token rotation, logout, email verification, password reset, and invitations are not.

## What was implemented

- Access-token login (`sub`, `sid`, `pv`) and Argon2id password hashing. Organization id stays in `X-Organization-Id`, not in the token.
- Organizations, branches, and memberships. The creating user becomes owner with `access_all_branches`.
- Permission catalogue and ten system roles copied onto each organization: owner, org admin, manager, accountant, cashier, salesperson, inventory manager, procurement, HR, and viewer.
- Role assignment, permission overrides (deny wins), and branch grants.
- Request checks for `accounting.journal.post`, `inventory.adjust`, `branches.manage`, and `users.manage`. Cashiers cannot post journals. Viewers cannot adjust stock unless an allow override says so. A granted branch does not reveal another branch.
- Forced row-level security on tenant tables. The API uses `bizpilot_app` (`NOBYPASSRLS`). Alembic uses the database owner.
- Organization bootstrap runs in a security-definer function so the first membership and roles can be inserted before the caller is a member.
- Error responses stay in the existing envelope. Permission failures are `403` / `permission_denied` and do not include a stack trace.

The journal and inventory routes are authorization gates only. They do not write accounting or stock rows.

## Files created

- `backend/alembic/versions/20261120_0002_phase3_rbac.py`
- `backend/app/core/context.py`
- `backend/app/core/rls.py`
- `backend/app/modules/identity/` (models, password hashing, JWT, register/login)
- `backend/app/modules/tenancy/` (organizations, branches, memberships)
- `backend/app/modules/authorization/` (catalogue, policies, dependencies)
- `backend/app/api/v1/auth.py`
- `backend/app/api/v1/organizations.py`
- `backend/app/api/v1/branches.py`
- `backend/app/api/v1/memberships.py`
- `backend/app/api/v1/authorization.py`
- `backend/app/api/v1/schemas.py`
- `backend/tests/__init__.py`
- `backend/tests/helpers.py`
- `backend/tests/test_permission_catalog.py`
- `backend/tests/test_authorization.py`
- `backend/tests/test_tenant_isolation.py`
- `scripts/postgres/init-roles.sql`
- `scripts/start-local-postgres.sh`
- `docs/phase-3-report.md`

## Files modified

- `backend/app/core/config.py`
- `backend/app/core/db.py`
- `backend/app/core/errors.py`
- `backend/app/core/middleware.py`
- `backend/app/api/v1/__init__.py`
- `backend/app/models/__init__.py`
- `backend/pyproject.toml`
- `backend/tests/conftest.py`
- `backend/tests/test_health_ready.py`
- `docker-compose.yml`
- `.env.example`
- `README.md`
- `docs/TECHNICAL_RECORD.md`
- `docs/setup.md`
- `docs/phase-1-notes.md`

## Database changes

Revision `20261120_0002` adds:

- Global: `users`, `user_sessions`, `industries` (one `general` row), `permissions`
- Tenant, with forced row-level security: `organizations` is global and filtered in the API; `branches`, `organization_memberships`, `roles`, `role_permissions`, `membership_roles`, `membership_branches`, `user_permission_overrides` are tenant tables
- Role `bizpilot_app` if it does not already exist, plus grants and the bootstrap/RLS functions
- `app_metadata.schema_phase` set to `3`

`organization_memberships` can be read by the current user or by an active member of that organization. Every other tenant table requires the organization GUC and an active membership. Downgrade drops these tables and restores `schema_phase` to `1`.

## Tests performed

All of these were run on 20 Nov 2026 against PostgreSQL 16 on `127.0.0.1:55432`.

| Command | Result |
| --- | --- |
| `alembic upgrade head` | Passed. Applied `20261120_0001` and `20261120_0002` |
| `alembic downgrade -1` | Passed. `schema_phase` returned to `1`. Public tables left: `alembic_version`, `app_metadata` |
| `alembic upgrade head` after that downgrade | Passed. Current revision `20261120_0002` |
| `alembic downgrade base` | Passed. Public tables left: `alembic_version` |
| `alembic upgrade head` after downgrade base | Passed |
| `pytest` | Passed. 17 tests, 3.84s, after the full downgrade/upgrade |
| `uvicorn` on port 8000 | Passed. `GET /health` returned `status: ok`. `GET /api/v1/health/ready` returned `database: ok`, `schema_phase: 3`, `redis: memory` |
| Live register, create organization, add cashier | Passed. Cashier `POST /api/v1/authorization/gates/journal-post` returned `403` `permission_denied`. Inventory adjust returned `403` `permission_denied` |

Pytest covers cashier and org-admin journal denial, viewer stock denial until an allow override, deny winning over the accountant role, branch list/get leakage, cross-organization requests, and direct SQL as `bizpilot_app` with and without the tenant GUCs.

## Problems encountered

- Docker is not installed in this environment. PostgreSQL 16 was installed with apt and started as a project-local cluster on port 55432.
- `python3-venv` was missing and was installed before the backend virtualenv could be created.
- Pytest-asyncio gives each test its own event loop. A pooled asyncpg connection from the previous test then failed with "attached to a different loop". The test environment uses `NullPool`.

## Outstanding tasks

- Refresh-token rotation, reuse detection, and logout
- Email verification before organization creation (decision D10), password reset, and invitations
- Optional TOTP
- Custom roles beyond the seeded system templates
- Warehouses, organization settings, and industry packs (Phase 4)
- Real journal posting and stock adjustments (later phases). The current gates only authorize
- API row checks are the RBAC boundary. Direct SQL as `bizpilot_app` is still limited to the caller's organizations, but it is not a second copy of the permission matrix
- Frontend screens for roles and branch grants
- CI remains scheduled for Phase 15

## Acceptance criteria

| Criterion | Result |
| --- | --- |
| Forbidden actions return 403 | Pass. Cashier journal post, cashier branch create, org-admin journal post, and viewer stock adjust returned `403` / `permission_denied` |
| Branch leak tests pass | Pass. A cashier granted branch A lists and reads only A, and receives `403` for branch B. Another organization's branch id returns `404`. `bizpilot_app` sees no branch rows without the tenant GUCs and sees none of another organization's rows when the GUC is set to an org the user has not joined |
| Database connects | Pass. Readiness reported `database: ok` |
| Migrations apply and reverse | Pass. `upgrade head`, `downgrade -1`, `downgrade base`, and `upgrade head` all ran |
| No secrets committed | Pass. `.env` is gitignored. `.env.example` holds the local development values only |
| Backend pytest | Pass. 17 passed |
| Frontend vitest, lint, and typecheck | Not run. The frontend was not changed in this phase |

## Next phase

Phase 4 — organization profile, warehouses, and industry configuration. The unfinished Phase 2 session and invitation flows should be closed before those settings depend on a verified owner.
