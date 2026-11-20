import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_ready_requires_database_and_schema(client: AsyncClient) -> None:
    response = await client.get("/api/v1/health/ready")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["checks"]["database"] == "ok"
    assert body["checks"]["schema_phase"] == "1"
    assert body["checks"]["redis"] in {"ok", "memory"}
