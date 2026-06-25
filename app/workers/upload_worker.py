import asyncio
from pathlib import Path

from app.core.temp_files import cleanup_job, cleanup_path, item_temp_dir
from app.modules.downloader.registry import registry
from app.modules.roblox.asset_operation import extract_asset_id, extract_operation_path, poll_asset_operation
from app.modules.roblox.asset_permission import grant_asset_permission_to_universe
from app.modules.roblox.asset_upload import create_audio_asset
from app.repositories.job_repository import JobRepository
from app.repositories.session_repository import SessionRepository
from app.services.auth_service import AuthService
from app.services.event_service import EventService
from app.workers.limits import download_semaphore, permission_semaphore, roblox_upload_semaphore


def safe_display_name(title: str, fallback: str) -> str:
    value = (title or fallback).strip()
    return (value or fallback)[:100]


class UploadWorker:
    def __init__(self):
        self.jobs = JobRepository()
        self.sessions = SessionRepository()
        self.events = EventService()
        self.auth = AuthService()

    async def process_job(self, job_id: str) -> None:
        job = await self.jobs.get_job(job_id)
        if not job:
            return

        session = await self.sessions.get_valid(job["session_id"])
        if not session:
            await self.jobs.mark_job_failed(job_id, "Session tidak valid.")
            await self.events.publish(
                job_id=job_id,
                event_type="job_failed",
                level="error",
                message="Session tidak valid atau expired.",
            )
            return

        api_key = self.auth.decrypt_api_key(session["api_key_encrypted"])
        items = await self.jobs.list_items(job_id)

        await self.jobs.mark_job_started(job_id)
        await self.events.publish(
            job_id=job_id,
            event_type="job_started",
            message="Job upload dimulai.",
            data={
                "source_type": job["source_type"],
                "total_audio": len(items),
                "experience_ids": job["experience_ids"],
            },
        )

        try:
            if job["options"].get("parallel", True):
                await asyncio.gather(*[
                    self.process_item(job, item, session, api_key)
                    for item in items
                ])
            else:
                for item in items:
                    await self.process_item(job, item, session, api_key)

            await self.jobs.mark_job_done(job_id)
            await self.events.publish(
                job_id=job_id,
                event_type="job_done",
                level="success",
                message="Semua proses upload selesai.",
            )

        except Exception as exc:
            await self.jobs.mark_job_failed(job_id, str(exc))
            await self.events.publish(
                job_id=job_id,
                event_type="job_failed",
                level="error",
                message=f"Job gagal: {exc}",
                data={"error_type": type(exc).__name__, "error": str(exc)},
            )

        finally:
            if job["options"].get("cleanup_temp", True):
                cleanup_job(job_id)

    async def process_item(self, job: dict, item: dict, session: dict, api_key: str) -> None:
        job_id = job["job_id"]
        item_id = item["item_id"]
        temp_dir = item_temp_dir(job_id, item_id)

        if await self.jobs.is_cancelled(job_id):
            return

        await self.jobs.mark_item_started(item_id)
        await self.events.publish(
            job_id=job_id,
            item_id=item_id,
            event_type="item_started",
            message=f"[{item_id}] Mulai proses audio.",
            data={"url": item["source_url"]},
        )

        try:
            downloader = registry.get(job["source_type"])

            await self.events.publish(
                job_id=job_id,
                item_id=item_id,
                event_type="download_started",
                message=f"[{item_id}] Download dimulai.",
                data={"url": item["source_url"], "source": downloader.source_key},
            )

            async with download_semaphore:
                download_result = await downloader.download(item["source_url"], temp_dir)

            await self.jobs.mark_item_downloaded(
                item_id,
                download_result.title,
                str(download_result.file_path),
            )

            await self.events.publish(
                job_id=job_id,
                item_id=item_id,
                event_type="download_done",
                level="success",
                message=f"[{item_id}] Download selesai: {download_result.title}",
                data={
                    "title": download_result.title,
                    "size_bytes": download_result.size_bytes,
                    "duration_seconds": download_result.duration_seconds,
                },
            )

            display_name = safe_display_name(download_result.title, f"RAU Upload {item['item_index']}")

            await self.events.publish(
                job_id=job_id,
                item_id=item_id,
                event_type="upload_started",
                message=f"[{item_id}] Upload ke Roblox dimulai.",
                data={"display_name": display_name},
            )

            async with roblox_upload_semaphore:
                create_response = await create_audio_asset(
                    api_key=api_key,
                    creator_user_id=session["authorized_user_id"],
                    audio_path=Path(download_result.file_path),
                    display_name=display_name,
                    description="Uploaded by Roblox Audio Uploader",
                )

            operation_path = extract_operation_path(create_response)

            async def on_poll(payload: dict) -> None:
                await self.events.publish(
                    job_id=job_id,
                    item_id=item_id,
                    event_type="operation_polling",
                    message=f"[{item_id}] Menunggu Roblox operation...",
                    data={
                        "done": payload.get("done"),
                        "operationId": payload.get("operationId"),
                    },
                )

            asset_response = await poll_asset_operation(
                api_key=api_key,
                operation_path=operation_path,
                on_poll=on_poll,
            )
            asset_id = extract_asset_id(asset_response)

            await self.events.publish(
                job_id=job_id,
                item_id=item_id,
                event_type="upload_done",
                level="success",
                message=f"[{item_id}] Upload berhasil: {asset_id}",
                data={
                    "asset_id": asset_id,
                    "rbxassetid": f"rbxassetid://{asset_id}",
                    "asset_url": f"https://create.roblox.com/store/asset/{asset_id}",
                },
            )

            if job["options"].get("grant_permission", True):
                for universe_id in job["experience_ids"]:
                    await self.events.publish(
                        job_id=job_id,
                        item_id=item_id,
                        event_type="permission_started",
                        message=f"[{item_id}] Grant permission ke experience {universe_id}.",
                        data={"asset_id": asset_id, "universe_id": universe_id},
                    )

                    async with permission_semaphore:
                        permission_response = await grant_asset_permission_to_universe(
                            api_key=api_key,
                            asset_id=asset_id,
                            universe_id=str(universe_id),
                        )

                    await self.events.publish(
                        job_id=job_id,
                        item_id=item_id,
                        event_type="permission_done",
                        level="success",
                        message=f"[{item_id}] Permission berhasil ke experience {universe_id}.",
                        data={
                            "asset_id": asset_id,
                            "universe_id": universe_id,
                            "permission_response": permission_response,
                        },
                    )

            await self.jobs.mark_item_done(item_id, asset_id)
            await self.events.publish(
                job_id=job_id,
                item_id=item_id,
                event_type="item_done",
                level="success",
                message=f"[{item_id}] Selesai.",
                data={"asset_id": asset_id},
            )

        except Exception as exc:
            details = getattr(exc, "details", None)
            await self.jobs.mark_item_failed(item_id, str(exc), details)
            await self.events.publish(
                job_id=job_id,
                item_id=item_id,
                event_type="item_failed",
                level="error",
                message=f"[{item_id}] Gagal: {exc}",
                data={
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                    "details": details,
                },
            )

        finally:
            if job["options"].get("cleanup_temp", True):
                cleanup_path(temp_dir)
