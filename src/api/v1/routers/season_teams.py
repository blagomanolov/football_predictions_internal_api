"""HTTP routes for season_teams reference data."""

from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, Query, Body, Request
from sqlalchemy.ext.asyncio import AsyncSession

from middleware.rate_limit import limiter
from core.auth import require_permissions
from database.dependencies import get_db_session
from repositories.season_teams import SeasonTeamsRepository
from schemas.season_teams import (
    SeasonTeamsRead,
    SeasonTeamsCreate,
    SeasonTeamsUpdate,
    SeasonTeamsWithSeasonAndTeam,
)
from services.season_teams import SeasonTeamsService
from schemas.filters import FilterItem
from schemas.base import DeleteConfirmation, PageResponse

router = APIRouter(prefix="/season-teams", tags=["SeasonTeams"])

def get_service(
    session: AsyncSession = Depends(get_db_session),
) -> SeasonTeamsService:
    """Build a ``SeasonTeamsService`` for the current request.

    Args:
        session: Injected async DB session.

    Returns:
        Service wired to a ``SeasonTeamsRepository``.
    """
    repo: SeasonTeamsRepository = SeasonTeamsRepository(session)
    return SeasonTeamsService(repo)

@router.post(
    "/",
    response_model=SeasonTeamsRead,
    summary="Create season_team record.",
    description="Create season_team record.",
    dependencies=[Depends(require_permissions(['data:write']))]
)
@limiter.limit("10/minute")
async def create(
    request: Request,
    data: SeasonTeamsCreate,
    service: SeasonTeamsService = Depends(get_service),
):
    """
    Create a new season_teams reference record.
    Args:
        data: Inbound team payload.
        service: Injected season_teams service.
    Returns:
        The newly created season_teams DTO.
    """
    return await service.create(data)

@router.get("/", response_model=PageResponse[SeasonTeamsRead], dependencies=[Depends(require_permissions(['data:read']))])
@limiter.limit("10/minute")
async def list_all(
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1_000),
    service: SeasonTeamsService = Depends(get_service)
) -> PageResponse[SeasonTeamsRead]:
    """List season_teams with offset pagination.
    
    Args:
        skip: Number of records to skip,
        limit: Maximum records to return
        service: Injected season_teams service.
    Returns:
        Paginated envelope of season_teams DTOs.
    """
    return await service.list(skip, limit)

@router.get(
    "/by-country",
    response_model=List[SeasonTeamsWithSeasonAndTeam],
    summary="Get season_teams by country names.",
    description=(
        "Retrieve season_teams records associated with specified country names, including the season name, "
        "team name."
    ),
    dependencies=[Depends(require_permissions(["data:read"]))]
)
@limiter.limit("10/minute")
async def get_many_by_country(
    request: Request,
    countries: List[str] = Query(
        default=["England"],
        description="One or more countries (e.g. 'England', 'Germany')"
    ),
    service: SeasonTeamsService = Depends(get_service)
) -> List[SeasonTeamsWithSeasonAndTeam]:
    """Fetch season_teams associated with specified country names.
    
    Args:
        countrie: One or more country names to filter by.
        service: Injected season_teams service.

    Returns:
        List of season_teams DTOs enriched with their associated with country names.
    """
    return await service.get_many_by_countries(countries)

@router.get(
    "/bulk",
    response_model=List[SeasonTeamsRead],
    summary="Get season_teams by ids.",
    description="Retrieve season_teams records matching ids.",
    dependencies=[Depends(require_permissions(["data:read"]))]
)
@limiter.limit("10/minute")
async def get_many(
    request: Request,
    ids: List[int] = Query(description="One or more season_team ids."),
    service: SeasonTeamsService = Depends(get_service),
) -> List[SeasonTeamsRead]:
    """Fetch multiple season_teams by primary key.
    
    Args:
        ids: Season teams ids.
        service: Injected season service.
    Returns:
        Matching season_teams DTOs.
    """
    return await service.get_many(ids)

@router.get(
    "/{season_team_id}",
    response_model=SeasonTeamsRead,
    summary="Get season_team by id.",
    description="Retrieve season_team record matching id.",
    dependencies=[Depends(require_permissions(["data:read"]))]
)
@limiter.limit("10/minute")
async def get_one(
    request: Request,
    season_team_id: int,
    service: SeasonTeamsService = Depends(get_service),
) -> SeasonTeamsRead:
    """Fetch a single season_team by id.

    Args:
        season_team_id: Season team primary key.
        service: Injected season_teams service.
    
    Returns:
        Season team DTO.
    """
    return await service.get(season_team_id)

@router.post(
        "/search",
        response_model=PageResponse[SeasonTeamsRead],
        summary="Retrieve season_teams using dynamic filters.",
        description=(
            "Retrieve a paginated list of season_teams matching dynamic defined"
            "filter critria across multiple model fields. Support multiple"
            "comperison operations, configurable sorting (asc or desc)"
            "and pagination using skip and limit parameters."
        ),
        dependencies=[Depends(require_permissions(["data:read"]))]
)
@limiter.limit("10/minute")
async def search(
    request: Request,
    filters: List[FilterItem] = Body(...),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1_000),
    order_by: Optional[str] = Query(None),
    desc: bool = Query(False),
    service: SeasonTeamsService = Depends(get_service),
) -> PageResponse[SeasonTeamsRead]:
    """Execute dynamic multi-criteria filter queries over season_teams.
    Args:
        filters: Body payload containing list of filter specifications.
        skip: Offset for pagination.
        limit: Max items to return.
        order_by: Column to sort on.
        desc: Sort descending if True.
        service: Injected season_teams service.
    Returns:
        List of matching season_team DTOs.
    """
    return await service.get_many_by_filters(filters, skip, limit, order_by, desc)

@router.patch(
    "/{season_team_id}",
    response_model=SeasonTeamsRead,
    summary="Update Season team by ID.",
    description = (
        "Update an existing season_team identified by its unique ID. "
        "Accepts the fields to be updated and applies the changes to the "
        "corresponding season_team records."
    ),
    dependencies=[Depends(require_permissions(["data:write"]))]
)
@limiter.limit("10/minute")
async def update(
    request: Request,
    season_team_id: int,
    data: SeasonTeamsUpdate,
    service: SeasonTeamsService = Depends(get_service)
):
    """Apply partial updates to a season_team record.

    Args:
        season_team_id: Season team primary key.
        data: Partial update payload.
        service:Injected season_team service.
    Returns:
        The updated season_team DTO.
    """
    return await service.update(season_team_id, data)

@router.delete(
    "/{season_team_id}",
    status_code=200,
    response_model=DeleteConfirmation,
    summary="Delete season_team by ID",
    description = (
            "Delete an existing season_team identified by its unique ID. "
            "Permanently removes the season_team record from the database."
    ),
    dependencies=[Depends(require_permissions(["data:write"]))]
)
@limiter.limit("10/minute")
async def delete(
    request: Request,
    season_team_id: int,
    service: SeasonTeamsService = Depends(get_service),
) -> DeleteConfirmation:
    """Permanently delete a season_team record by ID.
    Args:
        season_team_id: Season team primary key.
        service: Injected season_team service.
    """
    return await service.delete(season_team_id)