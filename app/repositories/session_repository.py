import json
from datetime import datetime, timezone

from app.db.sqlite import execute, fetchone


def parse_session(row: dict | None) -> dict | None:
    if not row:
        return None
    row["scopes"] = json.loads(row.pop("scopes_json") or "[]")
    return row


class SessionRepository:
    async def create(
        self,
        *,
        session_id: str,
        authorized_user_id: str,
        api_key_name: str,
        api_key_encrypted: str,
        api_key_masked: str,
        scopes: list,
        expires_at: datetime,
    ) -> dict:
        await execute(
            """
            INSERT INTO api_sessions (
                session_id, authorized_user_id, api_key_name, api_key_encrypted,
                api_key_masked, scopes_json, expires_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                session_id,
                authorized_user_id,
                api_key_name,
                api_key_encrypted,
                api_key_masked,
                json.dumps(scopes),
                expires_at.isoformat(),
            ),
        )
        return await self.get_valid(session_id)

    async def get_valid(self, session_id: str | None) -> dict | None:
        if not session_id:
            return None

        row = await fetchone(
            """
            SELECT *
            FROM api_sessions
            WHERE session_id = ?
              AND revoked_at IS NULL
              AND expires_at > ?
            """,
            (session_id, datetime.now(timezone.utc).isoformat()),
        )
        return parse_session(row)

    async def revoke(self, session_id: str | None) -> None:
        if not session_id:
            return

        await execute(
            """
            UPDATE api_sessions
            SET revoked_at = ?
            WHERE session_id = ?
            """,
            (datetime.now(timezone.utc).isoformat(), session_id),
        )
