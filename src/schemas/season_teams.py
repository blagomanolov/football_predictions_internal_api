"""Pydantic DTOs for season_teams create, update, and read operations."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from schemas.base import TimestampBase

class SeasonTeamsBase(BaseModel):
    """Shared season_teams fields used by create and read schemas."""

    season_id: int = Field(...)
    team_id: int = Field(...)

class SeasonTeamsCreate(SeasonTeamsBase):
    """Payload for creating a season_teams record."""
    pass

class SeasonTeamsUpdate(BaseModel):
    """Partial payload for updating a season_teams record."""
    season_id: Optional[int] = None
    team_id: Optional[int] = None

class SeasonTeamsRead(SeasonTeamsBase, TimestampBase):
    """Season representation returned by the API."""
    model_config = ConfigDict(from_attributes=True)

    id: int

class SeasonTeamsWithSeasonAndTeam(SeasonTeamsRead):
    """SeasonTeams representation enriched with the associated
    season and team, and country."""
    season_name: str = Field(..., max_length=50, description="Name of the associated season.")
    team_name: str = Field(..., max_length=120, description="Name of the associated team.")
    country_name: str = Field(..., max_length=100, description="Name of the associated country")