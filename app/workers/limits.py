import asyncio

from app.config import settings

download_semaphore = asyncio.Semaphore(settings.MAX_DOWNLOAD_CONCURRENT)
roblox_upload_semaphore = asyncio.Semaphore(settings.MAX_ROBLOX_UPLOAD_CONCURRENT)
permission_semaphore = asyncio.Semaphore(settings.MAX_PERMISSION_CONCURRENT)
