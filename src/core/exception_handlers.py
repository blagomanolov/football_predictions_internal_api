"""FastAPI exception handlers that emit the unified ``ErrorResponse`` body."""

from __future__ import annotations

from typing import Any, Optional

import structlog
from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import InterfaceError, OperationalError
from sqlalchemy.exc import TimeoutError as PoolTimeoutError
from starlette.exceptions import HTTPException as StarletteHTTPException

from configs.config import get_settings
from core.exceptions import AppError
from schemas.errors import ErrorResponse

log = structlog.get_logger(__name__)

_DB_UNAVAILABLE_ERRORS = (OperationalError, InterfaceError, PoolTimeoutError)


def _request_id(request: Request) -> str:
    """Return the correlation id set by ``RequestLoggingMiddleware``, or ``'-'``."""
    return getattr(request.state, "request_id", "-")


def _body(
    request: Request,
    code: str,
    message: str,
    details: Optional[Any] = None,
) -> dict:
    """Build a serialized ``ErrorResponse`` including ``request_id``.

    Args:
        request: Current request (source of the request id).
        code: Stable error code.
        message: Human-readable message.
        details: Optional structured details.

    Returns:
        Dict suitable for ``JSONResponse(content=...)``.
    """
    return ErrorResponse(
        code=code,
        message=message,
        details=details,
        request_id=_request_id(request),
    ).model_dump()


def register_exception_handlers(app: FastAPI) -> None:
    """Attach domain, HTTP, validation, database and catch-all handlers to ``app``.

    Note:
        Unhandled exceptions are logged once, with traceback, by
        ``RequestLoggingMiddleware`` (``request_failed``); the catch-all handler
        below only builds the response.

    Args:
        app: FastAPI application instance.
    """

    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        """Map ``AppError`` subclasses to their status code and error body."""
        level = "error" if exc.status_code >= 500 else "info"
        getattr(log, level)(
            "app_error",
            code=exc.code,
            status_code=exc.status_code,
            message=exc.message,
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=_body(request, exc.code, exc.message, exc.details),
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        """Normalize Starlette/FastAPI ``HTTPException`` into ``ErrorResponse``."""
        detail = exc.detail
        message = detail if isinstance(detail, str) else "HTTP error"
        details = None if isinstance(detail, str) else jsonable_encoder(detail)
        return JSONResponse(
            status_code=exc.status_code,
            content=_body(request, "http_error", message, details),
            headers=getattr(exc, "headers", None),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        """Return 422 with Pydantic validation errors in ``details``."""
        return JSONResponse(
            status_code=422,
            content=_body(
                request,
                "validation_error",
                "Request validation failed",
                jsonable_encoder(exc.errors()),
            ),
        )

    async def database_unavailable_handler(request: Request, exc: Exception) -> JSONResponse:
        """Return 503 when the database is unreachable or the pool is exhausted."""
        log.error("database_unavailable", error_type=type(exc).__name__)
        return JSONResponse(
            status_code=503,
            content=_body(
                request,
                "service_unavailable",
                "Service temporarily unavailable. Please retry shortly.",
            ),
            headers={"Retry-After": "5"},
        )

    for exc_type in _DB_UNAVAILABLE_ERRORS:
        app.add_exception_handler(exc_type, database_unavailable_handler)

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        """Return 500; hide exception details when ``DEBUG`` is false."""
        settings = get_settings()
        message = str(exc) if settings.debug else "Internal server error"
        details = {"type": type(exc).__name__} if settings.debug else None
        return JSONResponse(
            status_code=500,
            content=_body(request, "internal_error", message, details),
        )