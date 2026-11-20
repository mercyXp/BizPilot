import time

from app.core.redis import get_cache


class MemoryRateLimiter:
    def __init__(self) -> None:
        self._hits: dict[str, list[float]] = {}

    async def hit(self, key: str, limit: int, window_seconds: int) -> bool:
        now = time.time()
        bucket = [ts for ts in self._hits.get(key, []) if now - ts < window_seconds]
        if len(bucket) >= limit:
            self._hits[key] = bucket
            return False
        bucket.append(now)
        self._hits[key] = bucket
        return True


_memory = MemoryRateLimiter()


async def allow_attempt(key: str, limit: int, window_seconds: int) -> bool:
    cache = await get_cache()
    ping = getattr(cache, "incr", None)
    if ping is None:
        return await _memory.hit(key, limit, window_seconds)
    return await _memory.hit(key, limit, window_seconds)
