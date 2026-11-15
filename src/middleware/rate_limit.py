"""Per-client request rate limiting via SlowAPI (moving window, keyed by client IP)."""

from __future__ import annotations

import structlog
from fastapi import Request
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from configs.config import get_settings

log = structlog.get_logger(__name__)

_settings = get_settings()

# memory:// = counters per worker process. Use redis://... to share across workers/pods.
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[_settings.rate_limit_default],
    storage_uri=_settings.rate_limit_storage_uri,
    strategy="moving-window",
)


async def rate_limit_exceeded_handler(
    request: Request, exc: RateLimitExceeded
) -> JSONResponse:
    """Return 429 when the client exceeds the rate limit.

    Args:
        request: Incoming request.
        exc: SlowAPI rate limit exceeded exception.

    Returns:
        429 JSON response with a retry hint.
    """
    log.warning("rate_limit_exceeded", limit=str(exc.detail))
    return JSONResponse(
        status_code=429,
        content={
            "code": "rate_limit_exceeded",
            "message": f"Rate limit exceeded: {exc.detail}. Try again in 60 seconds.",
            "request_id": getattr(request.state, "request_id", "-"),
        },
        headers={"Retry-After": "60"},
    )