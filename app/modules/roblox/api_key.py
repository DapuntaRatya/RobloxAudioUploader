from typing import Any, Dict, List
import asyncio

import requests

from app.config import settings
from app.core.errors import AuthError


def _introspect_api_key_sync(api_key: str) -> requests.Response:
    return requests.post(
        settings.ROBLOX_INTROSPECT_URL,
        json={"apiKey": api_key},
        headers={
            "Content-Type": "application/json",
            "Accept": "*/*",
            "User-Agent": "curl/8.5.0",
        },
        timeout=settings.ROBLOX_REQUEST_TIMEOUT_SECONDS,
    )


async def introspect_api_key(api_key: str) -> Dict[str, Any]:
    try:
        response = await asyncio.to_thread(_introspect_api_key_sync, api_key)
    except requests.RequestException as exc:
        raise AuthError(
            "ROBLOX_INTROSPECT_CONNECTION_ERROR",
            f"Gagal menghubungi endpoint introspect Roblox: {type(exc).__name__}: {exc}",
            status_code=502,
        ) from exc

    if response.status_code != 200:
        try:
            body = response.json()
        except Exception:
            body = response.text

        raise AuthError(
            "INVALID_API_KEY",
            "API key tidak valid atau tidak bisa di-introspect.",
            status_code=401,
            details={"status_code": response.status_code, "body": body},
        )

    return response.json()


def _has_scope(scopes: List[Dict[str, Any]], scope_name: str, required_ops: List[str]) -> bool:
    for scope in scopes:
        if scope.get("name") != scope_name:
            continue

        operations = set(scope.get("operations") or [])
        if all(op in operations for op in required_ops):
            return True

    return False


def validate_api_key_info(info: Dict[str, Any]) -> None:
    if not info.get("enabled"):
        raise AuthError("API_KEY_DISABLED", "API key tidak aktif.", status_code=401)

    if info.get("expired"):
        raise AuthError("API_KEY_EXPIRED", "API key sudah expired.", status_code=401)

    if not info.get("authorizedUserId"):
        raise AuthError(
            "AUTHORIZED_USER_NOT_FOUND",
            "Tidak bisa membaca authorizedUserId dari API key.",
            status_code=401,
        )

    scopes = info.get("scopes") or []
    missing = []

    if not _has_scope(scopes, "asset", ["read", "write"]):
        missing.append("asset: read, write")

    if not _has_scope(scopes, "asset-permissions", ["write"]):
        missing.append("asset-permissions: write")

    if missing:
        raise AuthError(
            "MISSING_REQUIRED_SCOPE",
            "API key valid, tapi permission belum cukup.",
            status_code=403,
            details={
                "missing": missing,
                "hint": "Aktifkan scope asset read/write dan asset-permissions write di Roblox Open Cloud API Key.",
            },
        )
