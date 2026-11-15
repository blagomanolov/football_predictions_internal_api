"""Translate SQLAlchemy integrity errors to domain AppError subclasses."""

from __future__ import annotations

import re
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.exc import IntegrityError

from core.exceptions import ConflictError


@asynccontextmanager
async def handle_integrity_error(entity: str = "record") -> AsyncGenerator[None, None]:
    """Catch ``IntegrityError`` and re-raise as domain ``ConflictError``.

    Args:
        entity: Human-readable entity name used in error messages (e.g. 'country', 'competition').

    Raises:
        ConflictError: When a unique or foreign key constraint is violated.
    """
    try:
        yield
    except IntegrityError as exc:
        orig_msg = str(getattr(exc, "orig", exc))

        match = re.search(r"Duplicate entry '(.+?)' for key '(.+?)'", orig_msg)
        if match:
            value = match.group(1)
            key_name = match.group(2).split(".")[-1]
            raise ConflictError(
                f"{entity.capitalize()} already exists with this {key_name}.",
                details={"duplicate_key": key_name, "value": value},
            ) from exc

        if "foreign key constraint fails" in orig_msg.lower():
            raise ConflictError(
                f"Cannot modify or delete {entity}: related records exist or referenced entity not found.",
                details={"error": "foreign_key_violation"},
            ) from exc

        raise ConflictError(
            f"Database constraint violation on {entity}.",
            details={"error": orig_msg},
        ) from exc
