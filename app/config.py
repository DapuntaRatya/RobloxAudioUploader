from pathlib import Path

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent


class Settings(BaseSettings):
    APP_NAME: str = "Roblox Audio Uploader"
    APP_SHORT_NAME: str = "RAU"

    APP_ENV: str = "local"
    APP_HOST: str = "127.0.0.1"
    APP_PORT: int = 8000
    APP_BASE_URL: str = "http://127.0.0.1:8000"

    DATABASE_PATH: Path = PROJECT_ROOT / "data" / "rau.sqlite3"

    SESSION_COOKIE_NAME: str = "rau_session"
    SESSION_TTL_SECONDS: int = 86400
    COOKIE_SECURE: bool = False
    COOKIE_SAMESITE: str = "lax"

    FERNET_KEY: str = ""

    MAX_ITEMS_PER_JOB: int = 20
    MAX_EXPERIENCES_PER_JOB: int = 20
    MAX_ACTIVE_JOBS_PER_SESSION: int = 3
    WORKER_COUNT: int = 2

    MAX_DOWNLOAD_CONCURRENT: int = 4
    MAX_ROBLOX_UPLOAD_CONCURRENT: int = 3
    MAX_PERMISSION_CONCURRENT: int = 8

    FFMPEG_LOCATION: str = ""

    TEMP_DIR: Path = BASE_DIR / "temp"
    PUBLIC_DIR: Path = BASE_DIR / "public"

    ROBLOX_INTROSPECT_URL: str = "https://apis.roblox.com/api-keys/v1/introspect"
    ROBLOX_ASSETS_BASE_URL: str = "https://apis.roblox.com/assets/v1"
    ROBLOX_CREATE_ASSET_URL: str = "https://apis.roblox.com/assets/v1/assets"
    ROBLOX_PERMISSION_URL: str = "https://apis.roblox.com/asset-permissions-api/v1/assets/permissions"

    ROBLOX_REQUEST_TIMEOUT_SECONDS: int = 60
    ROBLOX_POLL_INTERVAL_SECONDS: int = 5
    ROBLOX_MAX_POLL_SECONDS: int = 240

    MAX_AUDIO_SIZE_BYTES: int = 20 * 1024 * 1024

    class Config:
        env_file = ".env"


settings = Settings()
settings.DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
settings.TEMP_DIR.mkdir(parents=True, exist_ok=True)
