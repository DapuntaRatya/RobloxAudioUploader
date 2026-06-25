from fastapi import APIRouter, Request, Response

from app.config import settings
from app.core.response import success_response
from app.dependencies import require_session, session_service
from app.schemas.auth_schema import LoginRequest

router = APIRouter()


@router.post("/api/login")
async def login(payload: LoginRequest, response: Response):
    session = await session_service.create_from_api_key(payload.api_key)

    response.set_cookie(
        key=settings.SESSION_COOKIE_NAME,
        value=session["session_id"],
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        max_age=settings.SESSION_TTL_SECONDS,
        path="/",
    )

    return success_response({
        "message": "Login berhasil.",
        "session": session_service.public_info(session),
    })


@router.post("/api/logout")
async def logout(request: Request, response: Response):
    session_id = request.cookies.get(settings.SESSION_COOKIE_NAME)
    await session_service.revoke(session_id)

    response.delete_cookie(key=settings.SESSION_COOKIE_NAME, path="/")
    return success_response({"message": "Logout berhasil."})


@router.get("/api/session")
async def session_info(request: Request):
    session = await require_session(request)
    return success_response(session_service.public_info(session))
