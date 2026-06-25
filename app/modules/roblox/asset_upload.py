import json
import mimetypes
import re
from pathlib import Path
from typing import Dict

from app.config import settings
from app.core.errors import ValidationAppError
from app.modules.roblox.client import RobloxClient


SUPPORTED_AUDIO_TYPES = {
    ".mp3": "audio/mpeg",
    ".ogg": "audio/ogg",
    ".wav": "audio/wav",
    ".flac": "audio/flac",
}

ROBLOX_ASSET_NAME_MAX_LENGTH = 50
ROBLOX_ASSET_NAME_FALLBACK = "RAU Audio"


def sanitize_roblox_asset_name(value: str, fallback: str = ROBLOX_ASSET_NAME_FALLBACK) -> str:
    name = str(value or "").strip()

    # Hapus karakter kontrol dan rapikan whitespace.
    name = re.sub(r"[\x00-\x1f\x7f]", " ", name)
    name = re.sub(r"\s+", " ", name).strip()

    if not name:
        name = fallback

    # Roblox menolak nama asset yang terlalu panjang.
    if len(name) > ROBLOX_ASSET_NAME_MAX_LENGTH:
        name = name[:ROBLOX_ASSET_NAME_MAX_LENGTH].rstrip(" -_.,|")

    if not name:
        name = fallback

    return name


def detect_audio_content_type(audio_path: Path) -> str:
    suffix = audio_path.suffix.lower()
    if suffix in SUPPORTED_AUDIO_TYPES:
        return SUPPORTED_AUDIO_TYPES[suffix]

    guessed, _ = mimetypes.guess_type(str(audio_path))
    raise ValidationAppError(
        "UNSUPPORTED_AUDIO_FORMAT",
        "Format audio tidak didukung.",
        status_code=400,
        details={
            "file": str(audio_path),
            "extension": suffix,
            "detected": guessed,
            "supported": list(SUPPORTED_AUDIO_TYPES.keys()),
        },
    )


def validate_audio_file(audio_path: Path) -> str:
    if not audio_path.exists() or not audio_path.is_file():
        raise ValidationAppError(
            "AUDIO_FILE_NOT_FOUND",
            "File audio tidak ditemukan.",
            details={"file": str(audio_path)},
        )

    size = audio_path.stat().st_size
    if size <= 0:
        raise ValidationAppError(
            "AUDIO_FILE_EMPTY",
            "File audio kosong.",
            details={"file": str(audio_path)},
        )

    if size > settings.MAX_AUDIO_SIZE_BYTES:
        raise ValidationAppError(
            "AUDIO_FILE_TOO_LARGE",
            "File audio terlalu besar.",
            details={"size_bytes": size, "max_bytes": settings.MAX_AUDIO_SIZE_BYTES},
        )

    return detect_audio_content_type(audio_path)


async def create_audio_asset(
    *,
    api_key: str,
    creator_user_id: str,
    audio_path: Path,
    display_name: str,
    description: str,
) -> Dict:
    content_type = validate_audio_file(audio_path)
    safe_display_name = sanitize_roblox_asset_name(display_name)

    request_payload = {
        "assetType": "Audio",
        "displayName": safe_display_name,
        "description": str(description or "")[:1000],
        "creationContext": {
            "creator": {
                "userId": str(creator_user_id),
            }
        },
    }

    client = RobloxClient(api_key)

    with audio_path.open("rb") as file_handle:
        response = await client.request(
            "POST",
            settings.ROBLOX_CREATE_ASSET_URL,
            data={"request": json.dumps(request_payload)},
            files={
                "fileContent": (
                    audio_path.name,
                    file_handle,
                    content_type,
                )
            },
        )

    return response.json()
