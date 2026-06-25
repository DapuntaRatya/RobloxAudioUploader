from typing import Dict, List

from app.config import settings
from app.modules.roblox.client import RobloxClient


async def grant_assets_permission_to_universe(
    *,
    api_key: str,
    asset_ids: List[str],
    universe_id: str,
) -> Dict:
    clean_asset_ids = [str(asset_id).strip() for asset_id in asset_ids if str(asset_id).strip()]

    payload = {
        "subjectType": "Universe",
        "subjectId": str(universe_id),
        "action": "Use",
        "requests": [
            {
                "assetId": str(asset_id),
                "grantToDependencies": True,
            }
            for asset_id in clean_asset_ids
        ],
    }

    client = RobloxClient(api_key)

    response = await client.request(
        "PATCH",
        settings.ROBLOX_PERMISSION_URL,
        headers={"Content-Type": "application/json"},
        json=payload,
    )

    if not response.text.strip():
        return {
            "successAssetIds": [int(asset_id) for asset_id in clean_asset_ids if str(asset_id).isdigit()],
            "errors": [],
        }

    return response.json()


async def grant_asset_permission_to_universe(
    *,
    api_key: str,
    asset_id: str,
    universe_id: str,
) -> Dict:
    return await grant_assets_permission_to_universe(
        api_key=api_key,
        asset_ids=[str(asset_id)],
        universe_id=str(universe_id),
    )
