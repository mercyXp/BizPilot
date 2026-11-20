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

If you use `docker compose up -d`, set:

```
DATABASE_URL=postgresql+asyncpg://bizpilot:bizpilot@127.0.0.1:55432/bizpilot
DATABASE_URL_SYNC=postgresql+psycopg://bizpilot:bizpilot@127.0.0.1:55432/bizpilot
REDIS_URL=redis://127.0.0.1:6379/0
```

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
pnpm test
pnpm dev
```

Open `http://localhost:3000`. The home page fetches FastAPI readiness over `NEXT_PUBLIC_API_URL`.

## API versioning

Business routes live under `/api/v1`. Additive changes stay on v1. Breaking changes require `/api/v2`.
