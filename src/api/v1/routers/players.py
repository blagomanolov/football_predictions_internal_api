"""HTTP routes for players reference data."""

from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession

from database.dependencies import get_db_session
from repositories.players import PlayersRepository
from schemas.players import (
    PlayersRead,
    PlayersCreate,
    PlayersUpdate,
    PlayersReadWithCountry
)
from services.players import PlayersService
from schemas.filters import FilterItem
from schemas.base import DeleteConfirmation, PageResponse

router = APIRouter(prefix="/players", tags=["Players"])


def get_service(
    session: AsyncSession = Depends(get_db_session),
) -> PlayersService:
    """Build a ``PlayersService`` for the current request.

    Args:
        session: Injected async DB session.

    Returns:
        Service wired to a ``PlayersRepository``.
    """
    repo: PlayersRepository = PlayersRepository(session)
    return PlayersService(repo)

@router.post(
        "/", 
        response_model=PlayersRead,
        summary="Create player record.",
        description="Create player record."
)
async def create(
    data: PlayersCreate, 
    service: PlayersService = Depends(get_service),
):
    """Create a new player reference record.
    Args:
        data: Inbound player payload.
        service: Injected player service.
    Returns:
        The newly created player DTO.
    """
    return await service.create(data)