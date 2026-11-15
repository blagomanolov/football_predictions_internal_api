"""Data-access layer for the ``Seasons`` ORM model"""

from __future__ import annotations

from typing import List, Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from models.seasons import Seasons
from models.competitions import Competitions
from models.countries import Countries
from repositories.base import BaseRepository

class SeasonsRepository(BaseRepository[Seasons]):
    """Repository specializing ``BaseRepository`` for seasons."""

    def __init__(self, session: AsyncSession) -> None:
        """Create a seasons repository bound to ``session``.

        Args:
            session: Request-scoped async SQLAlchemy session.
        """
        super().__init__(Seasons, session, "id")

    async def get_many_by_country_name(
        self, country_names: List[str]
    ) -> Sequence[tuple[Seasons, str, str]]:
        """Fetch seasons joined with country names by country name list.

        Args:
            country_names: List of country names to filter by (e.g. ``['Anfield', 'Germany']``).

        Returns:
            A sequence of database row tuples containing ``(Seasons, competition_name, country_name)``.
        """

        stmt = (
            select(Seasons, Competitions.name.label("competition_name"), Countries.name.label("country_name"))
            .join(Competitions, Competitions.id == Seasons.competition_id)
            .join(Countries, Countries.id == Competitions.country_id)
            .where(Countries.name.in_(country_names))
        )
        result = await self.session.execute(stmt)
        return result.all()