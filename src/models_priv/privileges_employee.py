"""ORM model for ``access_control.privileges_employee``."""
from datetime import datetime, date

from sqlalchemy import Integer, String, Boolean, UniqueConstraint, ForeignKey, CheckConstraint, DateTime, Date, func
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base

class PrivilegesEmployee(Base):
    """Persisted privileges_employee reference row."""

    __tablename__ = "privileges_employee"
    __table_args__ = (
        UniqueConstraint(
            "username",
            "role_id",
            "scope_code",
            name="uq_priv_username_role_scope",
        ),
        CheckConstraint(
            "(valid_until IS NULL) OR (valid_from IS NULL) OR (valid_until >= valid_from)",
            name="chk_priv_validity",
        ),
        {"schema": "access_control"},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(100), nullable=False)


    role_id: Mapped[int | None] = mapped_column(
        Integer, 
        ForeignKey(
            "roles.id,", 
            ondelete="CASCADE",
            name='fk_priv_employee_role'
        ),
        nullable=False,
    )

    scope_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    granted_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
    granted_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.current_timestamp(), nullable=False)
    valid_from: Mapped[date | None] = mapped_column(Date, nullable=True)
    valid_until: Mapped[date | None] = mapped_column(Date, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)