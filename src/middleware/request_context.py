"""Request correlation ID context, logging filter, and access-log middleware."""

from __future__ import annotations

import logging
import time
import uuid
from contextvars import ContextVar
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

request_id_ctx: ContextVar[str] = ContextVar("request_id", default="-")
logger = logging.getLogger("app.access")


class RequestIdFilter(logging.Filter):
    """Inject ``request_id`` from the context var onto every log record."""

    def filter(self, record: logging.LogRecord) -> bool:
        """Attach the current request id and always allow the record.

        Args:
            record: Log record being emitted.

        Returns:
            Always ``True``.
        """
        record.request_id = request_id_ctx.get("-")
        return True


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Assign/echo ``X-Request-ID`` and emit a structured access log line."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process one request with timing and correlation headers.

        Args:
            request: Incoming ASGI request.
            call_next: Next middleware or route handler.

        Returns:
            Downstream response with ``X-Request-ID`` set.

        Raises:
            Exception: Re-raises after logging if the route fails before
                producing a response.
        """
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        token = request_id_ctx.set(request_id)
        start = time.perf_counter()

        try:
            response = await call_next(request)
        except Exception:
            logger.exception(
                "Unhandled error path=%s method=%s",
                request.url.path,
                request.method,
            )
            raise
        finally:
            request_id_ctx.reset(token)

        duration_ms = (time.perf_counter() - start) * 1_000
        response.headers["X-Request-ID"] = request_id
        logger.info(
            "method=%s path=%s status=%s duration_ms=%s",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
            extra={"request_id": request_id},
        )
        return response
