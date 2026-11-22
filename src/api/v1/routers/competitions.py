"""HTTP routes for competitions reference data."""

from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, Query, Body, Request
from sqlalchemy.ext.asyncio import AsyncSession

from middleware.rate_limit import limiter
from core.auth import require_permissions
from database.dependencies import get_db_session
from repositories.competitions import CompetitionsRepository
from schemas.competitions import (
    CompetitionsRead,
    CompetitionsCreate,
    CompetitionsUpdate,
    CompetitionsReadWithCountry
)
from services.competitions import CompetitionsService
from schemas.filters import FilterItem
from schemas.base import DeleteConfirmation, PageResponse

router = APIRouter(prefix="/competitions", tags=["Competitions"])


def get_service(
    session: AsyncSession = Depends(get_db_session),
) -> CompetitionsService:
    """Build a ``CompetitionsService`` for the current request.

    Args:
        session: Injected async DB session.

    Returns:
        Service wired to a ``CompetitionsRepository``.
    """
    repo: CompetitionsRepository = CompetitionsRepository(session)
    return CompetitionsService(repo)

@router.post(
        "/", 
        response_model=CompetitionsRead,
        summary="Create competition record.",
        description="Create competition record.",
        dependencies=[Depends(require_permissions(["data:write"]))]
)
async def create(
    data: CompetitionsCreate, 
    service: CompetitionsService = Depends(get_service),
):
    """Create a new competition reference record.
    Args:
        data: Inbound competition payload.
        service: Injected competition service.
    Returns:
        The newly created competition DTO.
    """
    return await service.create(data)

@router.get("/", response_model=PageResponse[CompetitionsRead], dependencies=[Depends(require_permissions(["data:read"]))])
@limiter.limit("10/minute")
async def list_all(
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1_000),
    service: CompetitionsService = Depends(get_service),
) -> PageResponse[CompetitionsRead]:
    """List competitions with offset pagination.

    Args:
        skip: Number of records to skip.
        limit: Maximum records to return.
        service: Injected competitions service.

    Returns:
        Paginated envelope of competition DTOs.
    """
    return await service.list(skip, limit)

@router.get(
    "/by-name",
    response_model=List[CompetitionsRead],
    summary="Get competition by name.",
    description="Retrieve competition records matching name (exact match).",
    dependencies=[Depends(require_permissions(['data:read']))]
)
@limiter.limit("10/minute")
async def get_many_by_name(
    request: Request,
    names: List[str] = Query(
        default=["Premier League"],
        description="One or more name (e.g. 'Premier League')",
    ),
    service: CompetitionsService = Depends(get_service),
) -> List[CompetitionsRead]:
    """Fetch competitions by name.

    Args:
        name: Name values.
        service: Injected competitions service.

    Returns:
        Matching competition DTOs.
    """
    return await service.get_many_by_field(names, "name")

@router.get(
    "/by-code",
    response_model=List[CompetitionsRead],
    summary="Get competition by code",
    description="Retrieve competition records matching code (exact match).",
    dependencies=[Depends(require_permissions(['data:read']))]
)
@limiter.limit('10/minute')
async def get_many_by_code(
    request: Request,
    codes: List[str] = Query(
        default=["EPL"],
        description="One or more code (e.g. 'EPL')",
    ),
    service: CompetitionsService = Depends(get_service)
):
    """Fetch competitions by code.
    
    Args:
        codes: `code` values.
        service: Injected competitions service.

    Returns:
        Matching competition DTOs.
    """
    return await service.get_many_by_field(codes, "code")

@router.get(
    "/by-type",
    response_model=List[CompetitionsRead],
    summary="Get competition by type.",
    description="Retrieve competition records matching type (exact match).",
    dependencies=[Depends(require_permissions(['data:read']))]
)
@limiter.limit('10/minute')
async def get_many_by_type(
    request: Request,
    types: List[str] = Query(
        default=["domestic_league"],
        description="One or more type (e.g. 'domestic_league', 'domestic_cup')"
    ),
    service: CompetitionsService = Depends(get_service)
):
    """Fetch competitions by type.
    
    Args:
        types: `type` values.
        service: Injected competitions service.

    Returns:
        Matching competition DTOs.
    """
    return await service.get_many_by_field(types, "type")

@router.get(
    "/by-country",
    response_model=List[CompetitionsReadWithCountry],
    summary="Get competitions by country names.",
    description="Retrieve competition records associated with specified country names, including the country name.",
    dependencies=[Depends(require_permissions(['data:read']))]
)
@limiter.limit('10/minute')
async def get_many_by_country(
    request: Request,
    countries: List[str] = Query(
        default=["England"],
        description="One or more countries (e.g. 'England', 'Germany')"
    ),
    service: CompetitionsService = Depends(get_service)
) -> List[CompetitionsReadWithCountry]:
    """Fetch competitions associated with specified country names.

    Args:
        countries: One or more country names to filter by.
        service: Injected competitions service.

    Returns:
        List of competition DTOs enriched with their associated country name.
    """
    return await service.get_many_by_countries(countries)

@router.get(
    "/bulk",
    response_model=List[CompetitionsRead],
    summary="Get competitions by ids.",
    description="Retrieve competition records matching ids.",
    dependencies=[Depends(require_permissions(['data:read']))]
)
@limiter.limit('10/minute')
async def get_many(
    request: Request,
    ids: List[int] = Query(description="One or more competition ids."),
    service: CompetitionsService = Depends(get_service),
) -> List[CompetitionsRead]:
    """Fetch multiple competitions by primary key.
    
    Args:
        ids: Competition ids.
        service: Injected competitions service.    
    Returns:
        Matching competition DTOs.
    """
    return await service.get_many(ids)

@router.get(
    "/{competition_id}",
    response_model=CompetitionsRead,
    summary="Get competition by id.",
    description="Retrieve competition record matching id.",
    dependencies=[Depends(require_permissions(['data:read']))]
)
@limiter.limit('10/minute')
async def get_one(
    request: Request,
    competition_id: int,
    service: CompetitionsService = Depends(get_service),
) -> CompetitionsRead:
    """Fetch a single competition by id.

    Args:
        competition_id: Competition primary key.
        service: Injected competitions service.
    
    Returns:
        Competition DTO.
    """
    return await service.get(competition_id)

@router.post(
        "/search",
        response_model=PageResponse[CompetitionsRead],
        summary="Retrieve competitions using dynamic filters.",
        description=(
            "Retrieve a paginated list of competition matching dynamic defined"
            "filter critria across multiple model fields. Support multiple"
            "comperison operations, configurable sorting (asc or desc)"
            "and pagination using skip and limit parameters."
        ),
        dependencies=[Depends(require_permissions('data:read'))]
)
@limiter.limit('10/minute')
async def search(
    request: Request,
    filters: List[FilterItem] = Body(...),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1_000),
    order_by: Optional[str] = Query(None),
    desc: bool = Query(False),
    service: CompetitionsService = Depends(get_service),
) -> PageResponse[CompetitionsRead]:
    """Execute dynamic multi-criteria filter queries over competitions.
    Args:
        filters: Body payload containing list of filter specifications.
        skip: Offset for pagination.
        limit: Max items to return.
        order_by: Column to sort on.
        desc: Sort descending if True.
        service: Injected competitions service.
    Returns:
        List of matching competition DTOs.
    """
    return await service.get_many_by_filters(filters, skip, limit, order_by, desc)


@router.patch(
    "/{competition_id}",
    response_model=CompetitionsRead,
    summary="Update Competition by ID.",
    description=(
        "Update an existing competition identified by its unique ID. "
        "Accepts the fields to be updated and applies the changes to the "
        "corresponding competition records."
    ),
    dependencies=[Depends(require_permissions(['data:write']))]
)
async def update(
    competition_id: int,
    data: CompetitionsUpdate,
    service: CompetitionsService = Depends(get_service),
):
    """Apply partial updates to a competition record.

    Args:
        competition_id: Competition primary key.
        data: Partial update payload.
        service:Injected competition service.
    Returns:
        The updated competition DTO.
    """
    return await service.update(competition_id, data)

@router.delete(
    "/{competition_id}",
    status_code=200,
    response_model=DeleteConfirmation,
    summary="Delete competition by ID",
    description = (
        "Delete an existing competition identified by its unique ID. "
        "Permanently removes the competition record from the database."
    ),
    dependencies=[Depends(require_permissions(['data:write']))]
)
async def delete(
    competition_id: int,
    service: CompetitionsService = Depends(get_service)
) -> DeleteConfirmation:
    """Permanently delete a competition record by ID.
    Args:
        competition_id: Competition primary key.
        service: Injected competition service.
    """
    return await service.delete(competition_id)