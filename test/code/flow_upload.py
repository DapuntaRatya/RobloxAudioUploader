import asyncio
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from app.modules.roblox.asset_operation import extract_asset_id, extract_operation_path, poll_asset_operation
from app.modules.roblox.asset_permission import grant_asset_permission_to_universe
from app.modules.roblox.asset_upload import create_audio_asset

ROBLOX_API_KEY = os.getenv("ROBLOX_API_KEY", "api_key_disini")
ROBLOX_USER_ID = "9897973594"
ROBLOX_EXPERIENCE_IDS = ["9711918317"]
DUMMY_MUSIC_NAME = "Test Upload From Modular App"
DUMMY_MUSIC_PATH = PROJECT_ROOT / "test" / "data" / "test_music.mp3"


async def main():
    if ROBLOX_API_KEY == "api_key_disini":
        print("Isi env ROBLOX_API_KEY dulu atau edit file ini.")
        return 2
    if not DUMMY_MUSIC_PATH.exists():
        print(f"File test tidak ditemukan: {DUMMY_MUSIC_PATH}")
        return 2
    print("Upload audio...")
    create_response = await create_audio_asset(api_key=ROBLOX_API_KEY, creator_user_id=ROBLOX_USER_ID, audio_path=DUMMY_MUSIC_PATH, display_name=DUMMY_MUSIC_NAME, description="Uploaded by test/code/flow_upload.py")
    print(create_response)
    operation_path = extract_operation_path(create_response)
    print("Polling operation...")
    asset_response = await poll_asset_operation(api_key=ROBLOX_API_KEY, operation_path=operation_path)
    print(asset_response)
    asset_id = extract_asset_id(asset_response)
    print(f"Asset ID: {asset_id}")
    print(f"rbxassetid://{asset_id}")
    for universe_id in ROBLOX_EXPERIENCE_IDS:
        print(f"Grant permission to {universe_id}...")
        permission = await grant_asset_permission_to_universe(api_key=ROBLOX_API_KEY, asset_id=asset_id, universe_id=universe_id)
        print(permission)
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
