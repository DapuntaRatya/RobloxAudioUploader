import asyncio
from typing import Any, Dict, List

from app.config import settings
from app.modules.roblox.client import RobloxClient


def _state_flags(payload: Dict[str, Any]) -> dict:
    moderation_state = (
        payload.get("moderationResult", {}).get("moderationState")
        or payload.get("moderationState")
        or "Unknown"
    )
    state = payload.get("state") or "Unknown"

    moderation_lower = str(moderation_state).lower()
    state_lower = str(state).lower()

    is_blocked = (
        moderation_lower not in {"approved", "unknown", "pending"}
        or state_lower in {"blocked", "deleted", "moderated"}
    )

    is_archived = state_lower == "archived"
    can_played = moderation_lower == "approved" and state_lower == "active"

    return {
        "moderation_state": moderation_state,
        "asset_state": state,
        "is_blocked": is_blocked,
        "is_archived": is_archived,
        "can_played": can_played,
        "availability_type": (
            "blocked" if is_blocked else
            "archived" if is_archived else
            "can_played" if can_played else
            "unknown"
        ),
    }


async def get_asset_info(api_key: str, asset_id: str) -> Dict[str, Any]:
    client = RobloxClient(api_key)
    url = f"{settings.ROBLOX_ASSETS_BASE_URL}/assets/{asset_id}"
    response = await client.request("GET", url)
    return response.json()


async def enrich_assets_with_roblox_info(
    *,
    api_key: str,
    assets: List[dict],
    concurrency: int = 5,
) -> List[dict]:
    semaphore = asyncio.Semaphore(concurrency)

    async def enrich(asset: dict) -> dict:
        asset_id = str(asset.get("asset_id") or "").strip()
        if not asset_id:
            return asset

        async with semaphore:
            try:
                payload = await get_asset_info(api_key, asset_id)
            except Exception as exc:
                enriched = dict(asset)
                enriched["metadata_fetch_status"] = "failed"
                enriched["metadata_fetch_error"] = str(exc)
                enriched["moderation_state"] = enriched.get("moderation_state") or "Unknown"
                enriched["asset_state"] = enriched.get("asset_state") or "Unknown"
                return enriched

        flags = _state_flags(payload)
        creator = payload.get("creationContext", {}).get("creator", {})

        enriched = dict(asset)
        enriched.update({
            "metadata_fetch_status": "success",
            "path": payload.get("path"),
            "revision_id": payload.get("revisionId"),
            "revision_create_time": payload.get("revisionCreateTime"),
            "asset_id": str(payload.get("assetId") or asset_id),
            "title": payload.get("displayName") or asset.get("title") or "Untitled Audio",
            "display_name": payload.get("displayName") or asset.get("title") or "Untitled Audio",
            "description": payload.get("description") or asset.get("description") or "-",
            "asset_type": payload.get("assetType") or asset.get("asset_type") or "Audio",
            "creator_user_id": creator.get("userId") or asset.get("creator_user_id"),
            "creator_group_id": creator.get("groupId") or asset.get("creator_group_id"),
            "created_time": payload.get("revisionCreateTime") or asset.get("created_time"),
            "asset_url": f"https://create.roblox.com/store/asset/{payload.get('assetId') or asset_id}",
        })
        enriched.update(flags)
        return enriched

    return await asyncio.gather(*[enrich(asset) for asset in assets])
