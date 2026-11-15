"""ORM mixins for common timestamp columns."""

from sqlalchemy import TIMESTAMP, func
from sqlalchemy.orm import Mapped, mapped_column


class TimestampMixin:
    """Adds a server-default ``created_at`` column to mapped classes."""

    created_at: Mapped[TIMESTAMP] = mapped_column(
        TIMESTAMP,
        server_default=func.current_timestamp(),
        nullable=False,
    )

class TimestampFullMixin(TimestampMixin):
    """Adds a server-default ``created_at`` and ``updated_at`` to column to mapped classes."""

    updated_at: Mapped[TIMESTAMP] = mapped_column(
        TIMESTAMP,
        server_default=func.current_timestamp(),
        server_onupdate=func.current_timestamp(),
        nullable=False,
    )