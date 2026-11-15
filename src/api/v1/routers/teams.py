"""HTTP routes for teams reference data."""

from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, Query, Body, Request
from sqlalchemy.ext.asyncio import AsyncSession

from middleware.rate_limit import limiter
from database.dependencies import get_db_session
from repositories.teams import TeamsRepository
from schemas.teams import (
    TeamsRead,
    TeamsCreate,
    TeamsUpdate,
    TeamsReadWithCountryAndCityAndVenue,
)
from services.teams import TeamsService
from schemas.filters import FilterItem
from schemas.base import DeleteConfirmation, PageResponse

router = APIRouter(prefix="/teams", tags=["Teams"])

def get_service(
    session: AsyncSession = Depends(get_db_session),
) -> TeamsService:
    """Build a ``TeamsService`` for the current request.

    Args:
        session: Injected async DB session.

    Returns:
        Service wired to a ``TeamsRepository``.
    """
    repo: TeamsRepository = TeamsRepository(session)
    return TeamsService(repo)

@router.post(
    "/",
    response_model=TeamsRead,
    summary="Create team record.",
    description="Create team record."
)
@limiter.limit("10/minute")
async def create(
    request: Request,
    data: TeamsCreate,
    service: TeamsService = Depends(get_service)
):
    """Create a new team reference record.
    Args:
        data: Inbound team payload.
        service: Injected team service.
    Returns:
        The newly created team DTO.
    """
    return await service.create(data)

@router.get("/", response_model=PageResponse[TeamsRead])
@limiter.limit("10/minute")
async def list_all(
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1_000),
    service: TeamsService = Depends(get_service),
) -> PageResponse[TeamsRead]:
    """List teams with offset pagination.
    
    Args:
        skip: Number of records to skip,
        limit: Maximum records to return
        service: Injected teams service.
    Returns:
        Paginated envelope of teams DTOs.
    """
    return await service.list(skip, limit)

@router.get(
    "/by-name",
    response_model=List[TeamsRead],
    summary="Get team by name.",
    description="Retrieve teams records matching name (exact match).",
)
@limiter.limit("10/minute")
async def get_many_by_name(
    request: Request,
    names: List[str] = Query(
        default=["Liverpool FC"],
        description="One or more name (e.g. 'Liverpool FC', 'Arsenal FC')",
    ),
    service: TeamsService = Depends(get_service)
) -> List[TeamsRead]:
    """Fetch team by name.
    
    Args:
        name: Name values.
        service: Injected teams service.
    
    Returns:
        Matching team DTOs."""
    return await service.get_many_by_field(names, "name")

@router.get(
    "/by-short-name",
    response_model=List[TeamsRead],
    summary="Get team by short name.",
    description="Retrieve teams records matching short name (exact match).",
)
@limiter.limit("10/minute")
async def get_many_by_short_name(
    request: Request,
    short_names: List[str] = Query(
        default=["Liverpool"],
        description="One or more short name (e.g. 'Liverpool', 'Arsenal')",
    ),
    service: TeamsService = Depends(get_service)
) -> List[TeamsRead]:
    """Fetch team by short name.
    
    Args:
        short_names: Short name values.
        service: Injected teams service.
    
    Returns:
        Matching team DTOs."""
    return await service.get_many_by_field(short_names, "short_name")


@router.get(
    "/by-country",
    response_model=List[TeamsReadWithCountryAndCityAndVenue],
    summary="Get teams by country names.",
    description=(
        "Retrieve teams records associated with specified country names, including the country name, "
        "city name, and venue."
    )
)
@limiter.limit("10/minute")
async def get_many_by_country(
    request: Request,
    countries: List[str] = Query(
        default=["England"],
        description="One or more countries (e.g. 'England', 'Germany')"
    ),
    service: TeamsService = Depends(get_service)
) -> List[TeamsReadWithCountryAndCityAndVenue]:
    """Fetch teams associated with specified country names.
    
    Args:
        countries: One or more country names to filter by.
        service: Injected teams service.

    Returns:
        List of teams DTOs enriched with their associated country name.
    """
    return await service.get_many_by_countries(countries)

@router.get(
    "/by-city",
    response_model=List[TeamsReadWithCountryAndCityAndVenue],
    summary="Get teams by city names.",
    description=(
        "Retrieve teams records associated with specified city names, including the country name, "
        "city name, and venue."
    )
)
@limiter.limit("10/minute")
async def get_many_by_city(
    request: Request,
    cities: List[str] = Query(
        default=["Manchester"],
        description="One or more cities (e.g. 'Manchester', 'Liverpool')"
    ),
    service: TeamsService = Depends(get_service)
) -> List[TeamsReadWithCountryAndCityAndVenue]:
    """Fetch teams associated with specified city names.
    
    Args:
        cities: One or more city names to filter by.
        service: Injected teams service.

    Returns:
        List of teams DTOs enriched with their associated city name.
    """
    return await service.get_many_by_cities(cities)

@router.get(
    "/bulk",
    response_model=List[TeamsRead],
    summary="Get teams by ids.",
    description="Retrieve teams records matching ids."
)
@limiter.limit("10/minute")
async def get_many(
    request: Request,
    ids: List[int] = Query(description="One or more team ids."),
    service: TeamsService = Depends(get_service),
) -> List[TeamsRead]:
    """Fetch multiple teams by primary key.
    
    Args:
        ids: Teams ids.
        service: Injected season service.
    Returns:
        Matching teams DTOs.
    """
    return await service.get_many(ids)


@router.get(
    "/{season_id}",
    response_model=TeamsRead,
    summary="Get team by id.",
    description="Retrieve team record matching id.",
)
@limiter.limit("10/minute")
async def get_one(
    request: Request,
    team_id: int,
    service: TeamsService = Depends(get_service),
) -> TeamsRead:
    """Fetch a single team by id.

    Args:
        team_id: Team primary key.
        service: Injected teams service.
    
    Returns:
        Team DTO.
    """
    return await service.get(team_id)

@router.post(
        "/search",
        response_model=PageResponse[TeamsRead],
        summary="Retrieve teams using dynamic filters.",
        description=(
            "Retrieve a paginated list of teams matching dynamic defined"
            "filter critria across multiple model fields. Support multiple"
            "comperison operations, configurable sorting (asc or desc)"
            "and pagination using skip and limit parameters."
        )
)
@limiter.limit("10/minute")
async def search(
    request: Request,
    filters: List[FilterItem] = Body(...),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1_000),
    order_by: Optional[str] = Query(None),
    desc: bool = Query(False),
    service: TeamsService = Depends(get_service),
) -> PageResponse[TeamsRead]:
    """Execute dynamic multi-criteria filter queries over teams.
    Args:
        filters: Body payload containing list of filter specifications.
        skip: Offset for pagination.
        limit: Max items to return.
        order_by: Column to sort on.
        desc: Sort descending if True.
        service: Injected teams service.
    Returns:
        List of matching team DTOs.
    """
    return await service.get_many_by_filters(filters, skip, limit, order_by, desc)


@router.patch(
    "/{team_id}",
    response_model=TeamsRead,
    summary="Update Team by ID.",
    description = (
        "Update an existing team identified by its unique ID. "
        "Accepts the fields to be updated and applies the changes to the "
        "corresponding team records."
    )
)
@limiter.limit("10/minute")
async def update(
    request: Request,
    team_id: int,
    data: TeamsUpdate,
    service: TeamsService = Depends(get_service)
):
    """Apply partial updates to a team record.

    Args:
        team_id: Team primary key.
        data: Partial update payload.
        service:Injected team service.
    Returns:
        The updated team DTO.
    """
    return await service.update(team_id, data)

@router.delete(
    "/{team_id}",
    status_code=200,
    response_model=DeleteConfirmation,
    summary="Delete team by ID",
    description = (
            "Delete an existing team identified by its unique ID. "
            "Permanently removes the team record from the database."
    )
)
@limiter.limit("10/minute")
async def delete(
    request: Request,
    team_id: int,
    service: TeamsService = Depends(get_service),
) -> DeleteConfirmation:
    """Permanently delete a team record by ID.
    Args:
        team_id: Team primary key.
        service: Injected team service.
    """
    return await service.delete(team_id)