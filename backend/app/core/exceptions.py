"""Application-level exceptions and their FastAPI handlers.

Every error response returned by this API follows the same JSON shape:

    {"error": {"code": "SOME_CODE", "message": "human readable", "details": {...}}}

so frontend error handling never has to branch on which endpoint failed.
"""

from __future__ import annotations

import logging

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("zeroday.errors")


class AppError(Exception):
    """Base class for domain errors that should surface as clean API responses."""

    def __init__(
        self,
        message: str,
        *,
        code: str = "APP_ERROR",
        status_code: int = status.HTTP_400_BAD_REQUEST,
        details: dict | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}


class NotFoundError(AppError):
    def __init__(self, message: str = "Resource not found", **kwargs) -> None:
        kwargs.setdefault("code", "NOT_FOUND")
        kwargs.setdefault("status_code", status.HTTP_404_NOT_FOUND)
        super().__init__(message, **kwargs)


class UnauthorizedError(AppError):
    def __init__(self, message: str = "Authentication required", **kwargs) -> None:
        kwargs.setdefault("code", "UNAUTHORIZED")
        kwargs.setdefault("status_code", status.HTTP_401_UNAUTHORIZED)
        super().__init__(message, **kwargs)


class ForbiddenError(AppError):
    def __init__(self, message: str = "Not permitted", **kwargs) -> None:
        kwargs.setdefault("code", "FORBIDDEN")
        kwargs.setdefault("status_code", status.HTTP_403_FORBIDDEN)
        super().__init__(message, **kwargs)


class ConflictError(AppError):
    def __init__(self, message: str = "Conflicting state", **kwargs) -> None:
        kwargs.setdefault("code", "CONFLICT")
        kwargs.setdefault("status_code", status.HTTP_409_CONFLICT)
        super().__init__(message, **kwargs)


def _error_body(code: str, message: str, details: dict | None = None) -> dict:
    return {"error": {"code": code, "message": message, "details": details or {}}}


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def handle_app_error(request: Request, exc: AppError) -> JSONResponse:
        logger.warning(
            "%s %s -> %s: %s", request.method, request.url.path, exc.code, exc.message
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=_error_body(exc.code, exc.message, exc.details),
        )

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_exception(
        request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=_error_body("HTTP_ERROR", str(exc.detail)),
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=_error_body(
                "VALIDATION_ERROR",
                "Request validation failed",
                {"errors": exc.errors()},
            ),
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled error on %s %s", request.method, request.url.path)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=_error_body("INTERNAL_ERROR", "An unexpected error occurred"),
        )
