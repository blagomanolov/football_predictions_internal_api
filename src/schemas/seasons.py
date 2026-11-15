"""Pydantic DTOs for seasons create, update, and read operations."""

from __future__ import annotations

from typing import Optional
from datetime import date

from pydantic import BaseModel, ConfigDict, Field

from schemas.base import TimestampBase

class SeasonsBase(BaseModel):
    """Shared seasons fields used by create and read schemas."""

    competition_id: int = Field(...)
    name: str = Field(..., max_length=50)
    start_date: date = Field(...)
    end_date: date = Field(...)
    is_current: bool = Field(default=False)

class SeasonsCreate(SeasonsBase):
    """Payload for creating a seasons record."""

    pass

class SeasonsUpdate(BaseModel):
    """Partial payload for updating a season record."""

    competition_id: Optional[int] = None
    name: Optional[str] = Field(None, max_length=50)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_current: Optional[bool] = None

class SeasonsRead(SeasonsBase, TimestampBase):
    """Seasons representation returned by the API."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: int

class SeasonsReadWithCountryAndCompetitions(SeasonsRead):
    """Seasons representation enriched with the associated country name and competition name."""
    competition_name: str = Field(..., max_length=120, description="Name of the associated competition.")
    country_name: str = Field(..., max_length=100, description="Name of the associated country.")

class SeasonsReadWithCompetitions(SeasonsRead):
    """Seassons representation enriched with the associated competition name."""
    competition_name: str = Field(..., max_length=120, description="Name of the associated competition.")