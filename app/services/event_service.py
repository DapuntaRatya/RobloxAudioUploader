import asyncio
from collections import defaultdict
from typing import Any, AsyncGenerator

from app.repositories.event_repository import EventRepository

_conditions: dict[str, asyncio.Condition] = defaultdict(asyncio.Condition)
_terminal_events = {"job_done", "job_failed", "job_cancelled"}


class EventService:
    def __init__(self):
        self.repo = EventRepository()

    async def publish(
        self,
        *,
        job_id: str,
        event_type: str,
        message: str,
        level: str = "info",
        item_id: str | None = None,
        data: Any = None,
    ) -> dict:
        event = await self.repo.insert(
            job_id=job_id,
            item_id=item_id,
            event_type=event_type,
            level=level,
            message=message,
            data=data,
        )

        condition = _conditions[job_id]
        async with condition:
            condition.notify_all()

        return event

    async def subscribe(self, job_id: str, after_event_id: int = 0) -> AsyncGenerator[dict, None]:
        last_id = max(int(after_event_id or 0), 0)

        while True:
            events = await self.repo.list_by_job_after(job_id, last_id)
            for event in events:
                last_id = event["event_id"]
                yield event

                if event.get("type") in _terminal_events:
                    return

            condition = _conditions[job_id]
            try:
                async with condition:
                    await asyncio.wait_for(condition.wait(), timeout=15)
            except asyncio.TimeoutError:
                yield {"type": "__ping__", "event_id": last_id}
