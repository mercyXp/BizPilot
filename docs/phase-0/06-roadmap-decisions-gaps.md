# Phase 0 — Decisions, Gaps, Roadmap, Acceptance

## 1. Contradictions reviewed

| Topic | Resolution |
| --- | --- |
| Frontend sends org/branch IDs vs “never trust client” | Client sends headers; **membership check + RLS** is the source of truth |
| Full accounting vs phased delivery | Domain modules write source documents first; **only PostingEngine** writes journals. Engine interface exists before Phase 8; **posted journals and statement tests** are a Phase 8 gate |
| Platform super admin vs RLS | Separate `platform_role` and platform routes; no blanket BYPASSRLS on the app DB user |
| Industry-specific needs vs one platform | JSON schemas + module flags + optional workflow packs; no forked apps |
| Online-only vs Zambian connectivity | Honor online-only for v1; POS still uses idempotency so retries are safe. Offline POS is a future project, not a silent scope change |
| AI as a product vs unrestricted access | Tool-only, permissioned, tenant-scoped, drafts for writes |
| SaaS billing vs tenant accounting | Separate tables; never auto-post platform fees into the customer’s books unless they manually record an expense |
| “Don’t invent ZRA/mobile APIs” vs “prepare integrations” | Adapter interfaces + field reservations; no fake endpoints |

No requirement in the master prompt is rejected. Where two requirements tension, the stricter integrity/security rule wins.

## 2. Recommended decisions (approve with Phase 0)

These were not fully specified. They are **binding if you approve Phase 0**.

| ID | Decision | Why |
| --- | --- | --- |
| D1 | **Monorepo** `frontend/` + `backend/` | Simplest modular monolith; one PR, one CI |
| D2 | Access JWT **omits org_id**; org via `X-Organization-Id` | Multi-org users; switch org without refresh |
| D3 | Refresh token **httpOnly cookie** + CSRF on auth cookie routes; access token in memory | Limits XSS token theft of refresh; SPA-friendly |
| D4 | Password hashing **Argon2id** | Current best practice for new systems |
| D5 | UUID **v7** primary keys | Time-sortable, better index locality than v4 |
| D6 | Single functional currency per org; FX table **not** in v1 schema | Avoids incomplete multi-currency accounting |
| D7 | Weighted average at warehouse+variant (+batch if tracked) | Matches inventory reality; FIFO later |
| D8 | Default **deny negative stock** (org setting to allow) | Safer for grocery/pharmacy |
| D9 | Transfers use document in-transit, not a hidden warehouse | Simpler reconciliation |
| D10 | Email verification **required before creating an organization**; login allowed unverified with nag | Reduces spam orgs |
| D11 | Optional TOTP in Phase 2; not mandatory until policy | Unblocks Zambia SMEs without phones as 2FA |
| D12 | Default timezone `Africa/Lusaka`, currency `ZMW`, locale `en` | Market default |
| D13 | **PostingEngine** invoked from sales/GRN **from Phase 8**; Phase 6–7 persist `outbox_events` `accounting_post_requested` so no dual logic later | Avoids fake journals before COA/periods exist |
| D14 | COA **seeded at org onboarding** from a generic template (Phase 4/8) | Reports cannot run without accounts |
| D15 | Tax rates: **no production Zambia VAT seed** until verified against official sources | Legal accuracy |
| D16 | Payroll statutory formulas: configurable rows; **no production PAYE/NAPSA/NHIMA numbers** until verified | Legal accuracy |
| D17 | Platform billing **manual / recorded events** until a payment provider is contracted | No invented Stripe-like integration |
| D18 | Soft delete masters; **hard prohibition** on deleting stock movements, payments, journals | Audit |
| D19 | `document_sequences` table for numbers | Avoids gaps from failed commits without advisory-lock spaghetti |
| D20 | AI write path = **draft + approval** always | Matches “confirm sensitive actions” |
| D21 | Next.js talks **only** to FastAPI for business data | One security kernel |
| D22 | Dev payment provider `local_cash` and `mock_mobile_pending` | Tests the pending-payment rule without fake real APIs |
| D23 | Data Protection export/retention: **Phase 15** design, not Phase 2 | Focus isolation first |
| D24 | Restaurant tables/KOT, hotel folio, manufacturing BOM, serials: **industry extensions after core** (Phase 12+) | Shared platform first |
| D25 | Loyalty points: tables exist, **business rules minimal** until a pack enables them | Avoid unused complexity |

## 3. Important gaps (acknowledged)

1. **Official tax, payroll, and ZRA specs** — must be researched from primary sources before production configuration (Phases 12–14).  
2. **Mobile money providers (Airtel Money, MTN MoMo, Zamtel)** — adapter only until partner docs exist.  
3. **Bank integrations** — same.  
4. **WhatsApp Business** — Phase 14.  
5. **Multi-country VAT** — architecture allows country_code; only ZM defaults in onboarding.  
6. **Price lists / customer groups** — `price_list_code` on prices; full B2B price matrix later.  
7. **Serial numbers** — flag on product; table added when electronics pack lands.  
8. **Landed cost / import** — not v1.  
9. **Offline POS** — explicitly out of v1.  
10. **Customer-facing portal** — out of v1.

## 4. Implementation roadmap

Work one phase at a time. Do not start Phase N+1 until Phase N acceptance is checked.

### Phase 1 — Foundation

Compose, FastAPI, Next.js, Postgres, Alembic, logging, `/health`, CORS, config from env.  
**Accept:** both apps start; DB connects; migrations apply; health ready; no secrets in git.

### Phase 2 — Auth and tenancy

Register/login/logout/refresh/reset/verify; orgs; memberships; invitations; org switch; RLS.  
**Accept:** multi-org user; invite join; cross-tenant tests fail closed.

### Phase 3 — RBAC

Roles, permissions, branch grants, overrides, owner vs cashier.  
**Accept:** forbidden actions 403; branch leak tests pass.

### Phase 4 — Org, branches, industry

Profiles, branches, warehouses, industry pack storage, onboarding, currency/timezone.  
**Accept:** multi-branch create; settings stored; isolation holds.

### Phase 5 — Catalogue and inventory

Products, variants, prices, stock, movements, transfers, counts, batches.  
**Accept:** prices per branch; movements immutable; balances reconcile in tests; PO does not receive stock.

### Phase 6 — Sales and POS

Sessions, cart, tax, payments, receipts, refunds, idempotency, pending external pay.  
**Accept:** sale updates stock; duplicate key no double sale; mock mobile remains pending without webhook.

### Phase 7 — CRM and purchasing

Customers, credit, suppliers, PR/PO/GRN/invoices/payments.  
**Accept:** GRN increases stock; PO does not; balances correct; approve permission.

### Phase 8 — Accounting

COA, periods, engine, AR/AP, expenses, banks, statements.  
**Accept:** balanced post; immutability; reversals; closed period reject; source documents post; reports reconcile. **Hard gate.**

### Phase 9 — Payroll

Employees, leave, configurable components, runs, post to engine.  
**Accept:** auditable calc; journals balance; no hardcoded statutes as “official”.

### Phase 10 — Grok

Orchestrator, tools, approvals, metering, audit.  
**Accept:** verified data; tenant/permission isolation; no self-approved payouts.

### Phase 11 — Reporting

Dashboards, branch vs org, exports.  
**Accept:** totals match sources; permissioned.

### Phase 12 — i18n and industry packs

Message framework; 1–2 packs beyond general (pharmacy attributes, clothing variants as config).  
**Accept:** no forked codebase; professional translation flag.

### Phase 13 — SaaS billing and platform admin

Plans, limits, suspend/reactivate.  
**Accept:** tenant books unchanged by platform invoices.

### Phase 14 — Integrations

Adapters + official docs only.  
**Accept:** no claimed live ZRA/MoMo without credentials.

### Phase 15 — QA and production readiness

Tests, backups, CI, monitoring, docs.  
**Accept:** critical tests executed; production checklist complete.

## 5. Phase 0 acceptance criteria

| Criterion | Status |
| --- | --- |
| Product requirements captured | Met in `00-product-requirements.md` |
| System architecture and module map | Met in `01-system-architecture.md` |
| Database ER + table spec | Met in `02-database-specification.md` |
| Tenant isolation + RBAC | Met in `03-security-tenancy-authorization.md` |
| Accounting/inventory/POS transaction design | Met in `04-accounting-inventory-pos.md` |
| Grok + API + frontend IA | Met in `05-ai-api-frontend.md` |
| Roadmap and decisions | This document |
| Application code | **Intentionally not started** |

## 6. Stop point

**Phase 1 must not start until you approve Phase 0**, including the recommended decisions D1–D25 (or you list overrides).
