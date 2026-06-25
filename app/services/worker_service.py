import asyncio

from app.config import settings
from app.core.logger import get_logger
from app.repositories.job_repository import JobRepository
from app.services.queue_service import QueueService
from app.services.upload_orchestrator import UploadOrchestrator, init_semaphores

logger = get_logger("rau.worker")


class WorkerService:
    def __init__(self):
        self.queue = QueueService()
        self.jobs = JobRepository()
        self.orchestrator = UploadOrchestrator()
        self.tasks: list[asyncio.Task] = []
        self.stopping = False

    async def start(self) -> None:
        init_semaphores(
            settings.MAX_DOWNLOAD_CONCURRENT,
            settings.MAX_ROBLOX_UPLOAD_CONCURRENT,
            settings.MAX_PERMISSION_CONCURRENT,
        )

        await self.jobs.recover_running_as_failed()

        for job_id in await self.jobs.list_queued_jobs():
            await self.queue.enqueue_upload_job(job_id)

        self.tasks = [
            asyncio.create_task(self.worker_loop(index + 1))
            for index in range(settings.WORKER_COUNT)
        ]
        logger.info("Started %s in-process worker(s).", len(self.tasks))

    async def stop(self) -> None:
        self.stopping = True

        for task in self.tasks:
            task.cancel()

        await asyncio.gather(*self.tasks, return_exceptions=True)
        self.tasks = []
        logger.info("Stopped workers.")

    async def worker_loop(self, worker_id: int) -> None:
        logger.info("Worker %s ready.", worker_id)

        while not self.stopping:
            try:
                job_id = await self.queue.wait_for_upload_job()
                logger.info("Worker %s processing %s", worker_id, job_id)
                await self.orchestrator.process_job(job_id)
                self.queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.exception("Worker %s error: %s", worker_id, exc)
