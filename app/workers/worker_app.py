import asyncio
import signal

from app.core.logger import get_logger
from app.db.pool import close_db_pool, init_db_pool
from app.infra.redis_client import close_redis, init_redis
from app.services.queue_service import QueueService
from app.workers.upload_worker import UploadWorker

logger = get_logger("rau.worker")
should_stop = asyncio.Event()


def request_stop(*_):
    should_stop.set()


async def main():
    signal.signal(signal.SIGTERM, request_stop)
    signal.signal(signal.SIGINT, request_stop)

    await init_db_pool()
    await init_redis()

    queue = QueueService()
    worker = UploadWorker()

    logger.info("RAU worker started.")

    try:
        while not should_stop.is_set():
            job_id = await queue.wait_for_upload_job(timeout=5)
            if not job_id:
                continue

            logger.info("Processing job %s", job_id)
            await worker.process_job(job_id)

    finally:
        await close_redis()
        await close_db_pool()
        logger.info("RAU worker stopped.")


if __name__ == "__main__":
    asyncio.run(main())
