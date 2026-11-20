from typing import Protocol

from redis.asyncio import Redis

from app.core.config import get_settings

_memory_store: dict[str, str] = {}


class CacheClient(Protocol):
    async def ping(self) -> bool: ...
    async def close(self) -> None: ...


class MemoryCache:
    """In-process cache for local development when Redis is not installed."""

    async def ping(self) -> bool:
        _memory_store.setdefault("__health__", "ok")
        return True

    async def close(self) -> None:
        return None


_client: CacheClient | None = None


async def get_cache() -> CacheClient:
    global _client
    if _client is not None:
        return _client

    settings = get_settings()
    if settings.uses_memory_redis:
        _client = MemoryCache()
        return _client

    _client = Redis.from_url(settings.redis_url, decode_responses=True)
    return _client


async def close_cache() -> None:
    global _client
    if _client is not None:
        await _client.close()
        _client = None
