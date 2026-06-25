import asyncio
from typing import Optional

_upload_queue: asyncio.Queue[str] = asyncio.Queue()


class QueueService:
    async def enqueue_upload_job(self, job_id: str) -> None:
        await _upload_queue.put(job_id)

    async def wait_for_upload_job(self) -> str:
        return await _upload_queue.get()

    def task_done(self) -> None:
        _upload_queue.task_done()

    def size(self) -> int:
        return _upload_queue.qsize()
