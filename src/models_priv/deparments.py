"""ORM model for ``access_control.departments``."""

from sqlalchemy import Integer, String, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base
from models.timestampmixins import TimestampMixin


class Departments(Base, TimestampMixin):
    """Persisted departments reference row."""

    __tablename__ = "departments"
    __table_args__ = {"schema": "access_control"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    code: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(String(250), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
