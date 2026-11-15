"""Pydantic DTOs for competitions create, update, and read operations."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from schemas.base import TimestampBase

class CompetitionsBase(BaseModel):
    """Shared competitions fields used by create and read schemas."""

    country_id: Optional[int] = None
    name: str = Field(..., max_length=120)
    code: str = Field(..., max_length=20)
    type: str = Field(default='domestic_league', pattern=f"^(domestic_league|domestic_cup|continental_cup|international)$")
    tier: int = 1
    logo_url: Optional[str] = Field(default=None, max_length=255)
    is_active: int = 1

class CompetitionsCreate(CompetitionsBase):
    """Payload for creating a competitions record."""

    pass

class CompetitionsUpdate(BaseModel):
    """Partial payload for updating a competition record."""

    country_id: Optional[int] = None
    name: Optional[str] = Field(None, max_length=120)
    code: Optional[str] = Field(None, max_length=20)
    type: Optional[str] = Field(None, pattern=f"^(domestic_league|domestic_cup|continental_cup|international)$")
    tier: Optional[int] = None
    logo_url: Optional[str] = Field(None, max_length=255)
    is_active: Optional[int] = None

class CompetitionsRead(CompetitionsBase, TimestampBase):
    """Competitions representation returned by the API."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: int

class CompetitionsReadWithCountry(CompetitionsRead):
    """Competitions representation enriched with the associated country name."""

    country_name: str = Field(..., max_length=100, description="Name of the associated country.")
