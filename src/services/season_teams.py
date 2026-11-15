"""Business logic for season_teams lookups."""

from __future__ import annotations

from typing import List, Optional

from schemas.filters import FilterItem
from schemas.base import PageResponse
from core.exceptions import NotFoundError
from core.db_error_handler import handle_integrity_error
from repositories.season_teams import SeasonTeamsRepository
from schemas.season_teams import (
    SeasonTeamsRead,
    SeasonTeamsCreate,
    SeasonTeamsUpdate,
    SeasonTeamsWithSeasonAndTeam,
)

class SeasonTeamsService:
    """SeasonTeams use cases; raises domain errors, not HTTP exceptions."""
    def __init__(self, repository: SeasonTeamsRepository) -> None:
        """Bind a season_teams repository.
        
        Args:
            repository: Data-acess collaborator."""
        self.repository: SeasonTeamsRepository = repository

    async def get_many_by_countries(
        self, countries: List[str]
    ) -> List[SeasonTeamsWithSeasonAndTeam]:
        """Retrieve season_teams associated with specified country names.

        Args:
            countries: List of country names to filter by (e.g. ``['England', 'Germany']``).

        Returns:
            List of season_teams DTOs enriched with their associated country name.

        Raises:
            NotFoundError: If no season_teams match the specified country names.
        """
        objs = await self.repository.get_many_by_country_name(countries)
        if not objs:
            raise NotFoundError("SeasonTeams not found.")
        return [
            SeasonTeamsWithSeasonAndTeam(
                **SeasonTeamsRead.model_validate(season_team).model_dump(),
                season_name=season,
                team_name=team,
                country_name=country
            )
            for season_team, season, team, country in objs
        ]