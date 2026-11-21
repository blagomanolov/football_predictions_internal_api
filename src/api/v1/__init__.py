"""API version 1 route modules."""
from fastapi import APIRouter

from .routers import (
    auth,
    countries,
    competitions,
    seasons,
    venues,
    teams,
    season_teams,
    players,
)

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(countries.router)
api_router.include_router(competitions.router)
api_router.include_router(seasons.router)
api_router.include_router(venues.router)
api_router.include_router(teams.router)
api_router.include_router(season_teams.router)
api_router.include_router(players.router)
