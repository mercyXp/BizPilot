# Phase 2 leftover, Phase 4, and Phase 5 report

## Status

Phase 2 identity flows, Phase 4 organization/warehouse/industry onboarding, and Phase 5 catalogue/inventory are implemented and verified against PostgreSQL 16. `schema_phase` is `5`.

## What was implemented

### Phase 2

- Refresh tokens are opaque, hashed, stored on `user_sessions`, and returned as an httpOnly `bp_refresh` cookie. Rotation issues a new row in the same family. Reuse of a rotated token revokes the family.
- Logout revokes the family and clears cookies. Cookie routes require `X-CSRF-Token` matching the `bp_csrf` cookie.
- Email verification tokens are single-use and hashed. Login is allowed unverified. Creating an organization is not (`email_unverified`).
- Password reset tokens are single-use. Confirming a reset increments `session_version` and revokes sessions.
- Invitations carry email, roles, branches, optional `access_all_branches`, expiry, and inviter. Accept is a security-definer function so the guest can join before they are a member.
- Optional TOTP: enable, confirm, disable. Login returns `totp_required` until a valid code is supplied.
- Development and test responses include email/invite/reset tokens so the flows can be tested without SMTP. Production omits them.

### Phase 4

- Onboarding creates the organization, system roles, owner membership, settings from the industry pack, locales, first branch, first warehouse, and a default `EA` unit of measure.
- Multi-branch create also creates a default warehouse per branch.
- Organization profile, timezone, currency, industry, and JSON settings can be read and updated.
- Industry packs: `general`, `grocery`, `pharmacy`, `clothing`. Pharmacy/grocery default to batch and expiry tracking. Negative stock defaults to denied.

### Phase 5

- Units of measure, products, variants, and prices. A branch price wins over the org default for the same list and date.
- `InventoryService` is the only path that inserts `stock_movements` and updates `stock_balances`. Weighted average on inbound. Outbound uses current average.
- Purchase-order source types are rejected. Goods receipts (`purchase_receipt`) receive stock.
- Transfers: create, dispatch (`transfer_out`), receive (`transfer_in`). In-transit is remaining qty on the document.
- Counts snapshot system qty and post variance movements.
- Batches when `track_batches` is set.
- Database trigger: movements cannot be updated or deleted. Balances cannot go negative unless the org setting allows it.

## Files created

- `backend/alembic/versions/20261120_0003_phase2_4_5.py`
- `backend/app/modules/identity/cookies.py`, `totp.py`
- `backend/app/modules/industry/`
- `backend/app/modules/catalogue/`
- `backend/app/modules/inventory/`
- `backend/app/api/v1/invitations.py`, `warehouses.py`, `catalogue.py`, `inventory.py`
- `backend/tests/test_auth_sessions.py`, `test_invitations.py`, `test_org_onboarding.py`, `test_catalogue_inventory.py`
- `docs/phase-2-4-5-report.md`

## Files modified

- Identity models/service/security, tenancy models/service, authorization catalogue
- Auth, organization, API router, schemas, models package, pyproject, middleware
- Existing tests (`helpers.py`, `test_health_ready.py`)
- `docs/TECHNICAL_RECORD.md`, `docs/setup.md`, `README.md`

## Database changes

Revision `20261120_0003` adds:

- Global: `user_action_tokens`; `users.totp_pending_encrypted`
- Tenant: `organization_settings`, `organization_locales`, `warehouses`, `invitations`, catalogue tables, `product_batches`, `stock_balances`, `stock_movements`, `stock_transfers`, `stock_transfer_items`, `stock_counts`, `stock_count_items`, `document_sequences`
- Forced RLS on those tenant tables
- `app_accept_invitation`; bootstrap now takes industry, timezone, currency, country
- Permissions `catalogue.view` and `catalogue.manage`
- Industry rows for grocery, pharmacy, clothing (general updated)
- `schema_phase` = `5`

Downgrade drops the new tables and restores `schema_phase` to `3`.

## Tests performed

All run on 20 Nov 2026 against PostgreSQL 16 on `127.0.0.1:55432`.

| Command | Result |
| --- | --- |
| `alembic upgrade head` | Passed. Applied `20261120_0003` |
| `alembic downgrade -1` then `upgrade head` | Passed |
| `pytest` after upgrade | Passed. 32 tests |
| `pytest` after downgrade/upgrade | Passed. 32 tests |
| Live `GET /api/v1/health/ready` | Passed. `database: ok`, `schema_phase: 5`, `redis: memory` |

Coverage includes unverified org creation, refresh rotation and reuse, logout, password reset, CSRF, TOTP, invite join, cross-tenant 403, onboarding/settings isolation, branch prices, movement immutability, PO rejection, negative stock, transfer, and count variance.

Frontend vitest, lint, and typecheck were not run. The frontend was not changed.

## Problems encountered

- Alembic `op.execute` does not take a parameters dict; inserts use `bindparams` and `CAST(:id AS uuid)`.
- Returning FastAPI's injected `Response` from logout did not finish the ASGI response. Logout now mutates cookies and returns `None`.
- httpx cookie `domain="test"` broke CSRF on reuse tests. The reuse case now overwrites only the refresh cookie.

## Outstanding tasks

- Real SMTP (still a log adapter; tokens exposed only outside production)
- Custom roles beyond seeded templates
- Fiscal year/period tables (Phase 8)
- Sales/POS (Phase 6), purchasing/GRN as documents (Phase 7)
- Frontend screens for auth, onboarding, catalogue, and stock
- Journal posting (Phase 8). The journal gate is still authorization-only

## Acceptance criteria

| Criterion | Result |
| --- | --- |
| Multi-org user; invite join; cross-tenant fail closed | Pass |
| Multi-branch create; settings stored; isolation holds | Pass |
| Prices per branch; movements immutable; balances reconcile; PO does not receive stock | Pass |
| Email verification required before creating an organization | Pass |
| Refresh rotation and reuse revocation | Pass |
| Backend pytest | Pass. 32 passed |
| Migrations apply and reverse | Pass |
| Frontend vitest/lint/typecheck | Not run |

## Next phase

Phase 6 — sales and POS. Purchasing remains Phase 7; inventory already refuses to treat a purchase order as a receipt.
