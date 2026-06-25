from typing import Any, Iterable, Optional
import asyncio

import requests

from app.config import settings
from app.core.errors import RobloxApiError
from app.modules.roblox.roblox_errors import roblox_http_error_message


def response_body(response: Any):
    try:
        return response.json()
    except Exception:
        return response.text


class RobloxClient:
    def __init__(self, api_key: str):
        self.api_key = api_key

    def headers(self) -> dict:
        return {
            "x-api-key": self.api_key,
            "Accept": "*/*",
            "User-Agent": "curl/8.5.0",
        }

    def _request_sync(
        self,
        method: str,
        url: str,
        *,
        headers: dict,
        **kwargs,
    ) -> requests.Response:
        return requests.request(
            method=str(method).upper(),
            url=url,
            headers=headers,
            timeout=settings.ROBLOX_REQUEST_TIMEOUT_SECONDS,
            **kwargs,
        )

    async def request(
        self,
        method: str,
        url: str,
        *,
        expected_statuses: Optional[Iterable[int]] = None,
        **kwargs,
    ) -> requests.Response:
        if expected_statuses is None:
            expected_statuses = (200, 201, 202, 204)

        extra_headers = kwargs.pop("headers", {}) or {}
        headers = {**self.headers(), **extra_headers}

        try:
            response = await asyncio.to_thread(
                self._request_sync,
                method,
                url,
                headers=headers,
                **kwargs,
            )
        except requests.RequestException as exc:
            raise RobloxApiError(
                "ROBLOX_CONNECTION_ERROR",
                f"Gagal connect ke Roblox API: {type(exc).__name__}: {exc}",
                status_code=502,
            ) from exc

        if response.status_code not in expected_statuses:
            raise RobloxApiError(
                "ROBLOX_API_ERROR",
                roblox_http_error_message(response.status_code),
                status_code=response.status_code,
                details={
                    "url": str(response.url),
                    "status_code": response.status_code,
                    "body": response_body(response),
                },
            )

        return response
