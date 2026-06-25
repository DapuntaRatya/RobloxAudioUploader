import asyncio
import re
import shutil
from pathlib import Path
from typing import Dict

from app.config import settings
from app.core.errors import DownloaderError
from app.modules.downloader.base import BaseDownloader, DownloadResult
from app.modules.roblox.asset_upload import detect_audio_content_type


def clean_ansi(text: str) -> str:
    return re.sub(r"\x1b\[[0-9;]*m", "", text or "")


def resolve_ffmpeg_location() -> str | None:
    """Return lokasi ffmpeg yang bisa dipakai yt-dlp.

    Urutan:
    1. FFMPEG_LOCATION dari .env jika diset.
    2. ffmpeg dari PATH.
    3. ffmpeg binary dari package imageio-ffmpeg.
    """
    env_location = (settings.FFMPEG_LOCATION or "").strip()
    if env_location:
        return env_location

    path_ffmpeg = shutil.which("ffmpeg")
    if path_ffmpeg:
        return path_ffmpeg

    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return None


class YouTubeMp3Downloader(BaseDownloader):
    source_key = "youtube"
    label = "YouTube"
    enabled = True

    def can_handle(self, url: str) -> bool:
        value = url.lower()
        return "youtube.com" in value or "youtu.be" in value

    async def download(self, url: str, output_dir: Path) -> DownloadResult:
        return await asyncio.to_thread(self._download_sync, url, output_dir)

    def _download_sync(self, url: str, output_dir: Path) -> DownloadResult:
        try:
            from yt_dlp import YoutubeDL
        except Exception as exc:
            raise DownloaderError(
                "YT_DLP_NOT_INSTALLED",
                "yt-dlp belum terinstall.",
                status_code=500,
            ) from exc

        output_dir.mkdir(parents=True, exist_ok=True)
        before_files = set(output_dir.glob("*"))
        output_template = str(output_dir / "%(title).90s-%(id)s.%(ext)s")

        ffmpeg_location = resolve_ffmpeg_location()

        ydl_opts: Dict = {
            "format": "bestaudio/best",
            "outtmpl": output_template,
            "noplaylist": True,
            "quiet": True,
            "no_warnings": True,
            "restrictfilenames": True,
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }
            ],
        }

        if ffmpeg_location:
            ydl_opts["ffmpeg_location"] = ffmpeg_location

        try:
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
        except Exception as exc:
            error_text = clean_ansi(str(exc))
            if "ffprobe and ffmpeg not found" in error_text or "ffmpeg not found" in error_text:
                error_text += (
                    " | Solusi: jalankan 'pip install -r requirements.txt' ulang, "
                    "atau isi FFMPEG_LOCATION di .env dengan path ffmpeg.exe."
                )

            raise DownloaderError(
                "DOWNLOAD_FAILED",
                "Gagal download audio. Pastikan link valid dan ffmpeg tersedia.",
                details={
                    "url": url,
                    "error": error_text,
                    "ffmpeg_location": ffmpeg_location,
                },
            ) from exc

        after_files = set(output_dir.glob("*"))
        new_files = list(after_files - before_files)
        mp3_files = [file for file in new_files if file.suffix.lower() == ".mp3"]

        if not mp3_files:
            mp3_files = list(output_dir.glob("*.mp3"))

        if not mp3_files:
            raise DownloaderError(
                "OUTPUT_NOT_FOUND",
                "Download selesai tapi file MP3 tidak ditemukan.",
                details={"url": url, "output_dir": str(output_dir)},
            )

        file_path = max(mp3_files, key=lambda item: item.stat().st_mtime)
        content_type = detect_audio_content_type(file_path)

        return DownloadResult(
            source=self.source_key,
            url=url,
            title=info.get("title") or file_path.stem,
            file_path=file_path,
            content_type=content_type,
            duration_seconds=info.get("duration"),
            size_bytes=file_path.stat().st_size,
        )
