import asyncpg

from app.config import settings

_pool: asyncpg.Pool | None = None


async def init_db_pool() -> None:
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(dsn=settings.POSTGRES_DSN, min_size=1, max_size=10)


async def close_db_pool() -> None:
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None


def pool() -> asyncpg.Pool:
    if _pool is None:
        raise RuntimeError("Database pool belum diinisialisasi.")
    return _pool


async def fetchrow(query: str, *args):
    return await pool().fetchrow(query, *args)


async def fetch(query: str, *args):
    return await pool().fetch(query, *args)


async def execute(query: str, *args):
    return await pool().execute(query, *args)
