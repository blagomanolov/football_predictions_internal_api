"""ORM model for ``football_predictions.competitions``."""

from __future__ import annotations

from typing import TYPE_CHECKING
from sqlalchemy import Integer, String, Enum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base
from models.timestampmixins import TimestampMixin

if TYPE_CHECKING:
    from models.countries import Countries
    from models.seasons import Seasons


class Competitions(Base, TimestampMixin):
    """Persisted competitions reference row."""

    __tablename__ = "competitions"
    __table_args__ = {"schema": "football_predictions"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    country_id: Mapped[int | None] = mapped_column(
        Integer, 
        ForeignKey(
            'football_predictions.countries.id', 
            ondelete="SET NULL", 
            name="fk_competitions_country"
        ), 
        nullable=True
    )
    
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    code: Mapped[str] = mapped_column(String(20), nullable=False)
    type: Mapped[str] = mapped_column(Enum('domestic_league','domestic_cup','continental_cup','international', name='type_enum'), nullable=False, default='domestic_league')
    tier: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    logo_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    country: Mapped["Countries | None"] = relationship("Countries", back_populates="competitions")
    
    seasons: Mapped[list["Seasons"]] = relationship(
        "Seasons",
        back_populates="competition",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
