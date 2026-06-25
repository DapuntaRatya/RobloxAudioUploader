def roblox_http_error_message(status_code: int) -> str:
    if status_code == 400:
        return "Request Roblox tidak valid. Cek payload, assetId, creator, atau permission."
    if status_code == 401:
        return "API key tidak valid atau tidak terkirim."
    if status_code == 403:
        return "API key tidak punya permission yang cukup."
    if status_code == 404:
        return "Endpoint/resource Roblox tidak ditemukan."
    if status_code == 429:
        return "Kena rate limit dari Roblox. Coba lagi nanti."
    if 500 <= status_code <= 599:
        return "Server Roblox sedang error atau tidak stabil."
    return "Roblox API mengembalikan error."
