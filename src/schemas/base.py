"""Shared Pydantic base schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Generic, Optional, Sequence, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class TimestampBase(BaseModel):
    """Optional creation timestamp mixed into read DTOs."""

    created_at: Optional[datetime] = None

class TimestampFullBase(TimestampBase):
    """Optional creation timestamp mixed into read DTOs."""

    updated_at: Optional[datetime] = None


class DeleteConfirmation(BaseModel):
    """Generic confirmation payload returned after a successful deletion."""

    id: int = Field(..., description="ID of the deleted entity")
    message: str = Field(..., description="Human-readable success message")
    success: bool = Field(default=True, description="Deletion status flag")


class PageResponse(BaseModel, Generic[T]):
    """Standardized paginated envelope returned by list and search queries."""

    items: Sequence[T] = Field(..., description="List of items for the current page")
    total: int = Field(..., ge=0, description="Total matching items across all pages")
    skip: int = Field(..., ge=0, description="Number of items skipped")
    limit: int = Field(..., ge=1, description="Page size limit")
