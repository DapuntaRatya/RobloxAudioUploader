import json
from datetime import datetime, timezone

from app.db.sqlite import fetchall, insert_and_get_id


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_event(row: dict) -> dict:
    data_raw = row.pop("data_json", None)
    return {
        "event_id": row["id"],
        "job_id": row["job_id"],
        "item_id": row["item_id"],
        "type": row["event_type"],
        "level": row["level"],
        "message": row["message"],
        "data": json.loads(data_raw) if data_raw else None,
        "created_at": row["created_at"],
    }


class EventRepository:
    async def insert(
        self,
        *,
        job_id: str,
        item_id: str | None,
        event_type: str,
        level: str,
        message: str,
        data,
    ) -> dict:
        event_id = await insert_and_get_id(
            """
            INSERT INTO upload_events (
                job_id, item_id, event_type, level, message, data_json, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                job_id,
                item_id,
                event_type,
                level,
                message,
                json.dumps(data) if data is not None else None,
                now(),
            ),
        )

        rows = await fetchall("SELECT * FROM upload_events WHERE id = ?", (event_id,))
        return parse_event(rows[0])

    async def list_by_job_after(self, job_id: str, after_event_id: int = 0, limit: int = 500) -> list[dict]:
        rows = await fetchall(
            """
            SELECT *
            FROM upload_events
            WHERE job_id = ?
              AND id > ?
            ORDER BY id ASC
            LIMIT ?
            """,
            (job_id, after_event_id, limit),
        )
        return [parse_event(row) for row in rows]
