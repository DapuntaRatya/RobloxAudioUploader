import asyncio
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from app.modules.roblox.asset_permission import grant_asset_permission_to_universe

ROBLOX_API_KEY = os.getenv("ROBLOX_API_KEY", "api_key_disini")
ASSET_ID = "79113590726749"
EXPERIENCE_IDS = ["9711918317"]


async def main():
    if ROBLOX_API_KEY == "api_key_disini":
        print("Isi env ROBLOX_API_KEY dulu atau edit file ini.")
        return 2
    for universe_id in EXPERIENCE_IDS:
        print(f"Grant asset {ASSET_ID} to universe {universe_id}")
        result = await grant_asset_permission_to_universe(api_key=ROBLOX_API_KEY, asset_id=ASSET_ID, universe_id=universe_id)
        print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
