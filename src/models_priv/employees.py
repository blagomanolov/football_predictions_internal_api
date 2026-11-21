"""ORM model for ``access_control.employees``."""
from datetime import date, datetime

from sqlalchemy import Integer, String, Boolean, ForeignKey, Date, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base
from models.timestampmixins import TimestampFullMixin

class Employees(Base, TimestampFullMixin):
    """Persisted employees reference row."""

    __tablename__ = "employees"
    __table_args__ = {"schema": "access_control"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    employee_number: Mapped[str | None] = mapped_column(String(30), nullable=True, unique=True)
    first_name: Mapped[str] = mapped_column(String(80), nullable=False)
    last_name: Mapped[str] = mapped_column(String(80), nullable=False)
    full_name: Mapped[str] = mapped_column(String(80), nullable=False)
    email: Mapped[str] = mapped_column(String(190), nullable=False, unique=True)
    phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    job_title: Mapped[str | None] = mapped_column(String(120), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    department_id: Mapped[int | None] = mapped_column(
        Integer, 
        ForeignKey(
            "departments.id,", 
            ondelete="SET NULL",
            name='fk_employees_department'
        ),
        nullable=True,
    )

    manager_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey(
            "employees.id",
            ondelete="SET NULL",
            name='fk_employees_manager'
        ),
        nullable=True,
    )

    external_idp_id: Mapped[str | None] = mapped_column(String(190), nullable=True, unique=True)
    hire_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    termination_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime)
