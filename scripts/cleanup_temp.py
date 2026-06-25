from app.config import settings
from app.core.temp_files import cleanup_path

cleanup_path(settings.TEMP_DIR)
settings.TEMP_DIR.mkdir(parents=True, exist_ok=True)
print(f"Cleaned: {settings.TEMP_DIR}")
