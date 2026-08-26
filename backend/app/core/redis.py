from .config import settings

_pool = None


async def get_redis():
    global _pool
    if not settings.redis_enabled:
        return _null_redis
    if _pool is None:
        import redis.asyncio as aioredis
        _pool = aioredis.from_url(settings.redis_url, encoding="utf-8", decode_responses=True)
    return _pool


async def close_redis():
    global _pool
    if _pool and settings.redis_enabled:
        await _pool.aclose()
        _pool = None


class _NullRedis:
    """In-process store when Redis is off — revoke/login counters survive the request."""

    def __init__(self):
        self._store: dict = {}

    async def get(self, key):
        return self._store.get(key)

    async def set(self, key, value):
        self._store[key] = value

    async def setex(self, key, ttl, value):
        self._store[key] = value

    async def delete(self, key):
        self._store.pop(key, None)

    async def incr(self, key):
        self._store[key] = int(self._store.get(key) or 0) + 1
        return self._store[key]

    async def expire(self, key, ttl):
        return True


_null_redis = _NullRedis()
