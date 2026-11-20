# Production checklist (Phase 15)

Do not mark a Zambia tax, mobile-money, or ZRA item live unless credentials and official provider docs exist. This checklist does not invent those integrations.

## Before first production traffic

- [ ] `APP_ENV=production`
- [ ] `SECRET_KEY` is unique, stored in a secret manager, not in git
- [ ] `DATABASE_URL` uses `bizpilot_app` (no `BYPASSRLS`)
- [ ] Alembic runs as a privileged owner (`DATABASE_URL_SYNC`) then the app uses the RLS role
- [ ] `REDIS_URL` is a real Redis instance (`memory://` is development only)
- [ ] `CORS_ORIGINS` lists only the production frontend origin
- [ ] `PUBLIC_APP_URL` matches the public site
- [ ] `RESEND_API_KEY` and `RESEND_FROM_EMAIL` are set (domain verified in Resend)
- [ ] Ready check reports `email` as `resend` (not `missing` / `log_only`)
- [ ] TLS terminates in front of FastAPI and Next.js
- [ ] OpenAPI docs are off in production (`/docs` is disabled when `APP_ENV=production`)
- [ ] Demo mode is off (`DEMO_ENABLED=false`) unless a dedicated demo environment
- [ ] PostgreSQL backups: nightly `pg_dump` (or managed snapshots) plus a restore drill
- [ ] Log aggregation on API access, auth failures, and 5xx
- [ ] Uptime checks against `GET /api/v1/health` and `GET /api/v1/health/ready`
- [ ] Ready check reports `schema_phase` matching the latest applied migration (currently `11`)
- [ ] CI is green on `main` (pytest + vitest + typecheck)

## Data and isolation

- [ ] Cross-tenant tests still pass (no org A data on org B tokens)
- [ ] Cashier cannot call `/api/v1/reporting/*` (`reports.view`)
- [ ] Accounting statements stay behind `accounting.reports.view`
- [ ] Tax report UI still labelled DEV_ONLY / not an official ZRA filing

## Operations

- Restore drill: restore the latest dump into a scratch database and run `alembic current`
- Backup retention: keep at least 14 daily dumps (or the equivalent managed PITR window)
- Incident: rotate `SECRET_KEY` only with a planned session invalidation

## Explicitly not production-ready (do not claim)

- Live ZRA Smart Invoice / Smart Invoice API
- Airtel Money, MTN MoMo, or Zamtel production webhooks
- Official Zambia VAT, PAYE, NAPSA, or NHIMA rate tables
- Phase 10 Grok write tools
- Phase 13 SaaS billing collection
