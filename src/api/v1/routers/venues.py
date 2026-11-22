"""HTTP routes for venues reference data."""

from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, Query, Body, Request
from sqlalchemy.ext.asyncio import AsyncSession

from middleware.rate_limit import limiter
from core.auth import require_permissions
from database.dependencies import get_db_session
from repositories.venues import VenuesRepository
from schemas.venues import (
    VenuesRead,
    VenuesCreate,
    VenuesUpdate,
    VenuesReadWithCountry,
)
from services.venues import VenuesService
from schemas.filters import FilterItem
from schemas.base import DeleteConfirmation, PageResponse

router = APIRouter(prefix="/venues", tags=["Venues"])


def get_service(
    session: AsyncSession = Depends(get_db_session),
) -> VenuesService:
    """Build a ``VenuesService`` for the current request.

    Args:
        session: Injected async DB session.

    Returns:
        Service wired to a ``VenuesRepository``.
    """
    repo: VenuesRepository = VenuesRepository(session)
    return VenuesService(repo)


@router.post(
    "/",
    response_model=VenuesRead,
    summary="Create venues record.",
    description="Create a new venues reference record.",
    dependencies=[Depends(require_permissions(['data:write']))]
)
async def create(
    data: VenuesCreate,
    service: VenuesService = Depends(get_service),
) -> VenuesRead:
    """Create a new venue.

    Args:
        data: Inbound venue payload.
        service: Injected venues service.

    Returns:
        The newly created venue DTO.
    """
    return await service.create(data)


@router.get(
    "/",
    response_model=PageResponse[VenuesRead],
    summary="List venues.",
    description="Retrieve a paginated list of venues.",
    dependencies=[Depends(require_permissions(['data:read']))]
)
@limiter.limit("10/minute")
async def list_all(
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1_000),
    service: VenuesService = Depends(get_service),
) -> PageResponse[VenuesRead]:
    """List venues with offset pagination.

    Args:
        skip: Number of records to skip.
        limit: Maximum records to return.
        service: Injected venues service.

    Returns:
        Paginated envelope of venue DTOs.
    """
    return await service.list(skip, limit)


@router.get(
    "/by-name",
    response_model=List[VenuesRead],
    summary="Get venues by name.",
    description="Retrieve venue records matching name (exact match).",
    dependencies=[Depends(require_permissions(['data:read']))]
)
@limiter.limit('10/minute')
async def get_many_by_name(
    request: Request,
    names: List[str] = Query(
        default=["Anfield"],
        description="One or more venue names (e.g. 'Anfield', 'Old Trafford')",
    ),
    service: VenuesService = Depends(get_service),
) -> List[VenuesRead]:
    """Fetch venues by name.

    Args:
        names: Name values.
        service: Injected venues service.

    Returns:
        Matching venue DTOs.
    """
    return await service.get_many_by_field(names, "name")


@router.get(
    "/by-city",
    response_model=List[VenuesRead],
    summary="Get venues by city.",
    description="Retrieve venue records matching city (exact match).",
    dependencies=[Depends(require_permissions(['data:read']))]
)
@limiter.limit("10/minute")
async def get_many_by_city(
    request: Request,
    cities: List[str] = Query(
        default=["London"],
        description="One or more cities (e.g. 'London', 'Manchester')",
    ),
    service: VenuesService = Depends(get_service),
) -> List[VenuesRead]:
    """Fetch venues by city.

    Args:
        cities: City values.
        service: Injected venues service.

    Returns:
        Matching venue DTOs.
    """
    return await service.get_many_by_field(cities, "city")


@router.get(
    "/by-country",
    response_model=List[VenuesReadWithCountry],
    summary="Get venues by country names.",
    description="Retrieve venue records associated with specified country names.",
    dependencies=[Depends(require_permissions(['data:read']))]
)
@limiter.limit('10/minute')
async def get_many_by_country(
    request: Request,
    countries: List[str] = Query(
        default=["England"],
        description="One or more country names (e.g. 'England', 'Spain')",
    ),
    service: VenuesService = Depends(get_service),
) -> List[VenuesReadWithCountry]:
    """Fetch venues associated with specified country names.

    Args:
        countries: One or more country names to filter by.
        service: Injected venues service.

    Returns:
        List of venue DTOs enriched with country name.
    """
    return await service.get_many_by_countries(countries)


@router.get(
    "/bulk",
    response_model=List[VenuesRead],
    summary="Get venues by ids.",
    description="Retrieve venue records matching ids.",
    dependencies=[Depends(require_permissions(['data:read']))]
)
@limiter.limit('10/minute')
async def get_many(
    request: Request,
    ids: List[int] = Query(description="One or more venue ids."),
    service: VenuesService = Depends(get_service),
) -> List[VenuesRead]:
    """Fetch multiple venues by primary key.

    Args:
        ids: Venue primary keys.
        service: Injected venues service.

    Returns:
        Matching venue DTOs.
    """
    return await service.get_many(ids)


@router.get(
    "/{venue_id}",
    response_model=VenuesRead,
    summary="Get venue by id.",
    description="Retrieve venue record matching id.",
    dependencies=[Depends(require_permissions(['data:read']))]
)
@limiter.limit('10/minute')
async def get_one(
    request: Request,
    venue_id: int,
    service: VenuesService = Depends(get_service),
) -> VenuesRead:
    """Fetch a single venue by id.

    Args:
        venue_id: Venue primary key.
        service: Injected venues service.

    Returns:
        Venue DTO.
    """
    return await service.get(venue_id)


@router.post(
    "/search",
    response_model=PageResponse[VenuesRead],
    summary="Retrieve venues using dynamic filters.",
    description="Retrieve a paginated list of venues matching dynamic defined filter criteria.",
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
    service: VenuesService = Depends(get_service),
) -> PageResponse[VenuesRead]:
    """Execute dynamic multi-criteria filter queries over venues.

    Args:
        filters: Body payload containing list of filter specifications.
        skip: Offset for pagination.
        limit: Max items to return.
        order_by: Column to sort on.
        desc: Sort descending if True.
        service: Injected venues service.

    Returns:
        Paginated envelope of matching venue DTOs.
    """
    return await service.get_many_by_filters(filters, skip, limit, order_by, desc)


@router.patch(
    "/{venue_id}",
    response_model=VenuesRead,
    summary="Update venue by ID.",
    description="Apply partial updates to an existing venue record.",
    dependencies=[Depends(require_permissions(['data:write']))]
)
async def update(
    venue_id: int,
    data: VenuesUpdate,
    service: VenuesService = Depends(get_service),
) -> VenuesRead:
    """Apply partial updates to a venue record.

    Args:
        venue_id: Venue primary key.
        data: Partial update payload.
        service: Injected venue service.

    Returns:
        The updated venue DTO.
    """
    return await service.update(venue_id, data)


@router.delete(
    "/{venue_id}",
    status_code=200,
    response_model=DeleteConfirmation,
    summary="Delete venue by ID",
    description="Delete an existing venue identified by its unique ID.",
    dependencies=[Depends(require_permissions(['data:write']))]
)
async def delete(
    venue_id: int,
    service: VenuesService = Depends(get_service),
) -> DeleteConfirmation:
    """Permanently delete a venue record by ID.

    Args:
        venue_id: Venue primary key.
        service: Injected venue service.

    Returns:
        Delete confirmation payload.
    """
    return await service.delete(venue_id)
