"""Domain exceptions raised by services and mapped to HTTP by handlers.

Services must raise these types instead of FastAPI ``HTTPException``.
"""

from __future__ import annotations

from typing import Any, Optional


class AppError(Exception):
    """Base domain error with stable ``code`` and HTTP ``status_code``.

    Attributes:
        message: Human-readable error description.
        code: Machine-stable error code for API clients.
        status_code: HTTP status applied by the exception handler.
        details: Optional structured context (never put secrets here).
    """

    def __init__(
        self,
        message: str,
        *,
        code: str = "app_error",
        status_code: int = 400,
        details: Optional[Any] = None,
    ) -> None:
        """Create a domain error.

        Args:
            message: Human-readable description.
            code: Stable error code string.
            status_code: HTTP status for the handler response.
            details: Optional extra payload for clients.
        """
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details
        super().__init__(message)


class NotFoundError(AppError):
    """Resource was not found (HTTP 404 / ``not_found``)."""

    def __init__(
        self,
        message: str = "Resource not found",
        *,
        code: str = "not_found",
        details: Any = None,
    ) -> None:
        """Create a not-found error."""
        super().__init__(message, code=code, status_code=404, details=details)


class ConflictError(AppError):
    """Request conflicts with current state (HTTP 409 / ``conflict``)."""

    def __init__(
        self,
        message: str = "Conflict",
        *,
        code: str = "conflict",
        details: Any = None,
    ) -> None:
        """Create a conflict error."""
        super().__init__(message, code=code, status_code=409, details=details)


class UnauthorizedError(AppError):
    """Caller is not authenticated (HTTP 401 / ``unauthorized``)."""

    def __init__(
        self,
        message: str = "Unauthorized",
        *,
        code: str = "unauthorized",
        details: Any = None,
    ) -> None:
        """Create an unauthorized error."""
        super().__init__(message, code=code, status_code=401, details=details)


class ForbiddenError(AppError):
    """Caller is authenticated but not allowed (HTTP 403 / ``forbidden``)."""

    def __init__(
        self,
        message: str = "Forbidden",
        *,
        code: str = "forbidden",
        details: Any = None,
    ) -> None:
        """Create a forbidden error."""
        super().__init__(message, code=code, status_code=403, details=details)
