"""Generic filter item schema for future query/filter endpoints."""

from __future__ import annotations

from typing import Any, List, Optional

from pydantic import BaseModel, Field


class FilterItem(BaseModel):
    """Single field filter with optional comparison operators.

    Attributes:
        field: ORM / API field name to filter on.
        eq: Equality match.
        in_: Membership match (serialized as ``in``).
        lt / lte / gt / gte: Inequality bounds.
        like: SQL LIKE pattern.
    """

    field: str
    eq: Optional[Any] = None
    in_: Optional[List[Any]] = Field(default=None, alias="in")
    lt: Optional[Any] = None
    lte: Optional[Any] = None
    gt: Optional[Any] = None
    gte: Optional[Any] = None
    like: Optional[str] = None
