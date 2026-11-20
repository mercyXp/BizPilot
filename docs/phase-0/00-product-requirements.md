# Phase 0 — Product Requirements Document

## 1. Understanding

BizPilot is a **multi-tenant, modular-monolith SaaS** for running a business from one system: catalogue, inventory, POS, purchasing, customers, suppliers, expenses, double-entry accounting, employees/payroll, multi-branch operations, reporting, and a Grok-powered assistant.

It is **one configurable platform**, not a family of industry apps. Industry packs change terminology, enabled modules, product/service attributes, inventory rules, tax defaults, workflows, and dashboards. Core ledgers, stock movements, tenancy, and posting rules stay identical.

Initial commercial market is **Zambia**. The architecture is country-aware (currency, tax, address, document format, payment adapters, ZRA readiness) so additional countries can be added without rewriting the core.

Connectivity model for v1 is **online-only**. POS and financial operations therefore require an authenticated session, idempotency keys, and provider-verified payments. Offline POS is out of v1 scope (see recommended later enhancement).

## 2. Product principles

1. **Tenant isolation is absolute.** Organization data never leaks across tenants, including via AI, reports, search, or exports.
2. **Financial integrity.** Posted journals balance, are immutable, and always point at a source document. Corrections are reversals.
3. **Inventory integrity.** Stock changes only through immutable movements. Balances must reconcile to movement history.
4. **Authorization is server-side.** UI hiding is convenience; the API enforces every action.
5. **One posting engine.** Sales, refunds, purchases, expenses, payroll, and payments do not invent their own accounting.
6. **Adapters at the edge.** Mobile money, banks, SMS, email, ZRA, object storage: swap implementations without changing domain logic.
7. **Do not fabricate integrations.** External systems are interfaces until official docs and credentials exist.
8. **Modular monolith first.** Extract services only when a measured bottleneck or team boundary requires it.

## 3. Actors

| Actor | Scope | Notes |
| --- | --- | --- |
| Unauthenticated visitor | Public | Marketing/login/register only |
| User | Global identity | May belong to many organizations |
| Platform Super Administrator | Platform | Manages plans, orgs (suspend/reactivate), operational health. Separate from tenant RBAC |
| Organization Owner | Tenant | Full org control including billing contact, industry, branches, users |
| Organization Administrator | Tenant | Day-to-day admin; cannot transfer ownership or destroy the org |
| Manager | Tenant / branch-scoped | Operational oversight of assigned branches |
| Accountant | Tenant | Journals, periods, reports, reconciliation |
| Cashier | Branch | POS sessions, cash sales, assigned till |
| Salesperson | Branch | Sales, customers, quotes/invoices as permitted |
| Inventory Manager | Tenant / branch | Stock, transfers, counts, adjustments |
| Procurement Officer | Tenant / branch | Suppliers, POs, receiving |
| HR Manager | Tenant | Employees, leave, payroll inputs |
| Viewer | Tenant / branch | Read-only permitted modules |
| Grok assistant | Acting as the user | No extra privileges; tools run as the authenticated membership |

## 4. In-scope modules (platform)

| Module | Capability |
| --- | --- |
| Identity | Register, login, sessions, password reset, email verification |
| Tenancy | Organizations, memberships, invitations, org switch |
| Authorization | Roles, permissions, branch access, overrides |
| Organization | Profile, settings, currency, timezone, fiscal calendar |
| Branches & warehouses | Multi-branch, warehouses, transfers |
| Industry config | Packs, enabled modules, attributes, terminology |
| Catalogue | Categories, products, variants, UoM, prices, taxes |
| Inventory | Balances, movements, adjustments, counts, batches/expiry |
| POS & sales | Sessions, cart, payments, receipts, refunds, credit sales |
| Customers | Profiles, credit, loyalty (foundation), notes |
| Suppliers & purchasing | Requisitions, POs, GRN, supplier invoices, payments |
| Expenses | Expense claims/bills, attachments, posting |
| Accounting | COA, periods, journals, AR/AP, banks, statements |
| Employees & payroll | Profiles, attendance/shifts/leave, configurable payroll |
| AI assistant | Tool-calling Grok with approval and metering |
| Reporting | Operational and financial reports, branch vs consolidated |
| Notifications | Email/SMS adapters, in-app |
| Documents | Invoices, receipts, PDFs in object storage |
| SaaS billing | Plans, limits, usage — **separate** from tenant accounting |
| Platform admin | Org lifecycle, monitoring, support tools |
| Localization | English first; resource framework for Zambian languages |
| Integrations | Provider adapters; ZRA Smart Invoice readiness |

## 5. Industry packs (configuration, not forks)

Shared foundation plus progressive extensions:

| Industry | Core extras (phased; not all in first industry release) |
| --- | --- |
| Grocery / supermarket | Barcodes, catch-weight UoM, perishable batches |
| Pharmacy | Batch, expiry, restricted-product permissions, medicine attributes |
| Restaurant | Menus, recipes/BOM-lite, modifiers; KOT/tables as later extension |
| Clothing | Size/colour variants |
| Electronics | Serial-number tracking as later extension |
| Hardware | Units, bulk, variant attributes |
| Wholesale / distribution | Price lists, bulk UoM, credit terms |
| Beauty | Services + retail mix, appointments as later extension |
| Hotel | Rooms/folio as later extension |
| Professional services | Service catalogue, retainers, service invoices; appointments later |
| Manufacturing | BOM/production as later extension |
| General | Catalogue + POS + inventory + accounting |

**Rule:** Industry code lives in `industry/` packs that register schemas, default settings, optional workflows, and UI widgets. Domain tables stay generic (`products.attributes` JSONB validated by pack schema). Do not add `pharmacy_products` as a parallel catalogue.

## 6. Zambia-specific product requirements

- Default currency **ZMW**; amounts stored as `NUMERIC`, never float.
- Address model supports Zambian administrative areas without hard-coding only Zambia (country → admin1 → city/town → area → line fields).
- Tax **categories and rates are data**, effective-dated. No hardcoded VAT percentage in code.
- Receipt/invoice numbering is per organization (and optionally per branch), gap-controlled.
- Mobile money and bank payments: **pending until provider confirmation**.
- ZRA Smart Invoice: adapter + document fields reserved; implementation only against official specs in Phase 14.
- SMS and email notification adapters.
- Locale: English UI first. Translation resource pipeline for Bemba, Nyanja, Tonga, Lozi, Kaonde, Lunda, Luvale — production strings require professional validation.
- Payroll statutory components (PAYE, NAPSA, NHIMA, and any withholding) are **configurable and effective-dated**. Production rates require official verification before go-live.

## 7. Non-goals (v1)

- Offline / local-first POS.
- Native mobile apps (responsive web only).
- Microservices mesh, message buses beyond Redis/Celery/outbox.
- Multi-base-currency accounting inside one organization (single functional currency per org; FX table reserved for later).
- Marketplace / multi-seller.
- Customer-facing e-commerce storefront.
- Full manufacturing MRP.
- Hotel PMS completeness.
- Claiming any payment, SMS, or ZRA certification that has not been tested with real credentials.

## 8. Quality attributes

| Attribute | Target |
| --- | --- |
| Isolation | Cross-tenant access tests must fail closed |
| Consistency | Financial and inventory writes in DB transactions |
| Auditability | Mutations of money, stock, permissions, and AI actions logged |
| Idempotency | Critical POSTs accept `Idempotency-Key` |
| Observability | Structured logs, request IDs, health endpoints |
| Accessibility | Keyboard, labels, contrast on primary flows |
| Recoverability | Backup/restore procedures documented by Phase 15 |

## 9. Success definition for commercial v1 (Zambia)

A grocery, pharmacy, clothing, or general retailer can: onboard, configure tax and COA defaults, run multi-branch stock and POS, receive goods, invoice/credit customers, post expenses, close a period, and produce P&L / balance sheet / trial balance that reconcile to source documents — with users unable to see another tenant’s data.
