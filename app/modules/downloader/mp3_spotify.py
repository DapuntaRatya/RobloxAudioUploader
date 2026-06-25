from pathlib import Path

from app.core.errors import DownloaderError
from app.modules.downloader.base import BaseDownloader, DownloadResult


class SpotifyMp3Downloader(BaseDownloader):
    source_key = "spotify"
    label = "Spotify"
    enabled = False

    def can_handle(self, url: str) -> bool:
        return "spotify.com" in url.lower()

    async def download(self, url: str, output_dir: Path) -> DownloadResult:
        raise DownloaderError(
            "SPOTIFY_NOT_IMPLEMENTED",
            "Downloader Spotify belum diimplementasikan.",
            details={"url": url},
        )
