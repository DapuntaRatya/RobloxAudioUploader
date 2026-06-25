from fastapi import Request

from app.config import settings
from app.core.errors import AuthError
from app.services.session_service import SessionService

session_service = SessionService()


async def get_optional_session(request: Request) -> dict | None:
    session_id = request.cookies.get(settings.SESSION_COOKIE_NAME)
    return await session_service.get_valid(session_id)


async def require_session(request: Request) -> dict:
    session = await get_optional_session(request)
    if not session:
        raise AuthError(
            "UNAUTHENTICATED",
            "Session tidak valid. Silakan login ulang.",
            status_code=401,
        )
    return session
