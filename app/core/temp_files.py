import shutil
from pathlib import Path

from app.config import settings


def job_temp_dir(job_id: str) -> Path:
    path = settings.TEMP_DIR / job_id
    path.mkdir(parents=True, exist_ok=True)
    return path


def item_temp_dir(job_id: str, item_id: str) -> Path:
    path = job_temp_dir(job_id) / item_id
    path.mkdir(parents=True, exist_ok=True)
    return path


def cleanup_path(path: Path) -> None:
    if not path.exists():
        return
    if path.is_dir():
        shutil.rmtree(path, ignore_errors=True)
    else:
        try:
            path.unlink()
        except FileNotFoundError:
            pass


def cleanup_job(job_id: str) -> None:
    cleanup_path(settings.TEMP_DIR / job_id)
