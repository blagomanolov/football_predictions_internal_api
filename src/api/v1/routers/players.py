"""HTTP routes for players reference data."""

from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, Query, Body, Request
from sqlalchemy.ext.asyncio import AsyncSession

from middleware.rate_limit import limiter
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

@router.get("/", response_model=PageResponse[PlayersRead])
@limiter.limit("10/minute")
async def list_all(
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1_000),
    service: PlayersService = Depends(get_service)
) -> PageResponse[PlayersRead]:
    """List players with offset pagination.
    
    Args:
        skip: Number of records to skip,
        limit: Maximum records to return
        service: Injected players service.
    Returns:
        Paginated envelope of players DTOs.
    """
    return await service.list(skip, limit)

@router.get(
    "/by-first-name",
    response_model=List[PlayersRead],
    summary="Get player by first name.",
    description="Retrieve player records matching first_name (exact match)."
)
@limiter.limit("10/minute")
async def get_many_by_first_name(
    request: Request,
    first_names: List[str] = Query(
        default=["Bukayo"],
        description="One or more first_name (e.g. 'Bukayo', 'Declan')"
    ),
    service: PlayersService = Depends(get_service)
) -> List[PlayersRead]:
    """Fetch player by first_name.
    
    Args:
        first_name: first_name values.
        service: Injected player service
    Returns:
        Matching player DTOs.
    """
    return await service.get_many_by_field(first_names, "first_name")
