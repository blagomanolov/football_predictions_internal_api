"""HTTP routes for country reference data."""

from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession

from database.dependencies import get_db_session
from repositories.countries import CountriesRepository
from schemas.countries import (
    CountriesRead,
    CountriesCreate,
    CountriesUpdate
)
from services.countries import CountriesService
from schemas.filters import FilterItem
from schemas.base import DeleteConfirmation, PageResponse

router = APIRouter(prefix="/countries", tags=["Countries"])


def get_service(
    session: AsyncSession = Depends(get_db_session),
) -> CountriesService:
    """Build a ``CountriesService`` for the current request.

    Args:
        session: Injected async DB session.

    Returns:
        Service wired to a ``CountriesRepository``.
    """
    repo: CountriesRepository = CountriesRepository(session)
    return CountriesService(repo)

@router.post(
        "/", 
        response_model=CountriesRead,
        summary="Create country record.",
        description="Create country record."
)
async def create(
    data: CountriesCreate, 
    service: CountriesService = Depends(get_service),
):
    """Create a new country reference record.
    Args:
        data: Inbound country payload.
        service: Injected countries service.
    Returns:
        The newly created country DTO.
    """
    return await service.create(data)

@router.get("/", response_model=PageResponse[CountriesRead])
async def list_all(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1_000),
    service: CountriesService = Depends(get_service),
) -> PageResponse[CountriesRead]:
    """List countries with offset pagination.

    Args:
        skip: Number of records to skip.
        limit: Maximum records to return.
        service: Injected countries service.

    Returns:
        Paginated envelope of country DTOs.
    """
    return await service.list(skip, limit)


@router.get(
    "/by-name",
    response_model=List[CountriesRead],
    summary="Get countries by names.",
    description="Retrieve country records matching full country names (exact match).",
)
async def get_many_by_name(
    names: List[str] = Query(
        default=["England"],
        description="One or more country names (e.g. England, Spain, Germany)",
    ),
    service: CountriesService = Depends(get_service),
) -> List[CountriesRead]:
    """Fetch countries by exact ``name`` values.

    Args:
        names: Country names to match.
        service: Injected countries service.

    Returns:
        Matching country DTOs.
    """
    return await service.get_many_by_field(names, "name")


@router.get(
    "/by-code2",
    response_model=List[CountriesRead],
    summary="Get countries by code_alpha2.",
    description="Retrieve country records matching code_alpha2 (exact match).",
)
async def get_many_by_code2(
    codes: List[str] = Query(
        default=["EN"],
        description="One or more code_alpha2 values (e.g. EN, ES, DE)",
    ),
    service: CountriesService = Depends(get_service),
) -> List[CountriesRead]:
    """Fetch countries by ISO alpha-2 style codes.

    Args:
        codes: ``code_alpha2`` values.
        service: Injected countries service.

    Returns:
        Matching country DTOs.
    """
    return await service.get_many_by_field(codes, "code_alpha2")


@router.get(
    "/by-code3",
    response_model=List[CountriesRead],
    summary="Get countries by code_alpha3.",
    description="Retrieve country records matching code_alpha3 (exact match).",
)
async def get_many_by_code3(
    codes: List[str] = Query(
        default=["ENG"],
        description="One or more code_alpha3 values (e.g. ENG, ESP, DEU)",
    ),
    service: CountriesService = Depends(get_service),
) -> List[CountriesRead]:
    """Fetch countries by ISO alpha-3 style codes.

    Args:
        codes: ``code_alpha3`` values.
        service: Injected countries service.

    Returns:
        Matching country DTOs.
    """
    return await service.get_many_by_field(codes, "code_alpha3")


@router.get(
    "/by-confederation",
    response_model=List[CountriesRead],
    summary="Get countries by confederation.",
    description="Retrieve country records matching confederation (exact match).",
)
async def get_many_by_confederation(
    confederations: List[str] = Query(
        default=["UEFA"],
        description="One or more confederations (e.g. UEFA, CAF, CONMEBOL)",
    ),
    service: CountriesService = Depends(get_service),
) -> List[CountriesRead]:
    """Fetch countries by confederation name.

    Args:
        confederations: Confederation values.
        service: Injected countries service.

    Returns:
        Matching country DTOs.
    """
    return await service.get_many_by_field(confederations, "confederation")


@router.get(
    "/bulk",
    response_model=List[CountriesRead],
    summary="Get countries by ids.",
    description="Retrieve country records matching ids.",
)
async def get_many(
    ids: List[int] = Query(description="One or more country ids."),
    service: CountriesService = Depends(get_service),
) -> List[CountriesRead]:
    """Fetch multiple countries by primary key.

    Args:
        ids: Country ids.
        service: Injected countries service.

    Returns:
        Matching country DTOs.
    """
    return await service.get_many(ids)


@router.get(
    "/{country_id}",
    response_model=CountriesRead,
    summary="Get country by id.",
    description="Retrieve country record matching id.",
)
async def get_one(
    country_id: int,
    service: CountriesService = Depends(get_service),
) -> CountriesRead:
    """Fetch a single country by id.

    Args:
        country_id: Country primary key.
        service: Injected countries service.

    Returns:
        Country DTO.
    """
    return await service.get(country_id)

@router.post(
    "/search", 
    response_model=PageResponse[CountriesRead],
    summary="Retrieve countries using dynamic filters.",
    description=(
        "Retrieve a paginated list of countries matching dynamic defined "
        "filter criteria across multiple model fields. Support multiple "
        "comparison operations, configurable sorting (asc or desc), "
        "and pagination using skip and limit parameters."
    )
)
async def search(
    filters: List[FilterItem] = Body(...),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1_000),
    order_by: Optional[str] = Query(None),
    desc: bool = Query(False),
    service: CountriesService = Depends(get_service)
) -> PageResponse[CountriesRead]:
    """Execute dynamic multi-criteria filter queries over countries.
    Args:
        filters: Body payload containing list of filter specifications.
        skip: Offset for pagination.
        limit: Max items to return.
        order_by: Column to sort on.
        desc: Sort descending if True.
        service: Injected countries service.
    Returns:
        List of matching country DTOs.
    """
    return await service.get_many_by_filters(filters, skip, limit, order_by, desc)

@router.patch(
    "/{country_id}", 
    response_model=CountriesRead,
    summary="Update Country by ID.",
    description=(
        "Update an existing country identified by its unique ID. "
        "Accepts the fields to be updated and applies the changes to the "
        "corresponding country record."
    )
)
async def update(
    country_id: int,
    data: CountriesUpdate,
    service: CountriesService = Depends(get_service),
):
    """Apply partial updates to a country record.
    Args:
        country_id: Country primary key.
        data: Partial update payload.
        service: Injected countries service.
    Returns:
        The updated country DTO.
    """
    return await service.update(country_id, data)

@router.delete(
    "/{country_id}",
    status_code=200,
    response_model=DeleteConfirmation,
    summary="Delete country by ID",
    description = (
        "Delete an existing country identified by its unique ID. "
        "Permanently removes the country record from the database."
    )
)
async def delete(
    country_id: int,
    service: CountriesService = Depends(get_service)
) -> DeleteConfirmation:
    """Permanently delete a country record by ID.
    Args:
        country_id: Country primary key.
        service: Injected countries service.
    """
    return await service.delete(country_id)