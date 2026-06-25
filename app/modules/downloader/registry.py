from typing import Dict, List

from app.core.errors import ValidationAppError
from app.modules.downloader.base import BaseDownloader
from app.modules.downloader.mp3_soundcloud import SoundCloudMp3Downloader
from app.modules.downloader.mp3_spotify import SpotifyMp3Downloader
from app.modules.downloader.mp3_youtube import YouTubeMp3Downloader


class DownloaderRegistry:
    def __init__(self):
        self._downloaders: Dict[str, BaseDownloader] = {}

    def register(self, downloader: BaseDownloader) -> None:
        self._downloaders[downloader.source_key] = downloader

    def get(self, source_key: str) -> BaseDownloader:
        downloader = self._downloaders.get(source_key)
        if not downloader:
            raise ValidationAppError(
                "DOWNLOADER_NOT_FOUND",
                f"Downloader '{source_key}' tidak ditemukan.",
                details={"available": list(self._downloaders.keys())},
            )

        if not downloader.enabled:
            raise ValidationAppError(
                "DOWNLOADER_DISABLED",
                f"Downloader '{source_key}' belum aktif.",
            )

        return downloader

    def list_sources(self) -> List[dict]:
        return [
            {
                "key": downloader.source_key,
                "label": downloader.label,
                "enabled": downloader.enabled,
            }
            for downloader in self._downloaders.values()
        ]


registry = DownloaderRegistry()
registry.register(YouTubeMp3Downloader())
registry.register(SoundCloudMp3Downloader())
registry.register(SpotifyMp3Downloader())
