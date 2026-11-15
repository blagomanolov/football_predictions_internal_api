"""Data-access layer for the ``Teams`` ORM model."""

from __future__ import annotations

from typing import List, Sequence

from sqlalchemy import Row, Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.countries import Countries
from models.teams import Teams
from models.venues import Venues
from repositories.base import BaseRepository


class TeamsRepository(BaseRepository[Teams]):
    """Repository specializing ``BaseRepository`` for teams."""

    def __init__(self, session: AsyncSession) -> None:
        """Create a teams repository bound to ``session``.

        Args:
            session: Request-scoped async SQLAlchemy session.
        """
        super().__init__(Teams, session, "id")

    @staticmethod
    def _with_location_stmt() -> Select:
        """Base query: team + venue name + city + country name.

        Outer joins are used because ``teams.venue_id`` and ``teams.country_id``
        are nullable; inner joins would silently drop such teams.
        """
        return (
            select(
                Teams,
                Venues.name.label("venue_name"),
                Venues.city.label("city_name"),
                Countries.name.label("country_name"),
            )
            .select_from(Teams)
            .outerjoin(Venues, Venues.id == Teams.venue_id)
            .outerjoin(Countries, Countries.id == Teams.country_id)
            .order_by(Teams.id)
        )

    async def get_many_by_country_name(
        self, country_names: List[str]
    ) -> Sequence[Row]:
        """Fetch teams with venue/city/country by a list of country names.

        Args:
            country_names: Country names to filter by (e.g. ``['England', 'Germany']``).

        Returns:
            Rows of ``(Teams, venue_name, city_name, country_name)``; venue/city/country
            may be ``None`` when the team has no venue or country.
        """
        stmt = self._with_location_stmt().where(Countries.name.in_(country_names))
        result = await self.session.execute(stmt)
        return result.all()

    async def get_many_by_city_name(self, city_names: List[str]) -> Sequence[Row]:
        """Fetch teams with venue/city/country by a list of city names.

        Args:
            city_names: City names to filter by (e.g. ``['Manchester', 'Liverpool']``).

        Returns:
            Rows of ``(Teams, venue_name, city_name, country_name)``.
        """
        stmt = self._with_location_stmt().where(Venues.city.in_(city_names))
        result = await self.session.execute(stmt)
        return result.all()