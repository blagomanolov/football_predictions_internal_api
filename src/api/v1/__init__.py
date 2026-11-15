"""API version 1 route modules."""
from fastapi import APIRouter, Depends
from core.security import require_api_key
from api.v1.routers import countries, competitions, seasons, venues, teams, season_teams, players

api_v1_router = APIRouter(
    prefix="/api/v1",
    dependencies=[Depends(require_api_key)],
)

api_v1_router.include_router(countries.router)
api_v1_router.include_router(competitions.router)
api_v1_router.include_router(seasons.router)
api_v1_router.include_router(venues.router)
api_v1_router.include_router(teams.router)
api_v1_router.include_router(season_teams.router)
api_v1_router.include_router(players.router)