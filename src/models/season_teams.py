"""ORM model for ``football_predictions.season_teams``."""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING
from sqlalchemy import Integer, String, Boolean, ForeignKey, Date, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base
from models.timestampmixins import TimestampMixin

if TYPE_CHECKING:
    from models.seasons import Seasons
    from models.teams import Teams

class SeasonTeams(Base, TimestampMixin):
    """Persisted seasons reference row."""

    __tablename__ = "season_teams"
    __table_args = (
        UniqueConstraint("season_id", "team_id", name="uq_season_team"),
        {"schema": "football_predictions"},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    season_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(
            "football_predictions.seasons.id",
            ondelete="CASCADE",
            name="fk_season_teams_season"
        )
    )

    team_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(
            "football_predictions.teams.id",
            ondelete="CASCADE",
            name="fk_season_teams_team"
        )
    )

    season: Mapped["Seasons"] = relationship(
        "Seasons", back_populates="season_teams"
    )

    team: Mapped["Teams"] = relationship(
        "Teams", back_populates="season_teams"
    )