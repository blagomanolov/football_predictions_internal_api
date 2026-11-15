from __future__ import annotations

import re
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.exc import IntegrityError

from core.exceptions import ConflictError

@asynccontextmanager
async def handle_ingegrity_error(entity: str = 'record') -> AsyncGenerator[None, None]:
        """Catch ``IntegrityError`` and re-raise as ``ConflictError``.

        Args:
            entity: Human-readable entity name used in the error message.
        
        Raises:
            ConflictError: When a database unique or FK constraint is violated.
        """
        try:
            yield
        except IntegrityError as exc:

            match = re.search(r"Duplicate entry '(.+?)' for key '(.+?)'", str(exc.orig))
            detail = f"Duplicate value for {match.group(2)}" if match else None
            raise ConflictError(
                f"{entity.capitalize()} already exists.",
                details=detail,
            ) from exc