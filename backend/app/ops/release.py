"""Apply migrations as the Postgres owner, then set the RLS app-role password.

Render injects DATABASE_URL as the owner connection string. The API must connect
as bizpilot_app (NOBYPASSRLS). This command is safe to run on every deploy.
"""

from __future__ import annotations

import logging
import sys

import psycopg
from alembic import command
from alembic.config import Config
from psycopg import sql

from app.core.config import get_settings
from app.core.dsn import as_libpq_url

logger = logging.getLogger(__name__)

APP_ROLE = "bizpilot_app"


def alter_role_password_sql(role: str, password: str) -> sql.Composed:
    # ALTER ROLE does not accept bind parameters ($1); the password must be a SQL literal.
    return sql.SQL("ALTER ROLE {} WITH LOGIN PASSWORD {}").format(
        sql.Identifier(role),
        sql.Literal(password),
    )


def _alembic_upgrade(sync_url: str) -> None:
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", sync_url.replace("%", "%%"))
    command.upgrade(config, "head")


def _ensure_app_role(sync_url: str, password: str) -> None:
    dsn = as_libpq_url(sync_url)
    with psycopg.connect(dsn, autocommit=True) as conn:
        conn.execute(
            """
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'bizpilot_app') THEN
                    CREATE ROLE bizpilot_app LOGIN NOSUPERUSER NOBYPASSRLS
                        NOCREATEDB NOCREATEROLE NOINHERIT;
                END IF;
            END
            $$;
            """
        )
        conn.execute(alter_role_password_sql(APP_ROLE, password))
        row = conn.execute("SELECT current_database()").fetchone()
        if row is None:
            raise RuntimeError("Could not read current_database()")
        conn.execute(
            sql.SQL("GRANT CONNECT ON DATABASE {} TO bizpilot_app").format(sql.Identifier(row[0]))
        )


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    settings = get_settings()
    logger.info("release migrate env=%s", settings.app_env)
    _alembic_upgrade(settings.database_url_sync)
    if settings.uses_managed_app_role:
        if not settings.bizpilot_app_password.strip():
            logger.error("BIZPILOT_APP_PASSWORD is required in %s", settings.app_env)
            return 1
        _ensure_app_role(settings.database_url_sync, settings.bizpilot_app_password.strip())
        logger.info("app role %s password set", APP_ROLE)
    return 0


if __name__ == "__main__":
    sys.exit(main())
