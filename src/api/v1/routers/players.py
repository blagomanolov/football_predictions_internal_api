"""HTTP routes for players reference data."""

from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, Query, Body, Request
from sqlalchemy.ext.asyncio import AsyncSession

from middleware.rate_limit import limiter
from core.auth import require_permissions
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
        description="Create player record.",
        dependencies=[Depends(require_permissions(['data:write']))]
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

@router.get("/", response_model=PageResponse[PlayersRead], dependencies=[Depends(require_permissions(['data:read']))])
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
    description="Retrieve player records matching first_name (exact match).",
    dependencies=[Depends(require_permissions(['data:read']))]
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

@router.get(
    "/by-last-name",
    response_model=List[PlayersRead],
    summary="Get player by last name.",
    description="Retrieve player records matching last_name (exact match).",
    dependencies=[Depends(require_permissions(['data:read']))]
)
@limiter.limit("10/minute")
async def get_many_by_last_name(
    request: Request,
    last_names: List[str] = Query(
        default=["Saka"],
        description="One or more last_name (e.g. 'Saka', 'Rice')"
    ),
    service: PlayersService = Depends(get_service)
) -> List[PlayersRead]:
    """Fetch player by last_name.
    
    Args:
        last_names: last_name values.
        service: Injected player service
    Returns:
        Matching player DTOs.
    """
    return await service.get_many_by_field(last_names, "last_name")

@router.get(
    "/by-preferred-foot",
    response_model=List[PlayersRead],
    summary="Get player by preferred_foot.",
    description="Retrieve player records matching preferred_foot (exact match).",
    dependencies=[Depends(require_permissions(['data:read']))]
)
@limiter.limit("10/minute")
async def get_many_by_preferred_foot(
    request: Request,
    preferred_foots: List[str] = Query(
        default=["right"],
        description="One or more preferred_foot (e.g. 'right', 'left')"
    ),
    service: PlayersService = Depends(get_service)
) -> List[PlayersRead]:
    """Fetch player by preferred_foot.
    
    Args:
        preferred_foots: preferred_foot values.
        service: Injected player service
    Returns:
        Matching player DTOs.
    """
    return await service.get_many_by_field(preferred_foots, "preferred_foot")

@router.get(
    "/by-primary-position",
    response_model=List[PlayersRead],
    summary="Get player by primary_position.",
    description="Retrieve player records matching primary_position (exact match).",
    dependencies=[Depends(require_permissions(['data:read']))]
)
@limiter.limit("10/minute")
async def get_many_by_primary_position(
    request: Request,
    primary_positions: List[str] = Query(
        default=["GK"],
        description="One or more preferred_foot (e.g. 'GK', 'FW')"
    ),
    service: PlayersService = Depends(get_service)
) -> List[PlayersRead]:
    """Fetch player by primary_position.
    
    Args:
        primary_positions: primary_position values.
        service: Injected player service
    Returns:
        Matching player DTOs.
    """
    return await service.get_many_by_field(primary_positions, "primary_position")

@router.get(
    "/by-detailed-position",
    response_model=List[PlayersRead],
    summary="Get player by detailed_position.",
    description="Retrieve player records matching detailed_position (exact match).",
    dependencies=[Depends(require_permissions(['data:read']))]
)
@limiter.limit("10/minute")
async def get_many_by_detailed_position(
    request: Request,
    detailed_positions: List[str] = Query(
        default=["CB"],
        description="One or more detailed_position (e.g. 'CB', 'ST')"
    ),
    service: PlayersService = Depends(get_service)
) -> List[PlayersRead]:
    """Fetch player by detailed_position.
    
    Args:
        detailed_positions: detailed_position values.
        service: Injected player service
    Returns:
        Matching player DTOs.
    """
    return await service.get_many_by_field(detailed_positions, "detailed_position")


@router.get(
    "/by-market-value",
    response_model=PageResponse[PlayersRead],
    summary="List players within a market-value range.",
    description = (
        "Filter by inclusive market-value bounds in euros. "
        "Provide at least one of market_value_min_eur or market_value_max_eur."
    ),
    dependencies = [Depends(require_permissions(['data:read']))]
)
@limiter.limit("10/minute")
async def list_by_market_value(
    request: Request,
    market_value_min_eur: int | None = Query(
        default=None,
        ge=0,
        le=2_147_483_647,
        description='Inclusive minimum value in euros.'
    ),
    market_value_max_eur: int | None = Query(
        default=None,
        ge=0,
        le=2_147_483_647,
        description="Inclusive maximum value in euros."
    ),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1_000),
    service: PlayersService = Depends(get_service),
) -> PageResponse[PlayersRead]:
    return await service.list_by_market_value_range(
        min_eur=market_value_min_eur, max_eur=market_value_max_eur, skip=skip, limit=limit
    )

@router.get(
    '/by-country',
    response_model=List[PlayersReadWithCountry],
    summary="Get players by country names",
    description="Retrieve player records associated with specified country name, including the country name.",
    dependencies = [Depends(require_permissions(['data:read']))]
)
@limiter.limit('10/minute')
async def get_many_by_country(
    request: Request,
    countries: List[str] = Query(
        default=["England"],
        description="One or more countries (e.g. 'England', 'Germany')"
    ),
    service: PlayersService = Depends(get_service)
) -> List[PlayersReadWithCountry]:
    """Fetch players associated with specified country names.

    Args:
        countries: One or more country names to filter by.
        service: Injected player service.

    Returns:
        List of players DTOs enriched with their associated country name.
    """
    return await service.get_many_by_countries(countries)

@router.get(
    "/bulk",
    response_model=List[PlayersRead],
    summary="Get players by ids.",
    description="Retrieve player records atching ids.",
    dependencies=[Depends(require_permissions(['data:read']))]
)
@limiter.limit('10/minute')
async def get_many(
    request: Request,
    ids: List[int] = Query(description="One or more players ids."),
    service: PlayersService = Depends(get_service)
) -> List[PlayersRead]:
    """Fetch multiple players by primary key.
    
    Args:
        ids: Player ids.
        service: Injected players service.
    Returns:
        Matching pplayer DTOs.
    """
    return await service.get_many(ids)

@router.get(
    "/{player_id}",
    response_model=PlayersRead,
    summary="Get player by id.",
    description="Retrieve player record matching id.",
    dependencies=[Depends(require_permissions(['data:read']))]
)
@limiter.limit('10/minute')
async def get_one(
    request: Request,
    player_id: int,
    service: PlayersService = Depends(get_service)
) -> PlayersRead:
    """
    Fetch a single player by id.

    Args:
        player_id: Player prumary key.
        service: Injected players service.
    Returns:
        Player DTO.
    """
    return await service.get(player_id)

@router.post(
    "/search",
    response_model=PageResponse[PlayersRead],
    summary="Retrieve players using dynamic filters.",
    description = (
        "Retrieve a paginated list of players matching dynamic defined"
        "filter critria across multiple model fields. Support multiple"
        "comperison operations, configurable sorting (asc or desc)"
        "and pagination using skip and limit parameters."
    ),
    dependencies=[Depends(require_permissions(['data:read']))]
)
@limiter.limit('10/minute')
async def search(
    request: Request,
    filters: List[FilterItem] = Body(...),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, limit=1_000),
    order_by: Optional[str] = Query(None),
    desc: bool = Query(False),
    service: PlayersService = Depends(get_service)
) -> PageResponse[PlayersRead]:
    """Execute dynamic multi-criteria filter queries over players.
    Args:
        filters: Body payload containing list of filter specifications.
        skip: Offset for pagination.
        limit: Max items to return.
        order_by: Column to sort on.
        desc: Sort descending if True.
        service: Injected players service.
    Returns:
        List of matching player DTOs.
    """
    return await service.get_many_by_filters(filters, skip, limit, order_by, desc)

@router.patch(
    "/{player_id}",
    response_model=PlayersRead,
    summary="Update Player by ID.",
    description=(
        "Update an existing player identified by its unique ID. "
        "Accepts the fields to be updated and applies the changes to the "
        "corresponding player records."
    ),
    dependencies=[Depends(require_permissions(['data:write']))]
)
async def update(
    player_id: int,
    data: PlayersUpdate,
    service: PlayersService = Depends(get_service),
):
    """Apply partial updates to a player record.

    Args:
        player_id: player primary key.
        data: Partial update payload.
        service:Injected player service.
    Returns:
        The updated player DTO.
    """
    return await service.update(player_id, data)

@router.delete(
    "/{player_id}",
    status_code=200,
    response_model=DeleteConfirmation,
    summary="Delete player by ID",
    description = (
        "Delete an existing player identified by its unique ID. "
        "Permanently removes the player record from the database."
    ),
    dependencies=[Depends(require_permissions(['data:write']))]
)
async def delete(
    player_id: int,
    service: PlayersService = Depends(get_service)
) -> DeleteConfirmation:
    """Permanently delete a player record by ID.
    Args:
        player_id: Player primary key.
        service: Injected player service.
    """
    return await service.delete(player_id)