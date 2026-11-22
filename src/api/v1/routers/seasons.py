"""HTTP routes for seasons reference data."""

from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, Query, Body, Request
from sqlalchemy.ext.asyncio import AsyncSession

from middleware.rate_limit import limiter
from core.auth import require_permissions
from database.dependencies import get_db_session
from repositories.seasons import SeasonsRepository
from schemas.seasons import (
    SeasonsRead,
    SeasonsCreate,
    SeasonsUpdate,
    SeasonsReadWithCompetitions,
    SeasonsReadWithCountryAndCompetitions
)
from services.seasons import SeasonsService
from schemas.filters import FilterItem
from schemas.base import DeleteConfirmation, PageResponse

router = APIRouter(prefix="/seasons", tags=["Seasons"])

def get_service(
    session: AsyncSession = Depends(get_db_session),
) -> SeasonsService:
    """Build a ``SeasonService`` for the current request.

    Args:
        session: Injected async DB session.

    Returns:
        Service wired to a ``SeasonsRepository``.
    """
    repo: SeasonsRepository = SeasonsRepository(session)
    return SeasonsService(repo)

@router.post(
    "/",
    response_model=SeasonsRead,
    summary="Create season record.",
    description="Create season record.",
    dependencies=[Depends(require_permissions(['data:write']))]
)
async def create(
    data: SeasonsCreate,
    service: SeasonsService = Depends(get_service),
):
    """Create a new season reference record.
    Args:
        data: Inbound season payload.
        service: Injected season service.
    Returns:
        The newly created season DTO.
    """
    return await service.create(data)

@router.get(
    "/", 
    response_model=PageResponse[SeasonsRead], 
    dependencies=[Depends(require_permissions(['data:read']))]
)
@limiter.limit('10/minute')
async def list_all(
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1_000),
    service: SeasonsService = Depends(get_service),
) -> PageResponse[SeasonsRead]:
    """List seasons with offset pagination.

    Args:
        skip: Number of records to skip.
        limit: Maximum records to return.
        service: Injected season service.

    Returns:
        Paginated envelope of season DTOs.
    """
    return await service.list(skip, limit)

@router.get(
    "/by-name",
    response_model=List[SeasonsRead],
    summary="Get season by name.",
    description="Retrieve seasons records matching name (exact match).",
    dependencies=[Depends(require_permissions(['data:read']))]
)
@limiter.limit('10/minute')
async def get_many_by_name(
    request: Request,
    names: List[str] = Query(
        default=["2025/2026"],
        description="One or more name (e.g. '2025/2026', '2024/2025')",
    ),
    service: SeasonsService = Depends(get_service),
) -> List[SeasonsRead]:
    """Fetch season by name.

    Args:
        name: Name values.
        service: Injected seasons service.

    Returns:
        Matching season DTOs.
    """
    return await service.get_many_by_field(names, "name")

@router.get(
    "/by-current",
    response_model=List[SeasonsRead],
    summary="Get season by is_current.",
    description="Retrieve season records matching is_current (exact match).",
    dependencies=[Depends(require_permissions(['data:read']))]
)
@limiter.limit('10/minute')
async def get_many_by_current(
    request: Request,
    is_current: List[bool] = Query(
        default=[True],
        description="One or more is_current (e.g. 'True', 'False')",
    ),
    service: SeasonsService = Depends(get_service),
) -> List[SeasonsRead]:
    """Fetch season by is_current.

    Args:
        is_current: bool values.
        service: Injected season service.

    Returns:
        Matching seasons DTOs.
    """
    return await service.get_many_by_field(is_current, "is_current")

@router.get(
    "/by-country",
    response_model=List[SeasonsReadWithCountryAndCompetitions],
    summary="Get seasons by country names.",
    description="Retrieve seasons records associated with specified country names, including the country name.",
    dependencies=[Depends(require_permissions(['data:read']))]
)
@limiter.limit('10/minute')
async def get_many_by_country(
    request: Request,
    countries: List[str] = Query(
        default=["England"],
        description="One or more countries (e.g. 'England', 'Germany')"
    ),
    service: SeasonsService = Depends(get_service)
) -> List[SeasonsReadWithCountryAndCompetitions]:
    """Fetch seasons associated with specified country names.

    Args:
        countries: One or more country names to filter by.
        service: Injected seasons service.

    Returns:
        List of seasons DTOs enriched with their associated country name.
    """
    return await service.get_many_by_countries(countries)

@router.get(
    "/bulk",
    response_model=List[SeasonsRead],
    summary="Get seasons by ids.",
    description="Retrieve seasons records matching ids.",
    dependencies=[Depends(require_permissions(['data:read']))]
)
@limiter.limit('10/minute')
async def get_many(
    request: Request,
    ids: List[int] = Query(description="One or more seasons ids."),
    service: SeasonsService = Depends(get_service),
) -> List[SeasonsRead]:
    """Fetch multiple seasons by primary key.
    
    Args:
        ids: Seasons ids.
        service: Injected season service.    
    Returns:
        Matching seasons DTOs.
    """
    return await service.get_many(ids)

@router.get(
    "/{season_id}",
    response_model=SeasonsRead,
    summary="Get season by id.",
    description="Retrieve season record matching id.",
    dependencies=[Depends(require_permissions(['data:read']))]
)
@limiter.limit('10/minute')
async def get_one(
    request: Request,
    season_id: int,
    service: SeasonsService = Depends(get_service),
) -> SeasonsRead:
    """Fetch a single season by id.

    Args:
        season_id: Season primary key.
        service: Injected seasons service.
    
    Returns:
        Season DTO.
    """
    return await service.get(season_id)

@router.post(
        "/search",
        response_model=PageResponse[SeasonsRead],
        summary="Retrieve seasons using dynamic filters.",
        description=(
            "Retrieve a paginated list of competition matching dynamic defined"
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
    limit: int = Query(100, ge=1, le=1_000),
    order_by: Optional[str] = Query(None),
    desc: bool = Query(False),
    service: SeasonsService = Depends(get_service),
) -> PageResponse[SeasonsRead]:
    """Execute dynamic multi-criteria filter queries over seasons.
    Args:
        filters: Body payload containing list of filter specifications.
        skip: Offset for pagination.
        limit: Max items to return.
        order_by: Column to sort on.
        desc: Sort descending if True.
        service: Injected seasons service.
    Returns:
        List of matching season DTOs.
    """
    return await service.get_many_by_filters(filters, skip, limit, order_by, desc)


@router.patch(
    "/{season_id}",
    response_model=SeasonsRead,
    summary="Update Season by ID.",
    description = (
        "Update an existing season identified by its unique ID. "
        "Accepts the fields to be updated and applies the changes to the "
        "corresponding season records."
    ),
    dependencies=[Depends(require_permissions(['data:write']))]
)
async def update(
    season_id: int,
    data: SeasonsUpdate,
    service: SeasonsService = Depends(get_service)
):
    """Apply partial updates to a season record.

    Args:
        season_id: Season primary key.
        data: Partial update payload.
        service:Injected season service.
    Returns:
        The updated season DTO.
    """
    return await service.update(season_id, data)

@router.delete(
    "/{season_id}",
    status_code=200,
    response_model=DeleteConfirmation,
    summary="Delete season by ID",
    description = (
        "Delete an existing season identified by its unique ID. "
        "Permanently removes the season record from the database."
    ),
    dependencies=[Depends(require_permissions(['data:write']))]
)
async def delete(
    season_id: int,
    service: SeasonsService = Depends(get_service),
) -> DeleteConfirmation:
    """Permanently delete a season record by ID.
    Args:
        season_id: Season primary key.
        service: Injected season service.
    """
    return await service.delete(season_id)