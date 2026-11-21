"""ORM model for ``access_control.role_permissions``."""
from datetime import date, datetime

from sqlalchemy import Integer, UniqueConstraint, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base
from models.timestampmixins import TimestampFullMixin

class RolePermissions(Base, TimestampFullMixin):
    """Persisted role_permissions reference row."""

    __tablename__ = "role_permissions"
    __table_args__ = (
        UniqueConstraint(
            "role_id",
            "permission_id",
            name="uq_role_permission",
        ),
        {"schema": "access_control"},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    role_id: Mapped[int | None] = mapped_column(
        Integer, 
        ForeignKey(
            "roles.id,", 
            ondelete="CASCADE",
            name='fk_role_perm_role'
        ),
        nullable=False,
    )

    permission_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey(
            "permissions.id",
            ondelete="CASCADE",
            name='fk_role_perm_permission'
        ),
        nullable=True,
    )
