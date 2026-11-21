"""API-key authentication dependency."""

from __future__ import annotations

import secrets

from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

from configs.config import get_settings

API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)


async def require_api_key(api_key: str | None = Security(API_KEY_HEADER)) -> None:
    """Validate the ``X-API-Key`` header against the configured secret.

    Args:
        api_key: Header value extracted by FastAPI security dependency.

    Raises:
        HTTPException: 401 if the header is missing, 403 if the value is wrong.
    """
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-API-Key header",
        )
    expected = get_settings().api_key.get_secret_value()
    if not secrets.compare_digest(api_key.encode("utf-8"), expected.encode("utf-8")):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key",
        )