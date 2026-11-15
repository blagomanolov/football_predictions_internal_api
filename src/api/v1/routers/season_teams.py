"""HTTP routes for season_teams reference data."""

from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, Query, Body, Request
from sqlalchemy.ext.asyncio import AsyncSession

from middleware.rate_limit import limiter
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

@router.get(
    "/by-country",
    response_model=List[SeasonTeamsWithSeasonAndTeam],
    summary="Get season_teams by country names.",
    description=(
        "Retrieve season_teams records associated with specified country names, including the season name, "
        "team name."
    )
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