# Phase 6–9 report

## Status

Phases 6 (sales/POS), 7 (CRM and purchasing), 8 (accounting), and 9 (payroll) are implemented and verified against PostgreSQL 16. `schema_phase` is `9`.

## What was implemented

### Phase 6 — Sales and POS

- POS sessions: open with float, cash in/out, close with counted cash and variance posting.
- Server-side prices and tax. Client totals are ignored.
- Cash sales complete in one transaction: stock issue, receipt, journal.
- `Idempotency-Key` is required on sale complete, refunds, GRN, journal post, and payroll run. Reuse with the same payload returns the original result.
- `local_cash` settles immediately. `mock_mobile_pending` stays `pending` until `POST /payments/{id}/confirm`. Awaiting-payment sales do not issue stock.
- Refunds are line-wise, optional restock, and post a refund journal.

### Phase 7 — CRM and purchasing

- Customers, credit limits, and notes. Store-credit sales need `customers.credit` and a remaining limit.
- Suppliers, requisitions, purchase orders. Creating a PO does not touch stock.
- Approve requires `purchases.approve`. Cashiers are denied.
- GRN accepted qty calls `InventoryService.receive` (`purchase_receipt`). Over-receive is blocked.
- Supplier invoices and payments post AP through the posting engine.

### Phase 8 — Accounting

- Generic COA, document maps, fiscal year, and monthly periods are seeded at organization create (D14).
- `PostingEngine.post` is the only writer of posted journals. Domain modules never insert journal rows.
- Sales, GRN, invoices, payments, expenses, payroll, and POS variance call the engine in the same transaction and also write `accounting_post_requested` outbox events (D13).
- Posted journals are immutable. Reversals insert an opposite journal and mark the original `reversed`.
- Closed periods reject new posts.
- Trial balance, P&L, and balance sheet read posted lines. Bank import and reconciliation refuse unmatched silent posts.
- Tax rates are org data. Seeded `DEV_ZERO` is labelled DEV_ONLY. No Zambia VAT percentage in code.

### Phase 9 — Payroll

- Employees, leave, configurable components, periods, and runs.
- Calculations come from component JSON (`fixed`, `percent_of_base`, `percent_of_gross`). Statutory names cannot be labelled official.
- A processed run writes payroll items and a balanced payroll journal.
- `employees.base_salary` is stored on the employee (not in the Phase 0 column list) so a run has a base without extra assignment tables.

## Files created

- `backend/alembic/versions/20261120_0004_phase6_9.py`
- `backend/app/modules/audit/`
- `backend/app/modules/crm/`
- `backend/app/modules/sales/`
- `backend/app/modules/purchasing/`
- `backend/app/modules/accounting/`
- `backend/app/modules/payroll/`
- `backend/app/api/v1/customers.py`, `pos.py`, `sales.py`, `purchasing.py`, `accounting.py`, `payroll.py`, `ops_schemas.py`
- `backend/tests/test_sales_pos.py`, `test_purchasing.py`, `test_accounting.py`, `test_payroll.py`
- `docs/phase-6-9-report.md`

## Files modified

- API router, organization onboarding (COA seed), inventory `issue()`, permission catalogue (`purchases.view`)
- Models package, test helpers, health ready expectation
- `docs/TECHNICAL_RECORD.md`, `docs/setup.md`, `README.md`

## Database changes

Revision `20261120_0004` adds the Phase 6–9 tenant tables (POS, sales, CRM, purchasing, COA/journals/banks/expenses, payroll), forced RLS, append-only triggers on journals and audit logs, permission `purchases.view`, and `schema_phase` = `9`.

Downgrade drops those tables and restores `schema_phase` to `5`.

## Tests performed

All run on 20 Nov 2026 against PostgreSQL 16 on `127.0.0.1:55432`.

| Command | Result |
| --- | --- |
| `alembic upgrade head` | Passed. Applied `20261120_0004` |
| `alembic downgrade -1` then `upgrade head` | Passed |
| `pytest` after upgrade | Passed. 40 tests |
| `pytest` after downgrade/upgrade | Passed. 40 tests |
| Live `GET /api/v1/health/ready` | Passed. `database: ok`, `schema_phase: 9`, `redis: memory` |

Coverage includes cash sale stock and duplicate idempotency, mock mobile pending without webhook, refund restock, GRN vs PO stock, cashier cannot approve, balanced journals, immutability, reversals, closed period reject, report totals, and payroll calc/journals without official statutes.

Frontend vitest, lint, and typecheck were not run. The frontend was not changed.

## Problems encountered

- Closing the first open fiscal period did not block November posts. Tests now close the period that contains today.
- Reversal cannot UPDATE a posted journal’s `reverses_journal_id`. That field is set on insert; only `status`/`reversed_by_id` change on the original.

## Outstanding tasks

- Real payment, SMTP, and bank adapters
- Frontend POS, purchasing, accounting, and payroll screens
- Official tax and payroll figures after primary-source verification (Phases 12–14)
- Grok tools (Phase 10) and reporting dashboards (Phase 11)
- Loyalty business rules remain foundation-only (D25)

## Acceptance criteria

| Criterion | Result |
| --- | --- |
| Sale updates stock; duplicate key no double sale; mock mobile remains pending without webhook | Pass |
| GRN increases stock; PO does not; balances correct; approve permission | Pass |
| Balanced post; immutability; reversals; closed period reject; source documents post; reports reconcile | Pass |
| Auditable payroll calc; journals balance; no hardcoded statutes as official | Pass |
| Backend pytest | Pass. 40 passed |
| Migrations apply and reverse | Pass |
| Frontend vitest/lint/typecheck | Not run |

## Next phase

Phase 10 — Grok orchestrator, tools, approvals, and metering.
