from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api import auth, pages, stream, upload
from app.config import settings
from app.core.errors import AppError
from app.core.response import failed_response
from app.db.sqlite import close_db, init_db
from app.services.worker_service import WorkerService

worker_service = WorkerService()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    await worker_service.start()
    yield
    await worker_service.stop()
    await close_db()


app = FastAPI(title=settings.APP_NAME, lifespan=lifespan)

app.mount("/css", StaticFiles(directory=settings.PUBLIC_DIR / "css"), name="css")
app.mount("/js", StaticFiles(directory=settings.PUBLIC_DIR / "js"), name="js")

app.include_router(pages.router)
app.include_router(auth.router)
app.include_router(upload.router)
app.include_router(stream.router)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError):
    return JSONResponse(
        status_code=exc.status_code,
        content=failed_response(exc.code, exc.message, exc.details),
    )


@app.exception_handler(Exception)
async def unexpected_error_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content=failed_response(
            "INTERNAL_SERVER_ERROR",
            "Terjadi error tidak terduga di server.",
            {"error_type": type(exc).__name__, "error": str(exc)},
        ),
    )
