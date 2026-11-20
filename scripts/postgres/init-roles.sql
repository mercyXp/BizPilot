-- Local Docker role used by the API. Alembic repeats this if the role is missing.
-- The password is the local development password from .env.example, not a production secret.
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'bizpilot_app') THEN
    CREATE ROLE bizpilot_app LOGIN PASSWORD 'bizpilot'
      NOSUPERUSER NOBYPASSRLS NOCREATEDB NOCREATEROLE;
  END IF;
END
$$;

GRANT CONNECT ON DATABASE bizpilot TO bizpilot_app;
GRANT USAGE ON SCHEMA public TO bizpilot_app;
