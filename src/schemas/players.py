"""Pydantic DTOs for players create, update, and read operations."""

from __future__ import annotations

from typing import Optional
from datetime import date

from pydantic import BaseModel, ConfigDict, Field

from schemas.base import TimestampFullBase

class PlayersBase(BaseModel):
    """Shared players fields used by create and read schemas."""

    nationality_country_id: Optional[int] = None
    first_name: str = Field(..., max_length=80)
    last_name: str = Field(..., max_length=80)
    full_name: str = Field(..., max_length=180)
    common_name: Optional[str] = Field(default=None, max_length=80)
    birth_date: Optional[date] = None
    height_cm: Optional[int] = None
    weight_kg: Optional[int] = None
    preferred_foot: str = Field(default='right', pattern=f"^(left|right|both)$")
    primary_position: str = Field(pattern=f"^(GK|DF|MF|FW)$")
    detailed_position: str = Field(pattern=f"^(GK|CB|LB|RB|LWB|RWB|CDM|CM|CAM|LM|RM|LW|RW|CF|ST)$")
    market_value_eur: int = Field(default=0)
    photo_url: Optional[str] = Field(default=None, max_length=255)
    is_active: bool = Field(default=True)

class PlayersCreate(PlayersBase):
    """Payload for creating a player record."""
    
    pass

class PlayersUpdate(BaseModel):
    """Partial payload for updating a player record."""

    nationality_country_id: Optional[int] = None
    country_name: Optional[str] = Field(None, max_length=100, description="Name of nationality country (e.g. 'England')")
    
    first_name: Optional[str] = Field(None, max_length=80)
    last_name: Optional[str] = Field(None, max_length=80)
    full_name: Optional[str] = Field(None, max_length=180)
    common_name: Optional[str] = Field(None, max_length=80)
    birth_date: Optional[date] = None
    height_cm: Optional[int] = None
    weight_kg: Optional[int] = None
    preferred_foot: Optional[str] = Field(None, pattern=f"^(left|right|both)$")
    primary_position: Optional[str] = Field(None, pattern=f"^(GK|DF|MF|FW)$")
    detailed_position: Optional[str] = Field(None, pattern=f"^(GK|CB|LB|RB|LWB|RWB|CDM|CM|CAM|LM|RM|LW|RW|CF|ST)$")
    market_value_eur: Optional[int]  = None
    photo_url: Optional[str] = Field(None,max_length=255)
    is_active: Optional[bool] = None

class PlayersRead(PlayersBase, TimestampFullBase):
    """Players representation returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int

class PlayersReadWithCountry(PlayersBase):
    """Players representation enriched with the associated country name"""

    country_name: Optional[str] = Field(default=None, max_length=100, description="Name of the associated country.")