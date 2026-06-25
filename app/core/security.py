import secrets


def generate_id(prefix: str) -> str:
    token = secrets.token_urlsafe(18).replace("-", "").replace("_", "")[:22]
    return f"{prefix}_{token}"


def mask_secret(value: str, left: int = 12, right: int = 6) -> str:
    if not value:
        return ""
    if len(value) <= left + right:
        return "*" * len(value)
    return f"{value[:left]}...{value[-right:]}"
