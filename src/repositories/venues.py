"""Data-access layer for the ``Venues`` ORM model"""

from __future__ import annotations

from typing import List, Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from models.venues import Venues
from models.countries import Countries
from repositories.base import BaseRepository

class VenuesRepository(BaseRepository[Venues]):
    """Repository specializing ``BaseRepository`` for venues."""

    def __init__(self, session: AsyncSession) -> None:
        """Create a venues repository bound to ``session``.

        Args:
            session: Request-scoped async SQLAlchemy session.
        """
        super().__init__(Venues, session, "id")

    async def get_many_by_country_name(
        self, country_names: List[str]
    ) -> Sequence[tuple[Venues, str]]:
        """Fetch venues joined with country names by country name list.

        Args:
            country_names: List of country names to filter by (e.g. ``['England', 'Germany']``).

        Returns:
            A sequence of database row tuples containing ``(Venues, country_name)``.
        """
        stmt = (
            select(Venues, Countries.name.label("country_name"))
            .join(Countries, Countries.id == Venues.country_id)
            .where(Countries.name.in_(country_names))
        )
        result = await self.session.execute(stmt)
        return result.all()