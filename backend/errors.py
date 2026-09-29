"""Typed application errors mapped to clean, non-technical JSON responses.

Upstream exception text is logged server-side only; it can contain workspace
URLs, statement IDs, or other internal details that must not reach the UI.
"""


class AppError(Exception):
    status_code = 500
    code = "INTERNAL_ERROR"
    message = "Something went wrong. Please try again."

    def __init__(self, message: str | None = None):
        super().__init__(message or self.message)
        if message:
            self.message = message

    def to_dict(self) -> dict:
        return {"error": {"code": self.code, "message": self.message}}


class WarehouseUnavailable(AppError):
    status_code = 503
    code = "WAREHOUSE_UNAVAILABLE"
    message = "The SQL warehouse is starting up or temporarily unavailable. Please retry in a moment."


class SearchUnavailable(AppError):
    status_code = 503
    code = "SEARCH_UNAVAILABLE"
    message = "Document search is temporarily unavailable. Please retry in a moment."


class ModelUnavailable(AppError):
    status_code = 503
    code = "MODEL_UNAVAILABLE"
    message = "The answer-generation model is temporarily unavailable. Please retry in a moment."


class UpstreamTimeout(AppError):
    status_code = 504
    code = "UPSTREAM_TIMEOUT"
    message = "The request took too long to complete. Please retry; the warehouse may be warming up."


class UnknownAsset(AppError):
    status_code = 404
    code = "UNKNOWN_ASSET"

    def __init__(self, asset_id: str):
        super().__init__(f"No asset '{asset_id}' exists in the Blue River Power portfolio.")


class InvalidRequest(AppError):
    status_code = 422
    code = "INVALID_REQUEST"
    message = "The request was not valid."


class NotConfigured(AppError):
    status_code = 503
    code = "SERVICE_NOT_CONFIGURED"

    def __init__(self, what: str):
        super().__init__(f"The {what} is not configured for this app.")
