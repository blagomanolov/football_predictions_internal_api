"""Add secure HTTP response headers to every reply (pure ASGI, no BaseHTTPMiddleware)."""

from __future__ import annotations

from typing import Dict, Optional

from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

# HSTS is intentionally NOT set here: it must be sent by the TLS-terminating
# reverse proxy / load balancer, which is the component that knows about HTTPS.
DEFAULT_HEADERS: Dict[str, str] = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "0",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Cache-Control": "no-store",
}


class SecurityHeadersMiddleware:
    """Attach hardened security headers to every HTTP response.

    Existing headers set by routes are never overwritten.
    """

    def __init__(self, app: ASGIApp, extra_headers: Optional[Dict[str, str]] = None) -> None:
        """Store the wrapped app and the headers to add.

        Args:
            app: Next ASGI application.
            extra_headers: Additional/overriding headers to send on every response.
        """
        self.app = app
        self.headers: Dict[str, str] = {**DEFAULT_HEADERS, **(extra_headers or {})}

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """Wrap ``send`` so headers are added when the response starts."""
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_wrapper(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = MutableHeaders(scope=message)
                for name, value in self.headers.items():
                    headers.setdefault(name, value)
            await send(message)

        await self.app(scope, receive, send_wrapper)