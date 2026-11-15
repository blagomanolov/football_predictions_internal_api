import time
import uuid
from typing import Iterable, Optional
 
import structlog
from starlette.datastructures import Headers, MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

class RequestLoggingMiddleware:
    """
    Logs one structured line per HTTP request and binds request context
    (request_id, method, path, client_ip) to every log line of that request.
 
    Pure ASGI is used instead of BaseHTTPMiddleware: it is faster, does not
    break contextvars, and lets us read values set during the request
    (e.g. the authenticated user from request.state).
    """
 
    def __init__(
        self,
        app: ASGIApp,
        header_name: str = "X-Request-ID",
        exclude_paths: Iterable[str] = ("/health",),
        max_id_length: int = 128,
    ) -> None:
        self.app = app
        self.header_name = header_name
        self.exclude_paths = frozenset(exclude_paths)
        self.max_id_length = max_id_length
        self.log = structlog.get_logger("http")
  
    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
 
        request_id = self._resolve_request_id(scope)
        self._bind_context(scope, request_id)
        scope.setdefault("state", {})["request_id"] = request_id
 
        start = time.perf_counter()
        status_code = 500
 
        async def send_wrapper(message: Message) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
                MutableHeaders(scope=message)[self.header_name] = request_id
            await send(message)
 
        try:
            await self.app(scope, receive, send_wrapper)
        except Exception:
            self._log_failure(scope, start)
            raise
        else:
            self._log_completion(scope, status_code, start)
        finally:
            structlog.contextvars.clear_contextvars()
 
 
    def _resolve_request_id(self, scope: Scope) -> str:
        incoming = Headers(scope=scope).get(self.header_name)
        if incoming:
            return incoming[: self.max_id_length]
        return str(uuid.uuid4())
 
    @staticmethod
    def _bind_context(scope: Scope, request_id: str) -> None:
        structlog.contextvars.clear_contextvars()
        client = scope.get("client")
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            method=scope["method"],
            path=scope["path"],
            client_ip=client[0] if client else None,
        )
 
    @staticmethod
    def _elapsed_ms(start: float) -> float:
        return round((time.perf_counter() - start) * 1000, 2)
 
    @staticmethod
    def _user(scope: Scope) -> Optional[str]:
        return scope.get("state", {}).get("user")
 
    def _is_excluded(self, scope: Scope) -> bool:
        return scope["path"] in self.exclude_paths
 
    def _log_completion(self, scope: Scope, status_code: int, start: float) -> None:
        if self._is_excluded(scope):
            return
        level = "error" if status_code >= 500 else "warning" if status_code >= 400 else "info"
        getattr(self.log, level)(
            "request_completed",
            status_code=status_code,
            duration_ms=self._elapsed_ms(start),
            user=self._user(scope),
        )
 
    def _log_failure(self, scope: Scope, start: float) -> None:
        self.log.exception(
            "request_failed",
            duration_ms=self._elapsed_ms(start),
            user=self._user(scope),
        )