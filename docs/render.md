# Render production (API, Postgres, Redis)

The Next.js app stays on Vercel. FastAPI, PostgreSQL 16, and Redis run on Render from `render.yaml`.

## Create the Blueprint

1. Open [Render Blueprints](https://dashboard.render.com/blueprints) and connect `mercyXp/BizPilot`.
2. Use this file: `render.yaml` (Frankfurt). Database name/user `bizpilot` and region cannot change later.
3. When prompted, set:
   - `RESEND_API_KEY`
   - `RESEND_FROM_EMAIL` (verified domain, e.g. `BizPilot <noreply@yourdomain>`)
4. Apply the Blueprint. Render generates `SECRET_KEY` and `BIZPILOT_APP_PASSWORD`.
5. Copy the API URL (`https://bizpilot-api.onrender.com`, or the name Render assigned).

Each deploy runs `python -m app.ops.release`: Alembic as the owner role, then `ALTER ROLE bizpilot_app` so the web process never uses `BYPASSRLS`.

## Point Vercel at the API

On `bizpilot_frontend`, set:

```
NEXT_PUBLIC_API_URL=https://bizpilot-api.onrender.com
```

(production and preview). The Next.js rewrite proxies `/api/v1/*` so the `bp_refresh` cookie stays on the Vercel origin.

If you add a custom frontend domain, also update Render `PUBLIC_APP_URL` and `CORS_ORIGINS`.

## Checks

- `GET https://<api>/health`
- `GET https://<api>/api/v1/health/ready` → `database=ok`, `email=resend`, `redis=ok`, `schema_phase=11`

Do not commit Render or Resend secrets. Local development still uses `.env` and port `55432`.
