"""Data-access layer for the ``Countries`` ORM model."""

from __future__ import annotations

from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from models.countries import Countries
from repositories.base import BaseRepository


class CountriesRepository(BaseRepository[Countries]):
    """Repository specializing ``BaseRepository`` for countries."""

    def __init__(self, session: AsyncSession) -> None:
        """Create a countries repository bound to ``session``.

        Args:
            session: Request-scoped async SQLAlchemy session.
        """
        super().__init__(Countries, session, "id")

    async def get_by_name(self, name: str) -> Optional[Countries]:
        stmt = select(Countries).where(Countries.name == name)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
