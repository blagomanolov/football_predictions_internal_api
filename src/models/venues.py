"""ORM model for ``football_predictions.vanues``"""

from __future__ import annotations

from typing import TYPE_CHECKING
from decimal import Decimal
from sqlalchemy import Integer, String, Enum, ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base
from models.timestampmixins import TimestampMixin

if TYPE_CHECKING:
    from models.countries import Countries

class Venues(Base, TimestampMixin):
    """Persisted venues reference row."""

    __tablename__ = "venues"
    __table_args__ = {"schema": "football_predictions"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    country_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey(
            'football_predictions.countries.id',
            ondelete="SET NULL",
            name="fk_venues_country",
        ),
        nullable=True
    )

    name: Mapped[str] = mapped_column(String(150), nullable=False)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    capacity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    surface: Mapped[str] = mapped_column(Enum('natural_grass', 'hybrid_grass', 'artificial_turf', name='surface_enum'), nullable=False, default='natural_grass')
    pitch_length_m: Mapped[Decimal] = mapped_column(Numeric(5,2), nullable=False, default=Decimal("105.00"))
    pitch_width_m: Mapped[Decimal] = mapped_column(Numeric(5,2), nullable=False, default=Decimal("68.00"))
    altitude_m: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    latitude: Mapped[Decimal | None] = mapped_column(Numeric(9, 6), nullable=True)
    longitude: Mapped[Decimal | None] = mapped_column(Numeric(9, 6), nullable=True)  

    country: Mapped["Countries | None"] = relationship("Countries", back_populates="venues")

    teams: Mapped[list["Teams"]] = relationship(
        "Teams",
        back_populates="venue",
        passive_deletes=True,
    )