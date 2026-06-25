from typing import Any, Optional


def success_response(data: Optional[Any] = None) -> dict:
    return {
        "status": "success",
        "data": data if data is not None else {},
        "error": None,
    }


def failed_response(code: str, message: str, details: Optional[Any] = None) -> dict:
    return {
        "status": "failed",
        "data": None,
        "error": {
            "code": code,
            "message": message,
            "details": details,
        },
    }
