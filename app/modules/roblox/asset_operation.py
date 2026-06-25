import asyncio
import time
from typing import Any, Awaitable, Callable, Dict, Optional

from app.config import settings
from app.core.errors import RobloxApiError
from app.modules.roblox.client import RobloxClient


def extract_operation_path(create_response: Dict[str, Any]) -> str:
    operation_path = create_response.get("path")
    if not operation_path:
        operation_id = create_response.get("operationId")
        if operation_id:
            operation_path = f"operations/{operation_id}"

    if not operation_path or not str(operation_path).startswith("operations/"):
        raise RobloxApiError(
            "OPERATION_PATH_NOT_FOUND",
            "Tidak menemukan operation path dari response create asset.",
            details=create_response,
        )

    return str(operation_path)


def extract_asset_id(asset_response: Dict[str, Any]) -> str:
    asset_id = asset_response.get("assetId")
    if asset_id:
        return str(asset_id)

    path = asset_response.get("path")
    if isinstance(path, str) and path.startswith("assets/"):
        return path.split("/", 1)[1]

    raise RobloxApiError(
        "ASSET_ID_NOT_FOUND",
        "Asset ID tidak ditemukan dari operation response.",
        details=asset_response,
    )


async def poll_asset_operation(
    *,
    api_key: str,
    operation_path: str,
    on_poll: Optional[Callable[[Dict[str, Any]], Awaitable[None]]] = None,
) -> Dict[str, Any]:
    client = RobloxClient(api_key)
    operation_url = f"{settings.ROBLOX_ASSETS_BASE_URL}/{operation_path}"

    started_at = time.time()
    last_payload = None

    while True:
        elapsed = time.time() - started_at
        if elapsed > settings.ROBLOX_MAX_POLL_SECONDS:
            raise RobloxApiError(
                "OPERATION_TIMEOUT",
                "Upload operation belum selesai sampai timeout.",
                status_code=504,
                details={
                    "timeout_seconds": settings.ROBLOX_MAX_POLL_SECONDS,
                    "last_payload": last_payload,
                },
            )

        response = await client.request("GET", operation_url)
        payload = response.json()
        last_payload = payload

        if on_poll:
            await on_poll(payload)

        if payload.get("done") is True:
            if payload.get("error"):
                raise RobloxApiError(
                    "OPERATION_FAILED",
                    "Operation Roblox selesai dengan error.",
                    details=payload,
                )

            asset_response = payload.get("response")
            if not asset_response:
                raise RobloxApiError(
                    "OPERATION_RESPONSE_EMPTY",
                    "Operation selesai tapi response asset kosong.",
                    details=payload,
                )

            return asset_response

        await asyncio.sleep(settings.ROBLOX_POLL_INTERVAL_SECONDS)
