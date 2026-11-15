"""FastAPI dependencies for database access."""

from __future__ import annotations

from typing import AsyncGenerator

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession


async def get_db_session(request: Request) -> AsyncGenerator[AsyncSession, None]:
    """Provide a request-scoped async DB session from ``app.state.database``.

    Args:
        request: Current FastAPI request (used to reach ``app.state``).

    Yields:
        An ``AsyncSession`` managed by ``Database.get_session``.
    """
    database = request.app.state.database

    async for session in database.get_session():
        yield session
