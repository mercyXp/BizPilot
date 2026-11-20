import os
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1 import api_router
from app.core.config import get_settings
from app.core.db import engine
from app.core.errors import register_error_handlers
from app.core.logging import configure_logging
from app.core.middleware import register_middleware
from app.core.redis import close_cache, get_cache


@asynccontextmanager
async def lifespan(_app: FastAPI):
    settings = get_settings()
    configure_logging(settings.log_level)
    await get_cache()
    yield
    await close_cache()
    if os.environ.get("PYTEST_CURRENT_TEST"):
        return
    await engine.dispose()


def create_app() -> FastAPI:
    settings = get_settings()
    application = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/docs" if not settings.is_production else None,
        redoc_url=None,
        openapi_url="/openapi.json" if not settings.is_production else None,
    )
    register_middleware(application, settings)
    register_error_handlers(application)
    application.include_router(api_router, prefix=settings.api_v1_prefix)

    @application.get("/health")
    async def root_health() -> dict:
        return {"status": "ok", "service": settings.app_name}

    return application


app = create_app()
