# BizPilot

Multi-tenant business management SaaS. Initial market: Zambia. Default currency: ZMW.

This repository is a modular monolith: Next.js (`frontend/`) and FastAPI (`backend/`) sharing one PostgreSQL database.

## Current phase

Phase 3 — role-based access control. Register, login, organizations, branches, and row-level security are in place so permissions can be enforced. Refresh tokens, email verification, and invitations are still outstanding.

Architecture: `docs/TECHNICAL_RECORD.md` and `docs/phase-0/`.

## Quick start

See [docs/setup.md](docs/setup.md).
