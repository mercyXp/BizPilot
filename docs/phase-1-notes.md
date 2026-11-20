# Phase 1 notes

## Runtime choices

- Project-local PostgreSQL 18 cluster on port 55432 (`scripts/start-local-postgres.ps1`) because Docker is not installed and the system PostgreSQL instance uses 5433 with unknown credentials.
- `REDIS_URL=memory://` in development when Redis is not installed. Ready checks report `redis: memory`. Production must use `redis://`.
- Access JWT and RBAC are not implemented yet (Phase 2).

## Environment

Secrets live in `.env` (gitignored). `.env.example` is the committed template.
