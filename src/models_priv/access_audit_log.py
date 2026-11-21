"""ORM model for ``access_control.access_audit_log``."""

from __future__ import annotations

from sqlalchemy import Integer, String, Enum, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base
from models.timestampmixins import TimestampMixin

class AccessAuditLog(Base, TimestampMixin):
    """Persisted access_audit_log reference row."""

    __tablename__ = "access_audit_log"
    __table_args__ = {"schema": "access_control"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_type: Mapped[str] = mapped_column(Enum('login_success', 'login_failure', 'role_granted', 'role_revoked', 'employee_created', 'employee_deactivated', name='event_type_enum'), nullable=False)
    username: Mapped[str | None] = mapped_column(String(100), nullable=True)
    performed_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
    role_id: Mapped[int | None] = mapped_column(Integer, nullable=True) 
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    details: Mapped[JSON | None] = mapped_column(JSON, nullable=True)