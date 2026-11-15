"""SQLAlchemy declarative base for all ORM models."""

from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase


class Base(AsyncAttrs, DeclarativeBase):
    """Async-capable declarative base for mapped entities."""

    pass
