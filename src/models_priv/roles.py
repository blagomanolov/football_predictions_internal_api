"""ORM model for ``access_control.roles``."""

from sqlalchemy import Integer, String, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base
from models.timestampmixins import TimestampFullMixin


class Roles(Base, TimestampFullMixin):
    """Persisted roles reference row."""

    __tablename__ = "roles"
    __table_args__ = {"schema": "access_control"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    role_code: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_system_role: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
