class AppError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400, details=None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details


class AuthError(AppError):
    pass


class ValidationAppError(AppError):
    pass


class RobloxApiError(AppError):
    pass


class DownloaderError(AppError):
    pass


class JobError(AppError):
    pass
