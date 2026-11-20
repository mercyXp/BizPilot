# BizPilot development setup

Phase 1 runs a Next.js app, a FastAPI API, PostgreSQL, and an optional Redis server.

## Prerequisites

- Python 3.12+
- Node.js 20+
- PostgreSQL 16+ client/server binaries (Docker **or** a local install)

Docker is optional. This machine’s Phase 1 path uses a **project-local PostgreSQL cluster** on port `55432` so it does not collide with other Postgres instances.

## Environment

```powershell
copy .env.example .env
```

Do not commit `.env`. `SECRET_KEY` in the example is for local development only.

`REDIS_URL=memory://` is allowed in development when Redis is not installed. Production must use a real Redis URL.

Transactional mail uses [Resend](https://resend.com). Set `RESEND_API_KEY` and `RESEND_FROM_EMAIL` (a verified domain). With `APP_ENV=development` and an empty key, the API records `outbound_emails` and does not call Resend. `APP_ENV=test` never calls Resend. Staging and production refuse to send (and `/health/ready` fails) until the key is set.

The API runtime role is `bizpilot_app` (no RLS bypass). Alembic uses the cluster owner `bizpilot`.

If you use `docker compose up -d`, still run Alembic as the superuser, then point `DATABASE_URL` at `bizpilot_app`.

## PostgreSQL (local, no Docker)

```powershell
.\scripts\start-local-postgres.ps1
```

Creates `.data/postgres` (gitignored), user `bizpilot`, database `bizpilot`, port `55432`, trust auth on localhost.

## Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
alembic upgrade head
pytest
uvicorn app.main:app --reload --port 8000
```

Checks:

- `GET http://localhost:8000/health`
- `GET http://localhost:8000/api/v1/health`
- `GET http://localhost:8000/api/v1/health/ready`

## Frontend

This workstation’s `registry.npmjs.org` returns HTTP 403. `frontend/.npmrc` therefore uses `https://registry.npmmirror.com`. If your network can use the public npm registry, change that file.

```powershell
cd frontend
pnpm install
pnpm typecheck
pnpm lint
pnpm test
pnpm build
pnpm dev
```

Open `http://localhost:3000`. The marketing header uses `frontend/public/logo/BizPilot_logo.png` via `Logo`. Pricing is at `/pricing` (Basic Free, Premium K320, Entreprise K490). `/login` redirects to `/sign-in`. The home page fetches FastAPI readiness over `NEXT_PUBLIC_API_URL`.

After `alembic upgrade head`, `/api/v1/health/ready` should report `schema_phase` `11`. GitHub Actions runs pytest and vitest on every pull request. Production API + Postgres + Redis deploy on Render; see [render.md](render.md). Other go-live gates are in [production-checklist.md](production-checklist.md).

## API versioning

Business routes live under `/api/v1`. Additive changes stay on v1. Breaking changes require `/api/v2`.
