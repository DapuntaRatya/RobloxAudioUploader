from pydantic import BaseModel, Field, field_validator
from fastapi import APIRouter, Request

from app.core.errors import JobError
from app.core.response import success_response
from app.dependencies import require_session, session_service
from app.modules.downloader.registry import registry
from app.modules.roblox.asset_info import enrich_assets_with_roblox_info
from app.modules.roblox.asset_permission import grant_assets_permission_to_universe
from app.repositories.job_repository import JobRepository
from app.schemas.upload_schema import UploadRequest
from app.services.queue_service import QueueService
from app.services.upload_service import UploadService

router = APIRouter()
upload_service = UploadService()
job_repo = JobRepository()
queue_service = QueueService()


class GrantAssetsRequest(BaseModel):
    asset_ids: list[str] = Field(min_length=1)
    experience_ids: list[str] = Field(min_length=1)

    @field_validator("asset_ids")
    @classmethod
    def clean_asset_ids(cls, value: list[str]) -> list[str]:
        clean = []
        for item in value:
            text = str(item).strip()
            if not text:
                continue
            if not text.isdigit():
                raise ValueError(f"Asset ID harus angka: {text}")
            if text not in clean:
                clean.append(text)

        if not clean:
            raise ValueError("Minimal 1 asset ID harus dipilih.")
        return clean

    @field_validator("experience_ids")
    @classmethod
    def clean_experience_ids(cls, value: list[str]) -> list[str]:
        clean = []
        for item in value:
            text = str(item).strip()
            if not text:
                continue
            if not text.isdigit():
                raise ValueError(f"Experience/Universe ID harus angka: {text}")
            if text not in clean:
                clean.append(text)

        if not clean:
            raise ValueError("Minimal 1 experience ID harus diisi.")
        return clean


@router.get("/api/sources")
async def list_sources():
    return success_response({"sources": registry.list_sources()})


@router.get("/api/queue")
async def queue_status(request: Request):
    await require_session(request)
    return success_response({"queue_size": queue_service.size()})


@router.get("/api/assets")
async def list_uploaded_assets(request: Request):
    session = await require_session(request)
    api_key = session_service.decrypt_api_key_from_session(session)

    assets = await job_repo.list_uploaded_assets_by_authorized_user_id(session["authorized_user_id"])
    assets = await enrich_assets_with_roblox_info(
        api_key=api_key,
        assets=assets,
        concurrency=5,
    )

    return success_response({
        "assets": assets,
        "count": len(assets),
        "source_scope": "authorized_user_uploaded_enriched",
        "note": (
            "Data dasar berasal dari SQLite RAU berdasarkan authorized_user_id, bukan session login. Metadata asset seperti title, "
            "description, moderation_state, asset_state, dan revision_create_time "
            "di-refresh dari Roblox Assets API per asset ID."
        ),
    })


@router.post("/api/assets/grant")
async def grant_selected_assets(payload: GrantAssetsRequest, request: Request):
    session = await require_session(request)
    api_key = session_service.decrypt_api_key_from_session(session)

    results = []
    success_count = 0
    failed_count = 0

    for universe_id in payload.experience_ids:
        try:
            response = await grant_assets_permission_to_universe(
                api_key=api_key,
                asset_ids=payload.asset_ids,
                universe_id=universe_id,
            )

            success_assets = [str(item) for item in response.get("successAssetIds", [])]
            errors = response.get("errors", [])

            for asset_id in payload.asset_ids:
                is_success = asset_id in success_assets or not errors
                if is_success:
                    success_count += 1
                else:
                    failed_count += 1

                results.append({
                    "asset_id": asset_id,
                    "universe_id": universe_id,
                    "status": "success" if is_success else "failed",
                    "message": "Permission berhasil." if is_success else "Permission gagal.",
                    "response": response,
                })

        except Exception as exc:
            failed_count += len(payload.asset_ids)
            for asset_id in payload.asset_ids:
                results.append({
                    "asset_id": asset_id,
                    "universe_id": universe_id,
                    "status": "failed",
                    "message": str(exc),
                    "error_type": type(exc).__name__,
                    "details": getattr(exc, "details", None),
                })

    return success_response({
        "asset_ids": payload.asset_ids,
        "experience_ids": payload.experience_ids,
        "success_count": success_count,
        "failed_count": failed_count,
        "results": results,
    })


@router.post("/api/upload")
async def create_upload_job(payload: UploadRequest, request: Request):
    session = await require_session(request)
    job = await upload_service.create_upload_job(session=session, payload=payload)

    return success_response({
        "job_id": job["job_id"],
        "stream_url": f"/api/upload/{job['job_id']}/events",
    })


@router.get("/api/upload/{job_id}")
async def get_upload_job(job_id: str, request: Request):
    session = await require_session(request)
    job = await job_repo.get_job(job_id)

    if not job or job["session_id"] != session["session_id"]:
        raise JobError("JOB_NOT_FOUND", "Job tidak ditemukan.", status_code=404)

    items = await job_repo.list_items(job_id)

    return success_response({
        "job": job,
        "items": items,
    })


@router.post("/api/upload/{job_id}/cancel")
async def cancel_upload_job(job_id: str, request: Request):
    session = await require_session(request)
    job = await job_repo.get_job(job_id)

    if not job or job["session_id"] != session["session_id"]:
        raise JobError("JOB_NOT_FOUND", "Job tidak ditemukan.", status_code=404)

    await job_repo.mark_job_cancelled(job_id)
    return success_response({"message": "Job dibatalkan.", "job_id": job_id})
