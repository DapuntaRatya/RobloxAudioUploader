from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class RobloxOperationResponse(BaseModel):
    path: str
    operationId: Optional[str] = None
    done: bool = False
    response: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None


class RobloxAssetResponse(BaseModel):
    assetId: str
    displayName: str
    assetType: str
    path: Optional[str] = None


class PermissionResult(BaseModel):
    successAssetIds: List[int] = []
    errors: List[Dict[str, Any]] = []
