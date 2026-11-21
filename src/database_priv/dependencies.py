"""FastAPI dependencies for privilege database access."""

from __future__ import annotations

from typing import AsyncGenerator

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession


async def get_privilege_session(request: Request) -> AsyncGenerator[AsyncSession, None]:
    """Provide a request-scoped async DB session from ``app.state.privilege_db``.

    Args:
        request: Current FastAPI request (used to reach ``app.state``).

    Yields:
        An ``AsyncSession`` managed by ``PrivilegeDatabase.get_session``.
    """
    privilege_db = request.app.state.privilege_db

    async for session in privilege_db.get_session():
        yield session
