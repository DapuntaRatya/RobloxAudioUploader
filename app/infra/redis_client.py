import redis.asyncio as redis

from app.config import settings

_redis: redis.Redis | None = None


async def init_redis() -> None:
    global _redis
    if _redis is None:
        _redis = redis.from_url(settings.REDIS_URL, decode_responses=True)
        await _redis.ping()


async def close_redis() -> None:
    global _redis
    if _redis is not None:
        await _redis.aclose()
        _redis = None


def redis_client() -> redis.Redis:
    if _redis is None:
        raise RuntimeError("Redis client belum diinisialisasi.")
    return _redis
