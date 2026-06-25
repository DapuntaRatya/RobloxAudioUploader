from datetime import datetime, timedelta, timezone

from app.config import settings
from app.core.security import generate_id
from app.repositories.session_repository import SessionRepository
from app.services.auth_service import AuthService


class SessionService:
    def __init__(self):
        self.repo = SessionRepository()
        self.auth_service = AuthService()

    async def create_from_api_key(self, api_key: str) -> dict:
        info = await self.auth_service.introspect_and_validate(api_key)

        session_id = generate_id("sess")
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=settings.SESSION_TTL_SECONDS)

        return await self.repo.create(
            session_id=session_id,
            authorized_user_id=str(info["authorizedUserId"]),
            api_key_name=info.get("name") or "Roblox API Key",
            api_key_encrypted=self.auth_service.encrypted_api_key(api_key),
            api_key_masked=self.auth_service.mask_api_key(api_key),
            scopes=info.get("scopes") or [],
            expires_at=expires_at,
        )

    async def get_valid(self, session_id: str | None) -> dict | None:
        return await self.repo.get_valid(session_id)

    async def revoke(self, session_id: str | None) -> None:
        await self.repo.revoke(session_id)

    def public_info(self, session: dict) -> dict:
        return {
            "authenticated": True,
            "authorized_user_id": session["authorized_user_id"],
            "api_key_name": session["api_key_name"],
            "api_key_masked": session["api_key_masked"],
            "scopes": session["scopes"],
        }

    def decrypt_api_key_from_session(self, session: dict) -> str:
        return self.auth_service.decrypt_api_key(session["api_key_encrypted"])
