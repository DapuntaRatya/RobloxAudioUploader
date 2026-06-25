from typing import Any, Dict

from app.core.security import mask_secret
from app.infra.encryption import crypto
from app.modules.roblox.api_key import introspect_api_key, validate_api_key_info


class AuthService:
    async def introspect_and_validate(self, api_key: str) -> Dict[str, Any]:
        info = await introspect_api_key(api_key)
        validate_api_key_info(info)
        return info

    def encrypted_api_key(self, api_key: str) -> str:
        return crypto().encrypt(api_key)

    def decrypt_api_key(self, encrypted: str) -> str:
        return crypto().decrypt(encrypted)

    def mask_api_key(self, api_key: str) -> str:
        return mask_secret(api_key)
