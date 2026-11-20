from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import text
from app.core.config import Settings, get_settings
from app.core.db import SessionLocal
from app.core.redis import get_cache

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_live(settings: Settings = Depends(get_settings)) -> dict:
    return {
        "status": "ok",
        "service": settings.app_name,
        "environment": settings.app_env,
        "api": "v1",
    }


@router.get("/health/ready")
async def health_ready(settings: Settings = Depends(get_settings)) -> dict:
    checks: dict[str, str] = {}
    failures: list[str] = []

    try:
        async with SessionLocal() as db:
            await db.execute(text("SELECT 1"))
            checks["database"] = "ok"
            try:
                version = await db.execute(
                    text("SELECT value FROM app_metadata WHERE key = 'schema_phase'")
                )
                schema_phase = version.scalar_one_or_none()
                checks["schema_phase"] = schema_phase or "missing"
                if schema_phase is None:
                    failures.append("schema")
            except Exception:
                checks["schema_phase"] = "unavailable"
                failures.append("schema")
    except Exception:
        checks["database"] = "unavailable"
        failures.append("database")

    try:
        cache = await get_cache()
        await cache.ping()
        checks["redis"] = "memory" if settings.uses_memory_redis else "ok"
    except Exception:
        checks["redis"] = "unavailable"
        failures.append("redis")

    from app.core.email import email_delivery_mode

    checks["email"] = email_delivery_mode(settings)
    if checks["email"] == "missing":
        failures.append("email")

    payload = {
        "status": "ok" if not failures else "unavailable",
        "service": settings.app_name,
        "checks": checks,
    }
    if failures:
        return JSONResponse(status_code=503, content=payload)
    return payload
