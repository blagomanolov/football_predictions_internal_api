"""Data-acess layer for the ``SeasonTeams`` ORM model"""

from __future__ import annotations

from typing import List, Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from models.season_teams import SeasonTeams
from models.teams import Teams
from models.seasons import Seasons
from models.countries import Countries
from repositories.base import BaseRepository

class SeasonTeamsRepository(BaseRepository[SeasonTeams]):
    """Repository specializing ``BaseRepository`` for season_teams."""

    def __init__(self, session: AsyncSession) -> None:
        """Create a season_teams repository bound to ``session.

        Args:
            session: Request-scoped async SQLAlchemy session
        """
        super().__init__(SeasonTeams, session, "id")

    async def get_many_by_country_name(
        self, country_names: List[str]
    ) -> Sequence[tuple[SeasonTeams, str, str]]:
        """Fetch season_teams joined with team name and season name by country name.

        Args:
            country_names: List of country names to filter by (e.g. ``['England', 'Germany']``).

        Returns:
            A sequence of database row tuples containing ``(SeasonTeams, season_name, team_name, country_name)``.
        """
        stmt = (
            select(SeasonTeams, Seasons.name.label("season_name"), Teams.name.label("team_name"), Countries.name.label("country_name"))
            .join(Seasons, Seasons.id == SeasonTeams.season_id)
            .join(Teams, Teams.id == SeasonTeams.team_id)
            .join(Countries, Countries.id == Teams.country_id)
            .where(Countries.name.in_(country_names))
        )
        result = await self.session.execute(stmt)
        return result.all()