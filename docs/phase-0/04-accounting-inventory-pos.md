# Phase 0 — Accounting, Inventory, and POS Transaction Architecture

## 1. Accounting: double-entry posting engine

### 1.1 Principles

- One **functional currency** per organization (default ZMW).
- Organization-wide **chart of accounts**.
- **Branch is a reporting dimension** on journal lines (nullable only for true org-level allocations; operational transactions set branch).
- Every **posted** journal: `sum(debit) = sum(credit)`, at least two lines, period open, unique source.
- Posted journals are **immutable**. `status: draft | posted | reversed`. Edits allowed only in `draft`.
- Corrections: a new journal with `reverses_journal_id` and opposite lines; original stays.
- Closed `accounting_periods` reject new ordinary posts. Period close is a permissioned command.
- Every posted journal has `source_type` + `source_id` (sale, refund, grn, supplier_payment, customer_payment, expense, payroll_run, bank_transfer, manual, reversal).

### 1.2 Central engine

`PostingEngine.post(command)` is the only way to insert posted journals.

Command includes: org, optional branch, period (resolved from timestamp + org calendar), description, lines `(account_id, debit, credit, branch_id, party_type, party_id, tax_rate_id?, memo)`, source ref, actor, idempotency key.

Engine responsibilities:

1. Validate membership/permissions (`accounting.journal.post` or a privileged system actor from a domain module running inside an already-authorized transaction).
2. Resolve period; reject if closed.
3. Coerce money to `Decimal`; reject mixed currencies.
4. Balance check; reject zero-amount lines.
5. Insert header + lines; stamp `posted_at`.
6. Update AR/AP subledger projections if party present.
7. Audit + outbox.

Domain modules **never** insert into `journal_entries` themselves.

### 1.3 Source-to-account mapping

Configurable per org (`accounting_document_maps` or settings):

| Source event | Typical posting (illustrative, accounts configurable) |
| --- | --- |
| Cash/card/mobile sale | Dr Bank/Cash/Mobile clearing, Dr AR if credit; Cr Revenue; Cr Tax payable if exclusive; inventory Dr COGS Cr Inventory |
| Refund | Reverse of original via reversal journal + restock movements if required |
| GRN (accepted qty) | Dr Inventory; Cr GRNI / Accrued purchases |
| Supplier invoice | Dr GRNI/Expense; Dr Tax input; Cr AP |
| Supplier payment | Dr AP; Cr Bank/Mobile |
| Customer payment | Dr Bank; Cr AR |
| Expense | Dr Expense; Dr Tax; Cr Bank/AP |
| Payroll | Dr Salary expense / employer contributions; Cr PAYE/NAPSA/NHIMA payables; Cr Net pay clearing |

Exact account codes are **org data**, seeded from an industry/country pack, not constants in Python except as seed fixtures.

### 1.4 Tax

- `tax_rates`: org-scoped, `rate` NUMERIC, `inclusive` flag, `effective_from`, `effective_to`.
- Line tax computed in domain services using rate in effect on document date.
- **Do not hardcode Zambian VAT.** Production seed happens after official-source verification (Phase 12/14). Dev fixtures may use placeholder labelled `DEV_ONLY` and must not ship as “Zambia VAT”.

### 1.5 Periods and statements

- `fiscal_years` → `accounting_periods` (typically months).
- Reports read journal lines: GL, trial balance, P&L (income/expense accounts), balance sheet (asset/liability/equity), cash flow (indirect from period movements + cash accounts — implementation in Phase 8 with test fixtures).
- AR/AP ageing from open items (invoice remaining vs paid allocations).

### 1.6 Banks

Bank accounts belong to org (optionally default branch). Import transactions; reconciliation matches bank lines to journal/payment refs. Unmatched items cannot silently post.

## 2. Inventory

### 2.1 Costing

- **Weighted average** at `warehouse_id + product_variant_id` (and `batch_id` when batch-tracked).
- Average recalculated on inbound valued receipts: `new_avg = (qty*avg + in_qty*in_cost) / (qty + in_qty)`.
- Outbound uses current average (COGS).
- Schema reserved: movement `costing_method` and future FIFO layers table **not** implemented until needed.

### 2.2 Immutable movements

`stock_movements` insert-only. Types: `purchase_receipt`, `sale_issue`, `refund_return`, `transfer_out`, `transfer_in`, `adjustment`, `count_variance`, `production_issue`, `production_receipt` (latter two unused until manufacturing pack).

Rules:

- Never `UPDATE` quantity on a movement.
- Never change `stock_balances.qty` except in the same transaction as a movement insert (single `InventoryService` path).
- PO **does not** create inbound movements.
- GRN accepted quantity **does**.
- Transfer: dispatch → `transfer_out` (source); receive → `transfer_in` (dest). In-transit is `dispatched - received` on the transfer document, not a fake warehouse unless we add one later.

### 2.3 Quantities

All qty `NUMERIC(19,4)`. UoM on variant; conversions in `uom_conversions`. POS sells in sell UoM; stock stored in stock UoM.

### 2.4 Batches and expiry

`product_batches` when `products.track_batches`. Movements reference `batch_id`. Expiry alerts are queries over remaining qty where `expires_on <= threshold`. Pharmacy pack sets `track_batches` and `track_expiry` defaults true.

### 2.5 Transfers lifecycle

`draft → approved → dispatched → (partially_received) → completed | cancelled`

Cannot complete with remaining qty unless short-close with discrepancy movement (permissioned).

### 2.6 Counts

Count sheet captures snapshot qty; posting writes variance adjustments. Count in progress may optionally freeze warehouse (setting).

## 3. POS and sales integrity

### 3.1 Sale completion (single DB transaction)

1. Lock POS session (must be `open`, same cashier/branch).
2. Idempotency key: if seen, return original result.
3. Validate stock (or allow negative if org setting — default **deny**).
4. Compute prices, discounts, tax from server-side price/tax tables (client totals are hints; **server is authority**).
5. Insert `sales`, `sale_items`, `payments` (see payment states), `receipts`.
6. Inventory issues for goods (not services).
7. Call posting engine (from Phase 8 onward; until then `accounting_pending` outbox event — see decision in roadmap).
8. Audit.

### 3.2 Payments

| Method | Recorded as paid when |
| --- | --- |
| Cash | Session records cash tender + change; no external provider |
| Card / bank / mobile money | `payments.status = pending` until adapter confirms (webhook or query). Sale may be `awaiting_payment` or split: unpaid remainder |
| Customer credit | Requires `customers.credit` permission and limit check; posts AR |

**Never** set mobile money to `completed` because the cashier selected the method.

Split payments: sum(allocated) must equal sale total before sale `status=completed`, except explicit credit remainder.

### 3.3 Refunds

Permission `sales.refund`. Original sale required. Restock optional. Accounting via reversal/refund journal. Partial refunds allowed line-wise up to remaining qty/amount.

### 3.4 POS sessions

Open session: opening float. Cash in/out movements. Close: counted vs expected; variance recorded (expense/overage accounts when accounting live).

### 3.5 External payment adapter interface

```
PaymentProvider.create_intent(org, amount, currency, reference) -> provider_ref
PaymentProvider.verify(provider_ref) -> settled | failed | pending
handle_webhook(payload, signature) -> verify, then complete payment + post if sale completable
```

No real endpoints invented in Phase 0–6. Fake `LocalCashProvider` for tests only.

## 4. Purchasing

- Requisition → PO (approval permission) → GRN (partial OK) → supplier invoice → payment.
- PO qty vs received vs invoiced tracked separately (three-way match optional by org setting; default two-way PO/GRN then invoice).
- Discrepancies: short receive, over-receive (blocked or permissioned).

## 5. Transaction and outbox pattern

All of: document write + movements + journals + `outbox_events` + `audit_logs` in **one** SQL transaction. Celery delivers outbox after commit. Failed delivery retries; handlers are idempotent.
