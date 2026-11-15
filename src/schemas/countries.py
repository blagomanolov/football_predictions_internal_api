"""Pydantic DTOs for country create, update, and read operations."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from schemas.base import TimestampBase


class CountriesBase(BaseModel):
    """Shared country fields used by create and read schemas."""

    name: str = Field(..., max_length=100)
    code_alpha2: str = Field(..., max_length=2)
    code_alpha3: str = Field(..., max_length=3)
    confederation: str = Field(..., max_length=20)
    flag_url: Optional[str] = Field(None, max_length=255)


class CountriesCreate(CountriesBase):
    """Payload for creating a country record."""

    pass


class CountriesUpdate(BaseModel):
    """Partial payload for updating a country record."""

    name: Optional[str] = Field(None, max_length=100)
    code_alpha2: Optional[str] = Field(None, max_length=2)
    code_alpha3: Optional[str] = Field(None, max_length=3)
    confederation: Optional[str] = Field(None, max_length=20)
    flag_url: Optional[str] = Field(None, max_length=255)


class CountriesRead(CountriesBase, TimestampBase):
    """Country representation returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
