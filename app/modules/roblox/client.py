from typing import Iterable, Optional

import httpx

from app.config import settings
from app.core.errors import RobloxApiError
from app.modules.roblox.roblox_errors import roblox_http_error_message


def response_body(response: httpx.Response):
    try:
        return response.json()
    except Exception:
        return response.text


class RobloxClient:
    def __init__(self, api_key: str):
        self.api_key = api_key

    def headers(self) -> dict:
        return {"x-api-key": self.api_key}

    async def request(
        self,
        method: str,
        url: str,
        *,
        expected_statuses: Optional[Iterable[int]] = None,
        **kwargs,
    ) -> httpx.Response:
        if expected_statuses is None:
            expected_statuses = (200, 201, 202, 204)

        headers = kwargs.pop("headers", {})
        headers = {**self.headers(), **headers}

        try:
            async with httpx.AsyncClient(timeout=settings.ROBLOX_REQUEST_TIMEOUT_SECONDS) as client:
                response = await client.request(method, url, headers=headers, **kwargs)
        except httpx.RequestError as exc:
            raise RobloxApiError(
                "ROBLOX_CONNECTION_ERROR",
                f"Gagal connect ke Roblox API: {exc}",
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
