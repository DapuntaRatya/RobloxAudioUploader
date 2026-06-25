from cryptography.fernet import Fernet, InvalidToken

from app.config import settings
from app.core.errors import AppError


class CryptoService:
    def __init__(self):
        if not settings.FERNET_KEY or settings.FERNET_KEY.startswith("CHANGE_ME"):
            raise AppError(
                "FERNET_KEY_MISSING",
                "FERNET_KEY belum diset. Jalankan python scripts/make_fernet_key.py lalu isi .env.",
                status_code=500,
            )
        self.fernet = Fernet(settings.FERNET_KEY.encode("utf-8"))

    def encrypt(self, value: str) -> str:
        return self.fernet.encrypt(value.encode("utf-8")).decode("utf-8")

    def decrypt(self, value: str) -> str:
        try:
            return self.fernet.decrypt(value.encode("utf-8")).decode("utf-8")
        except InvalidToken as exc:
            raise AppError(
                "DECRYPT_FAILED",
                "Gagal decrypt API key. Cek FERNET_KEY.",
                status_code=500,
            ) from exc


_crypto: CryptoService | None = None


def crypto() -> CryptoService:
    global _crypto
    if _crypto is None:
        _crypto = CryptoService()
    return _crypto
