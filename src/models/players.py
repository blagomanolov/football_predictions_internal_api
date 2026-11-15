"""ORM model for ``football_predictions.players``."""

from __future__ import annotations

from typing import TYPE_CHECKING
from sqlalchemy import Integer, String,  Enum, ForeignKey, DATE, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base
from models.timestampmixins import TimestampFullMixin

if TYPE_CHECKING:
    from models.countries import Countries

class Players(Base, TimestampFullMixin):
    """Persisted players reference row."""

    __tablename__ = "players"
    __table_args__ = {"schema": "football_predictions"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    nationality_country_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey(
            "football_predictions.countries.id",
            ondelete="SET NULL",
            name="fk_players_country",
        ),
        nullable=True
    )

    first_name: Mapped[str] = mapped_column(String(80), nullable=False)
    last_name: Mapped[str] = mapped_column(String(80), nullable=False)
    full_name: Mapped[str] = mapped_column(String(180), nullable=False)
    common_name: Mapped[str | None] = mapped_column(String(80), nullable=True)
    birth_date: Mapped[DATE] = mapped_column(DATE, nullable=False)
    height_cm: Mapped[int | None] = mapped_column(Integer, nullable=True)
    weight_kg: Mapped[int | None] = mapped_column(Integer, nullable=True)
    preferred_foot: Mapped[str] = mapped_column(Enum('left', 'right', 'both', name='prefered_foot_enum'), nullable=False, default='right')
    primary_position: Mapped[str] = mapped_column(Enum('GK', 'DF', 'MF', 'FW', name='primary_position_enum'), nullable=False)
    detailed_position: Mapped[str] = mapped_column(Enum('GK', 'CB', 'LB', 'RB', 'LWB', 'RWB', 'CDM', 'CM', 'CAM', 'LM', 'RM', 'LW', 'RW', 'CF', 'ST', name='detailed_position_enum'), nullable=False)
    market_value_eur: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    photo_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    country: Mapped["Countries | None"] = relationship("Countries", back_populates="players")