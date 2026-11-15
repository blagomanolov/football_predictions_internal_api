"""ASGI application entrypoint: settings, logging, lifespan, middleware, routes."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator
import json

import structlog
import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIASGIMiddleware
from starlette.middleware.gzip import GZipMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from api.v1 import api_v1_router
from configs.config import Settings, get_settings
from configs.constants import AppEnv
from configs.logging_config import setup_logging
from core.exception_handlers import register_exception_handlers
from database.database import Database
from middleware.middleware import RequestLoggingMiddleware
from middleware.rate_limit import limiter, rate_limit_exceeded_handler
from middleware.security_headers import SecurityHeadersMiddleware

HEALTH_PATHS = ("/health", "/health/live", "/health/ready")

settings: Settings = get_settings()

setup_logging(
    json_logs=settings.config_env != AppEnv.local,
    level=settings.log_level,
)

log = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Initialize the DB engine on startup and dispose it on shutdown."""
    log.info(
        "app_starting",
        app_name=settings.app_name,
        version=settings.version,
        env=str(settings.config_env),
    )
    database: Database = Database(**settings.model_dump())
    app.state.database = database
    yield
    log.info("app_shutting_down")
    await database.engine.dispose()


swagger_params = {"persistAuthorization": True}
if settings.config_env == AppEnv.local:
    swagger_params["authAction"] = {
        "APIKeyHeader": {
            "name": "APIKeyHeader",
            "schema": {"type": "apiKey", "in": "header", "name": "X-API-Key"},
            "value": settings.api_key.get_secret_value(),
        }
    }

app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    lifespan=lifespan,
    docs_url="/docs" if settings.docs_enabled else None,
    redoc_url="/redoc" if settings.docs_enabled else None,
    openapi_url="/openapi.json" if settings.docs_enabled else None,
    swagger_ui_parameters=swagger_params,
)

app.state.limiter = limiter

app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(SlowAPIASGIMiddleware) 
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["X-API-Key", "X-Request-ID", "Content-Type"],
    expose_headers=["X-Request-ID"],
)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.trusted_hosts)
app.add_middleware(RequestLoggingMiddleware, exclude_paths=HEALTH_PATHS)

app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)
register_exception_handlers(app)


@app.get("/health/live", tags=["Health"], summary="Liveness probe")
@limiter.exempt
async def liveness() -> dict:
    """Liveness probe: the process is up. Never touches the database."""
    return {"status": "ok"}


async def _readiness_response(request: Request) -> JSONResponse:
    """Build the readiness response from a DB ping with a short timeout."""
    db_ok: bool = await request.app.state.database.ping()
    return JSONResponse(
        status_code=200 if db_ok else 503,
        content={"status": "ok" if db_ok else "degraded", "db": db_ok},
    )


@app.get("/health/ready", tags=["Health"], summary="Readiness probe")
@limiter.exempt
async def readiness(request: Request) -> JSONResponse:
    """Readiness probe: the app can serve traffic (database reachable)."""
    return await _readiness_response(request)


@app.get("/health", tags=["Health"], summary="Health check (alias for /health/ready)")
@limiter.exempt
async def health(request: Request) -> JSONResponse:
    """Backward-compatible alias of ``/health/ready``."""
    return await _readiness_response(request)


app.include_router(api_v1_router)

if __name__ == "__main__":
    log.info("launching_dev_server", app_name=settings.app_name, url="http://127.0.0.1:8000")
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=settings.config_env != AppEnv.prod,
        log_config=None,
        access_log=False,
    )