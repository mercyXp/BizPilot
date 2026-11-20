import os

os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("DEMO_COMPACT", "true")
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+asyncpg://bizpilot_app@127.0.0.1:55432/bizpilot",
)
os.environ.setdefault(
    "DATABASE_URL_SYNC",
    "postgresql+psycopg://bizpilot@127.0.0.1:55432/bizpilot",
)

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
async def client() -> AsyncClient:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
