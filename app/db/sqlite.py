from pathlib import Path
from typing import Any

import aiosqlite

from app.config import settings

_conn: aiosqlite.Connection | None = None


def row_to_dict(row: aiosqlite.Row | None) -> dict | None:
    if row is None:
        return None
    return dict(row)


async def init_db() -> None:
    global _conn
    if _conn is not None:
        return

    settings.DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    _conn = await aiosqlite.connect(settings.DATABASE_PATH)
    _conn.row_factory = aiosqlite.Row

    await _conn.execute("PRAGMA journal_mode = WAL")
    await _conn.execute("PRAGMA foreign_keys = ON")

    schema_path = Path(__file__).resolve().parent / "schema.sql"
    await _conn.executescript(schema_path.read_text(encoding="utf-8"))
    await _conn.commit()


async def close_db() -> None:
    global _conn
    if _conn is not None:
        await _conn.close()
        _conn = None


def db() -> aiosqlite.Connection:
    if _conn is None:
        raise RuntimeError("SQLite belum diinisialisasi.")
    return _conn


async def execute(query: str, args: tuple = ()) -> None:
    await db().execute(query, args)
    await db().commit()


async def fetchone(query: str, args: tuple = ()) -> dict | None:
    cursor = await db().execute(query, args)
    row = await cursor.fetchone()
    await cursor.close()
    return row_to_dict(row)


async def fetchall(query: str, args: tuple = ()) -> list[dict]:
    cursor = await db().execute(query, args)
    rows = await cursor.fetchall()
    await cursor.close()
    return [dict(row) for row in rows]


async def insert_and_get_id(query: str, args: tuple = ()) -> int:
    cursor = await db().execute(query, args)
    await db().commit()
    last_id = cursor.lastrowid
    await cursor.close()
    return int(last_id)
