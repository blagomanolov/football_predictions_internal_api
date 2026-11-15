"""Pydantic DTOs for venues create, update, and read operations."""

from __future__ import annotations

from typing import Optional
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from schemas.base import TimestampBase

class VenuesBase(BaseModel):
    """Shared venues fields used by create and read schemas."""

    country_id: Optional[int] = None
    name: str = Field(..., max_length=150)
    city: str = Field(..., max_length=100)
    capacity: Optional[int] = None
    surface: str = Field(default='natural_grass', pattern=f"^(natural_grass|hybrid_grass|artificial_turf)$")
    pitch_length_m: Decimal = Field(default=Decimal('105.00'), max_digits=5, decimal_places=2)
    pitch_width_m: Decimal = Field(default=Decimal('68.00'), max_digits=5, decimal_places=2)
    altitude_m: int = 0
    latitude: Optional[Decimal] = Field(default=None, max_digits=9, decimal_places=6)
    longitude: Optional[Decimal] = Field(default=None, max_digits=9, decimal_places=6)

class VenuesCreate(VenuesBase):
    """Payload for creating a venues record."""

    pass

class VenuesUpdate(BaseModel):
    """Partial payload for updating a venues record."""

    country_id: Optional[int] = None
    name: Optional[str] = Field(None, max_length=150)
    city: Optional[str] = Field(None, max_length=100)
    capacity: Optional[int] = None
    surface: Optional[str] = Field(None, pattern=f"^(natural_grass|hybrid_grass|artificial_turf)$")
    pitch_length_m: Optional[Decimal] = Field(None, max_digits=5, decimal_places=2)
    pitch_width_m: Optional[Decimal] = Field(None, max_digits=5, decimal_places=2)
    altitude_m: Optional[int] = None
    latitude: Optional[Decimal] = Field(None, max_digits=9, decimal_places=6)
    longitude: Optional[Decimal] = Field(default=None, max_digits=9, decimal_places=6)

class VenuesRead(VenuesBase, TimestampBase):
    """Venues representation returned by the API."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: int

class VenuesReadWithCountry(VenuesRead):
    """Venues representation enriched with the associated country name."""

    country_name: str = Field(..., max_length=100, description="Name of the associated country.")
