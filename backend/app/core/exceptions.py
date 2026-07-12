"""
Domain exceptions and global FastAPI error handlers.
Every domain exception maps to one HTTP status code.
The error envelope format is consistent across all endpoints.
"""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import logging
import traceback

logger = logging.getLogger(__name__)


# ── Domain Exceptions ──────────────────────────────────────────────

class DomainError(Exception):
    """Base for all domain errors raised in the service layer."""
    def __init__(self, code: str, message: str, details: dict | None = None):
        self.code = code
        self.message = message
        self.details = details or {}
        super().__init__(message)


class NotFoundError(DomainError):
    """Resource not found → 404"""
    def __init__(self, message: str = "Resource not found", code: str = "NOT_FOUND", details: dict | None = None):
        super().__init__(code=code, message=message, details=details)


class ConflictError(DomainError):
    """Conflicting state → 409"""
    def __init__(self, message: str = "Conflict", code: str = "CONFLICT", details: dict | None = None):
        super().__init__(code=code, message=message, details=details)


class PermissionDeniedError(DomainError):
    """Caller lacks the required role → 403"""
    def __init__(self, message: str = "Permission denied", code: str = "FORBIDDEN", details: dict | None = None):
        super().__init__(code=code, message=message, details=details)


class DomainValidationError(DomainError):
    """Business-rule validation failure → 422"""
    def __init__(self, message: str = "Validation error", code: str = "VALIDATION_ERROR", details: dict | None = None):
        super().__init__(code=code, message=message, details=details)


# ── Error envelope builder ─────────────────────────────────────────

def _error_envelope(code: str, message: str, details: dict | None = None) -> dict:
    body = {"error": {"code": code, "message": message}}
    if details:
        body["error"]["details"] = details
    return body


# ── Register handlers on the FastAPI app ───────────────────────────

def register_exception_handlers(app: FastAPI):
    """Call once from the app factory to wire up all global handlers."""

    @app.exception_handler(NotFoundError)
    async def not_found_handler(_req: Request, exc: NotFoundError):
        return JSONResponse(status_code=404, content=_error_envelope(exc.code, exc.message, exc.details))

    @app.exception_handler(ConflictError)
    async def conflict_handler(_req: Request, exc: ConflictError):
        return JSONResponse(status_code=409, content=_error_envelope(exc.code, exc.message, exc.details))

    @app.exception_handler(PermissionDeniedError)
    async def permission_handler(_req: Request, exc: PermissionDeniedError):
        return JSONResponse(status_code=403, content=_error_envelope(exc.code, exc.message, exc.details))

    @app.exception_handler(DomainValidationError)
    async def validation_handler(_req: Request, exc: DomainValidationError):
        return JSONResponse(status_code=422, content=_error_envelope(exc.code, exc.message, exc.details))

    @app.exception_handler(Exception)
    async def unhandled_handler(_req: Request, exc: Exception):
        logger.error(f"Unhandled exception: {exc}\n{traceback.format_exc()}")
        return JSONResponse(
            status_code=500,
            content=_error_envelope("INTERNAL_ERROR", "An internal error occurred."),
        )
