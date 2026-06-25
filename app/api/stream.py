import json

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from app.core.errors import JobError
from app.dependencies import require_session
from app.repositories.job_repository import JobRepository
from app.services.event_service import EventService

router = APIRouter()
job_repo = JobRepository()
event_service = EventService()


def sse_format(event: dict) -> str:
    if event.get("type") == "__ping__":
        return ": ping\n\n"

    event_name = event.get("type", "message")
    event_id = event.get("event_id", "")
    data = json.dumps(event, ensure_ascii=False)
    return f"id: {event_id}\nevent: {event_name}\ndata: {data}\n\n"


@router.get("/api/upload/{job_id}/events")
async def upload_events(job_id: str, request: Request):
    session = await require_session(request)
    job = await job_repo.get_job(job_id)

    if not job or job["session_id"] != session["session_id"]:
        raise JobError("JOB_NOT_FOUND", "Job tidak ditemukan.", status_code=404)

    last_id_raw = request.headers.get("last-event-id") or "0"
    try:
        last_id = int(last_id_raw)
    except ValueError:
        last_id = 0

    async def generator():
        async for event in event_service.subscribe(job_id, after_event_id=last_id):
            if await request.is_disconnected():
                break
            yield sse_format(event)

    return StreamingResponse(
        generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
