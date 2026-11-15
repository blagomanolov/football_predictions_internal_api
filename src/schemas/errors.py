"""API error response schema shared by all exception handlers."""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel


class ErrorResponse(BaseModel):
    """Stable error body returned to API clients.

    Attributes:
        code: Machine-stable error code (e.g. ``not_found``).
        message: Human-readable description.
        details: Optional structured context (validation errors, etc.).
        request_id: Correlation id for log lookup.
    """

    code: str
    message: str
    details: Optional[Any] = None
    request_id: Optional[str] = None
