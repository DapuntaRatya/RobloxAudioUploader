import asyncio
from datetime import datetime, timezone

TERMINAL_EVENTS = {"job_done", "job_failed", "job_cancelled"}


class EventBus:
    def __init__(self):
        self._events = {}
        self._conditions = {}

    def _condition(self, job_id: str):
        if job_id not in self._conditions:
            self._conditions[job_id] = asyncio.Condition()
        return self._conditions[job_id]

    def has_job(self, job_id: str) -> bool:
        return job_id in self._events

    async def publish(self, job_id: str, event_type: str, message: str, *, level="info", item_id=None, data=None):
        events = self._events.setdefault(job_id, [])
        event = {
            "event_id": len(events) + 1,
            "job_id": job_id,
            "item_id": item_id,
            "type": event_type,
            "level": level,
            "message": message,
            "data": data,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        condition = self._condition(job_id)
        async with condition:
            events.append(event)
            condition.notify_all()
        return event

    def is_terminal(self, job_id: str) -> bool:
        events = self._events.get(job_id, [])
        return bool(events and events[-1].get("type") in TERMINAL_EVENTS)

    async def subscribe(self, job_id: str, after_event_id: int = 0):
        index = max(after_event_id, 0)
        while True:
            events = self._events.get(job_id, [])
            while index < len(events):
                event = events[index]
                index += 1
                yield event
            if self.is_terminal(job_id):
                break
            condition = self._condition(job_id)
            async with condition:
                await condition.wait()
