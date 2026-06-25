import json
from datetime import datetime, timezone

from app.core.security import generate_id
from app.db.sqlite import db, execute, fetchall, fetchone


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_job(row: dict | None) -> dict | None:
    if not row:
        return None
    row["experience_ids"] = json.loads(row.pop("experience_ids_json") or "[]")
    row["options"] = json.loads(row.pop("options_json") or "{}")
    return row


def parse_item(row: dict | None) -> dict | None:
    if not row:
        return None
    if "error_details_json" in row:
        raw = row.pop("error_details_json")
        row["error_details"] = json.loads(raw) if raw else None
    return row


def parse_json_maybe(value, default=None):
    if default is None:
        default = {}
    if not value:
        return default
    try:
        return json.loads(value)
    except Exception:
        return default


def seconds_to_length(seconds) -> str:
    if seconds is None:
        return "-"
    try:
        total = int(float(seconds))
    except Exception:
        return "-"
    minutes = total // 60
    sec = total % 60
    return f"{minutes}:{sec:02d}"


class JobRepository:
    async def create_job(
        self,
        *,
        session_id: str,
        authorized_user_id: str,
        source_type: str,
        audio_links: list[str],
        experience_ids: list[str],
        options: dict,
    ) -> dict:
        job_id = generate_id("job")

        async with db().execute("BEGIN"):
            await db().execute(
                """
                INSERT INTO upload_jobs (
                    job_id, session_id, authorized_user_id, source_type, status,
                    total_items, experience_ids_json, options_json
                )
                VALUES (?, ?, ?, ?, 'queued', ?, ?, ?)
                """,
                (
                    job_id,
                    session_id,
                    authorized_user_id,
                    source_type,
                    len(audio_links),
                    json.dumps(experience_ids),
                    json.dumps(options),
                ),
            )

            for index, url in enumerate(audio_links, start=1):
                await db().execute(
                    """
                    INSERT INTO upload_items (
                        item_id, job_id, item_index, source_url, status
                    )
                    VALUES (?, ?, ?, ?, 'queued')
                    """,
                    (
                        f"{job_id}_audio_{index}",
                        job_id,
                        index,
                        url,
                    ),
                )

            await db().commit()

        return await self.get_job(job_id)

    async def get_job(self, job_id: str) -> dict | None:
        return parse_job(await fetchone("SELECT * FROM upload_jobs WHERE job_id = ?", (job_id,)))

    async def list_items(self, job_id: str) -> list[dict]:
        rows = await fetchall(
            """
            SELECT *
            FROM upload_items
            WHERE job_id = ?
            ORDER BY item_index ASC
            """,
            (job_id,),
        )
        return [parse_item(row) for row in rows]

    async def list_uploaded_assets_by_authorized_user_id(self, authorized_user_id: str) -> list[dict]:
        rows = await fetchall(
            """
            SELECT
                i.asset_id AS asset_id,
                COALESCE(NULLIF(i.download_title, ''), 'Untitled Audio') AS title,
                i.item_id AS item_id,
                i.job_id AS job_id,
                i.source_url AS source_url,
                i.finished_at AS finished_at,
                i.created_at AS created_at,
                j.source_type AS source_type,
                (
                    SELECT e.data_json
                    FROM upload_events e
                    WHERE e.item_id = i.item_id
                      AND e.event_type = 'download_done'
                    ORDER BY e.id DESC
                    LIMIT 1
                ) AS download_done_data_json,
                (
                    SELECT e.data_json
                    FROM upload_events e
                    WHERE e.item_id = i.item_id
                      AND e.event_type = 'upload_done'
                    ORDER BY e.id DESC
                    LIMIT 1
                ) AS upload_done_data_json
            FROM upload_items i
            INNER JOIN upload_jobs j ON j.job_id = i.job_id
            WHERE j.authorized_user_id = ?
              AND i.asset_id IS NOT NULL
              AND TRIM(i.asset_id) <> ''
            ORDER BY i.finished_at DESC, i.created_at DESC
            """,
            (authorized_user_id,),
        )

        assets = []
        for row in rows:
            download_data = parse_json_maybe(row.get("download_done_data_json"))
            upload_data = parse_json_maybe(row.get("upload_done_data_json"))
            duration_seconds = download_data.get("duration_seconds")

            asset_id = str(row["asset_id"])
            assets.append({
                "asset_id": asset_id,
                "title": row["title"] or "Untitled Audio",
                "description": "Uploaded by Roblox Audio Uploader",
                "length": seconds_to_length(duration_seconds),
                "length_seconds": duration_seconds,
                "created_time": row["finished_at"] or row["created_at"],
                "finished_at": row["finished_at"],
                "created_at": row["created_at"],
                "source_type": row["source_type"],
                "item_id": row["item_id"],
                "job_id": row["job_id"],
                "source_url": row["source_url"],
                "asset_url": upload_data.get("asset_url") or f"https://create.roblox.com/store/asset/{asset_id}",
                "on_creator_store": False,
                "on_creator_store_label": "No / Unknown",
                "is_archived": False,
                "is_blocked": False,
                "can_played": True,
                "asset_state": "uploaded",
                "availability_type": "can_played",
                "origin": "rau_uploaded",
            })

        return assets

    async def list_uploaded_assets_by_session(self, session_id: str) -> list[dict]:
        # Deprecated wrapper. Asset history sekarang tidak lagi diikat ke session.
        row = await fetchone(
            "SELECT authorized_user_id FROM api_sessions WHERE session_id = ?",
            (session_id,),
        )
        if not row:
            return []
        return await self.list_uploaded_assets_by_authorized_user_id(row["authorized_user_id"])

    async def active_jobs_count(self, session_id: str) -> int:
        row = await fetchone(
            (
                "SELECT COUNT(*) AS count "
                "FROM upload_jobs "
                "WHERE session_id = ? "
                "AND status IN ('queued', 'running')"
            ),
            (session_id,),
        )
        return int(row["count"] if row else 0)

    async def list_queued_jobs(self) -> list[str]:
        rows = await fetchall(
            """
            SELECT job_id
            FROM upload_jobs
            WHERE status = 'queued'
            ORDER BY created_at ASC
            """
        )
        return [row["job_id"] for row in rows]

    async def recover_running_as_failed(self) -> None:
        await execute(
            """
            UPDATE upload_jobs
            SET status = 'failed', finished_at = ?
            WHERE status = 'running'
            """,
            (now(),),
        )

    async def mark_job_started(self, job_id: str) -> None:
        await execute(
            """
            UPDATE upload_jobs
            SET status = 'running', started_at = COALESCE(started_at, ?)
            WHERE job_id = ?
            """,
            (now(), job_id),
        )

    async def mark_job_done(self, job_id: str) -> None:
        await execute(
            """
            UPDATE upload_jobs
            SET status = 'done',
                finished_at = ?,
                total_success = (
                    SELECT COUNT(*) FROM upload_items
                    WHERE job_id = ? AND status = 'done'
                ),
                total_failed = (
                    SELECT COUNT(*) FROM upload_items
                    WHERE job_id = ? AND status = 'failed'
                )
            WHERE job_id = ?
            """,
            (now(), job_id, job_id, job_id),
        )

    async def mark_job_failed(self, job_id: str) -> None:
        await execute(
            """
            UPDATE upload_jobs
            SET status = 'failed', finished_at = ?
            WHERE job_id = ?
            """,
            (now(), job_id),
        )

    async def mark_job_cancelled(self, job_id: str) -> None:
        await execute(
            """
            UPDATE upload_jobs
            SET status = 'cancelled', cancelled_at = ?, finished_at = ?
            WHERE job_id = ?
            """,
            (now(), now(), job_id),
        )

    async def is_cancelled(self, job_id: str) -> bool:
        row = await fetchone("SELECT status FROM upload_jobs WHERE job_id = ?", (job_id,))
        return bool(row and row["status"] == "cancelled")

    async def mark_item_started(self, item_id: str) -> None:
        await execute(
            """
            UPDATE upload_items
            SET status = 'running', started_at = COALESCE(started_at, ?)
            WHERE item_id = ?
            """,
            (now(), item_id),
        )

    async def mark_item_downloaded(self, item_id: str, title: str, temp_file_path: str) -> None:
        await execute(
            """
            UPDATE upload_items
            SET download_title = ?, temp_file_path = ?
            WHERE item_id = ?
            """,
            (title, temp_file_path, item_id),
        )

    async def mark_item_done(self, item_id: str, asset_id: str) -> None:
        await execute(
            """
            UPDATE upload_items
            SET status = 'done', asset_id = ?, finished_at = ?
            WHERE item_id = ?
            """,
            (asset_id, now(), item_id),
        )

    async def mark_item_failed(self, item_id: str, message: str, details=None) -> None:
        await execute(
            """
            UPDATE upload_items
            SET status = 'failed',
                error_message = ?,
                error_details_json = ?,
                finished_at = ?
            WHERE item_id = ?
            """,
            (
                message,
                json.dumps(details) if details is not None else None,
                now(),
                item_id,
            ),
        )
