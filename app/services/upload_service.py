from app.config import settings
from app.core.errors import JobError
from app.modules.downloader.registry import registry
from app.repositories.job_repository import JobRepository
from app.schemas.upload_schema import UploadRequest
from app.services.event_service import EventService
from app.services.queue_service import QueueService


class UploadService:
    def __init__(self):
        self.jobs = JobRepository()
        self.queue = QueueService()
        self.events = EventService()

    async def create_upload_job(self, *, session: dict, payload: UploadRequest) -> dict:
        registry.get(payload.source_type)

        active_count = await self.jobs.active_jobs_count(session["session_id"])
        if active_count >= settings.MAX_ACTIVE_JOBS_PER_SESSION:
            raise JobError(
                "TOO_MANY_ACTIVE_JOBS",
                f"Maksimal {settings.MAX_ACTIVE_JOBS_PER_SESSION} job aktif per session.",
                status_code=429,
            )

        options = payload.options.model_dump()

        job = await self.jobs.create_job(
            session_id=session["session_id"],
            authorized_user_id=session["authorized_user_id"],
            source_type=payload.source_type,
            audio_links=payload.audio_links,
            experience_ids=payload.experience_ids,
            options=options,
        )

        await self.events.publish(
            job_id=job["job_id"],
            event_type="job_created",
            level="success",
            message=f"Job dibuat: {job['job_id']}",
            data={
                "job_id": job["job_id"],
                "source_type": payload.source_type,
                "total_audio": len(payload.audio_links),
                "total_experience": len(payload.experience_ids),
            },
        )

        await self.queue.enqueue_upload_job(job["job_id"])

        return job
