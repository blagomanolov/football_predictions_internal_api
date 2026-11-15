"""Data-access layer for the ``Competitions`` ORM model"""

from __future__ import annotations

from typing import List, Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from models.competitions import Competitions
from models.countries import Countries
from repositories.base import BaseRepository

class CompetitionsRepository(BaseRepository[Competitions]):
    """Repository specializing ``BaseRepository`` for competitions."""

    def __init__(self, session: AsyncSession) -> None:
        """Create a competitions repository bound to ``session``.

        Args:
            session: Request-scoped async SQLAlchemy session.
        """
        super().__init__(Competitions, session, "id")

    async def get_many_by_country_name(
        self, country_names: List[str]
    ) -> Sequence[tuple[Competitions, str]]:
        """Fetch competitions joined with country names by country name list.

        Args:
            country_names: List of country names to filter by (e.g. ``['England', 'Germany']``).

        Returns:
            A sequence of database row tuples containing ``(Competitions, country_name)``.
        """
        stmt = (
            select(Competitions, Countries.name.label("country_name"))
            .join(Countries, Countries.id == Competitions.country_id)
            .where(Countries.name.in_(country_names))
        )
        result = await self.session.execute(stmt)
        return result.all()