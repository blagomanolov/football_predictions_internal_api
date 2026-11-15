"""Data-acess layer fir tge ``Players`` ORM model"""

from __future__ import annotations

from typing import List, Sequence

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from models.players import Players
from models.countries import Countries
from repositories.base import BaseRepository

class PlayersRepository(BaseRepository[Players]):
    """Repository specializing ``BaseRepository`` for players."""

    def __init__(self, session: AsyncSession) -> None:
        """Create a players repository bound to ``session``.
        
        Args:
            session: Request-scoped async SQLAlchemy session."""
        super().__init__(Players, session, 'id')

    async def get_many_by_country_name(
            self, country_names: List[str],
    ) -> Sequence[tuple[Players, str]]:
        """Fetch players joined with country names by country name list.

        Args:
            country_names: List of country names to filter by (e.g. ``['England', 'Germany']``).

        Returns:
            A sequence of database row tuples containing ``(Players, country_name)``.
        """
        stmt = (
            select(Players, Countries.name.label("country_name"))
            .join(Countries, Countries.id == Players.nationality_country_id)
            .where(Countries.name.in_(country_names))
        )
        result = await self.session.execute(stmt)
        return result.all