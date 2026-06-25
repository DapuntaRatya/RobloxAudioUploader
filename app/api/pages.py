from fastapi import APIRouter, Request
from fastapi.responses import FileResponse, RedirectResponse

from app.config import settings
from app.dependencies import get_optional_session

router = APIRouter()


@router.get("/")
async def dashboard_page(request: Request):
    session = await get_optional_session(request)
    if not session:
        return RedirectResponse(url="/login", status_code=302)
    return FileResponse(settings.PUBLIC_DIR / "index.html")


@router.get("/assets")
async def assets_page(request: Request):
    session = await get_optional_session(request)
    if not session:
        return RedirectResponse(url="/login", status_code=302)
    return FileResponse(settings.PUBLIC_DIR / "assets.html")


@router.get("/login")
async def login_page(request: Request):
    session = await get_optional_session(request)
    if session:
        return RedirectResponse(url="/", status_code=302)
    return FileResponse(settings.PUBLIC_DIR / "login.html")
