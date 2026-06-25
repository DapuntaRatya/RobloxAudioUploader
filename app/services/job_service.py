import time
import uuid
from dataclasses import dataclass, field
from typing import Optional
from app.schemas.upload_schema import UploadRequest
from app.services.session_service import SessionData


@dataclass
class UploadJob:
    job_id: str
    session: SessionData
    request: UploadRequest
    status: str = "created"
    created_at: float = field(default_factory=time.time)
    task: Optional[object] = None


class JobService:
    def __init__(self):
        self._jobs = {}

    def create_job(self, *, session: SessionData, request: UploadRequest) -> UploadJob:
        job = UploadJob(job_id=f"job_{uuid.uuid4().hex[:16]}", session=session, request=request)
        self._jobs[job.job_id] = job
        return job

    def get_job(self, job_id: str):
        return self._jobs.get(job_id)

    def set_task(self, job_id: str, task: object):
        if job := self.get_job(job_id):
            job.task = task

    def set_status(self, job_id: str, status: str):
        if job := self.get_job(job_id):
            job.status = status
