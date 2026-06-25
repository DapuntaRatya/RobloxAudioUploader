import asyncio

from app.db.sqlite import close_db, init_db


async def main():
    await init_db()
    await close_db()
    print("SQLite initialized.")


if __name__ == "__main__":
    asyncio.run(main())
