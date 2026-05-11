from .config import settings

_pool = None


async def get_redis():
    global _pool
    if not settings.redis_enabled:
        return _NullRedis()
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
    """No-op Redis when Redis is not available."""
    async def get(self, key): return None
    async def set(self, key, value): pass
    async def setex(self, key, ttl, value): pass
    async def delete(self, key): pass
    async def incr(self, key): return 1
    async def expire(self, key, ttl): pass
