import pytest
from pydantic import ValidationError

from app.core.config import Settings
from app.ops.release import alter_role_password_sql
from app.core.dsn import app_async_url, ensure_ssl, owner_sync_url, replace_user, with_sqlalchemy_driver


def test_render_postgres_url_becomes_asyncpg_with_ssl() -> None:
    raw = "postgres://bizpilot:o%2Fwn@dpg-abc-a.frankfurt-postgres.render.com:5432/bizpilot"
    url = app_async_url(raw, app_role="bizpilot_app", app_password="s#cret")
    assert url.startswith("postgresql+asyncpg://")
    assert "bizpilot_app:" in url
    assert "ssl=require" in url
    assert "s%23cret" in url or "s#cret" in url


def test_local_urls_do_not_force_ssl() -> None:
    raw = "postgresql+asyncpg://bizpilot_app@127.0.0.1:55432/bizpilot"
    assert "ssl=" not in app_async_url(raw)
    assert "sslmode=" not in owner_sync_url(raw, None)


def test_sync_url_derived_from_owner_when_unset() -> None:
    raw = "postgres://bizpilot:pass@db.example.render.com/bizpilot"
    sync = owner_sync_url(raw, None)
    assert sync.startswith("postgresql+psycopg://bizpilot:pass@")
    assert "sslmode=require" in sync


def test_replace_user_keeps_host_and_db() -> None:
    url = replace_user(
        "postgresql+asyncpg://old:pw@db.example.render.com:5432/bizpilot",
        "bizpilot_app",
        "newpw",
    )
    assert url == "postgresql+asyncpg://bizpilot_app:newpw@db.example.render.com:5432/bizpilot"


def test_with_sqlalchemy_driver_strips_existing_driver() -> None:
    assert with_sqlalchemy_driver(
        "postgresql+asyncpg://u:p@h/db", "psycopg"
    ) == "postgresql+psycopg://u:p@h/db"


def test_production_settings_rewrite_to_app_role() -> None:
    settings = Settings(
        app_env="production",
        secret_key="not-the-dev-placeholder-key",
        database_url="postgres://bizpilot:owner@db.example.render.com/bizpilot",
        database_url_sync="",
        bizpilot_app_password="app-secret",
        resend_api_key="re_test",
        resend_from_email="BizPilot <noreply@example.com>",
        redis_url="redis://red-abc:6379",
    )
    assert "bizpilot_app" in settings.database_url
    assert "postgresql+asyncpg://" in settings.database_url
    assert "postgresql+psycopg://bizpilot:owner@" in settings.database_url_sync
    assert "ssl=require" in settings.database_url


def test_production_settings_require_app_password() -> None:
    with pytest.raises(ValidationError):
        Settings(
            app_env="production",
            secret_key="not-the-dev-placeholder-key",
            database_url="postgres://bizpilot:owner@db.example.render.com/bizpilot",
            bizpilot_app_password="",
        )


def test_ensure_ssl_skips_loopback() -> None:
    url = "postgresql+asyncpg://bizpilot_app@127.0.0.1:55432/bizpilot"
    assert ensure_ssl(url, async_driver=True) == url


def test_alter_role_password_sql_quotes_literal_not_placeholder() -> None:
    rendered = alter_role_password_sql("bizpilot_app", "p'ass$1").as_string(None)
    assert "$1" not in rendered.replace("'p''ass$1'", "")
    assert "PASSWORD 'p''ass$1'" in rendered
    assert '"bizpilot_app"' in rendered
