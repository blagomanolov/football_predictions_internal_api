"""Pydantic DTOs for teams create, update, and read operations."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from schemas.base import TimestampBase

class TeamsBase(BaseModel):
    """Shared teams fields used by create and read schemas."""

    country_id: Optional[int] = None
    venue_id: Optional[int] = None
    name: str = Field(..., max_length=120)
    short_name: str = Field(..., max_length=50)
    code: str = Field(..., max_length=10)
    founded_year: Optional[int] = None
    current_manager: Optional[str] = Field(None, max_length=100)
    website_url: Optional[str] = Field(None, max_length=255)
    logo_url: Optional[str] = Field(None, max_length=255)

class TeamsCreate(TeamsBase):
    """Payload for creating a teams record."""

    pass

class TeamsUpdate(BaseModel):
    """Partial payload for updating a competition record."""

    country_id: Optional[int] = None
    venue_id: Optional[int] = None
    name: Optional[str] = Field(None, max_length=120)
    short_name: Optional[str] = Field(None, max_length=50)
    code: Optional[str] = Field(None, max_length=10)
    founded_year: Optional[int] = None
    current_manager: Optional[str] = Field(None, max_length=100)
    website_url: Optional[str] = Field(None, max_length=255)
    logo_url: Optional[str] = Field(None, max_length=255)

class TeamsRead(TeamsBase, TimestampBase):
    """Teams representation returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int 

class TeamsReadWithCountryAndCityAndVenue(TeamsRead):
    """Teams representation enriched with the associated country name and venue."""

    country_name: Optional[str] = Field(default=None, max_length=100, description="Name of the associated country.")
    venue_name: Optional[str] = Field(default=None, max_length=150, description="Name of the associated venue.")
    city_name: Optional[str] = Field(default=None, max_length=100, description="Name of the associated ciy.")
