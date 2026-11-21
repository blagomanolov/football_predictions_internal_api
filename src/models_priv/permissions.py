"""ORM model for ``access_control.permissions``."""

from sqlalchemy import Integer, String, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base
from models.timestampmixins import TimestampMixin


class Permissions(Base, TimestampMixin):
    """Persisted permissions reference row."""

    __tablename__ = "permissions"
    __table_args__ = {"schema": "access_control"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    permission_code: Mapped[str] = mapped_column(String(80), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
