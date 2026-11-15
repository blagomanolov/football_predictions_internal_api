"""ORM model for ``football_predictions.seasons``."""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING
from sqlalchemy import Integer, String, Boolean, ForeignKey, Date, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base
from models.timestampmixins import TimestampMixin

if TYPE_CHECKING:
    from models.competitions import Competitions
    from models.season_teams import SeasonTeams


class Seasons(Base, TimestampMixin):
    """Persisted seasons reference row."""

    __tablename__ = "seasons"
    __table_args__ = (
        UniqueConstraint("competition_id", "name", name="uq_competition_season"),
        {"schema": "football_predictions"},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    competition_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(
            "football_predictions.competitions.id",
            ondelete="CASCADE",
            name="fk_seasons_competition",
        ),
        nullable=False,
    )

    name: Mapped[str] = mapped_column(String(50), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    is_current: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    competition: Mapped["Competitions"] = relationship(
        "Competitions", back_populates="seasons"
    )

    season_teams: Mapped[list["SeasonTeams"]] = relationship(
        "SeasonTeams",
        back_populates="season",
        cascade="all, delete-orphan",
        passive_deletes=True
    )