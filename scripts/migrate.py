import asyncio
from pathlib import Path

import asyncpg
from dotenv import load_dotenv

from app.config import settings

load_dotenv()


async def main():
    conn = await asyncpg.connect(dsn=settings.POSTGRES_DSN)
    try:
        migration_dir = Path("app/db/migrations")
        for path in sorted(migration_dir.glob("*.sql")):
            print(f"Running migration: {path}")
            await conn.execute(path.read_text(encoding="utf-8"))
        print("Migration done.")
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
