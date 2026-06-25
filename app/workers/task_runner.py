import asyncio
from typing import Awaitable


def run_background(coro: Awaitable) -> asyncio.Task:
    return asyncio.create_task(coro)
