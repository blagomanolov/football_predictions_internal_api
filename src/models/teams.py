"""ORM model for ``football_predictions.teams``"""

from __future__ import annotations

from typing import TYPE_CHECKING
from decimal import Decimal

from sqlalchemy import Integer, String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base
from models.timestampmixins import TimestampMixin

if TYPE_CHECKING:
    from models.venues import Venues
    from models.countries import Countries
    from models.season_teams import SeasonTeams

class Teams(Base, TimestampMixin):
    """Persisted teams reference row."""

    __tablename__ = "teams"
    __table_args__ = {"schema": "football_predictions"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    country_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey(
            'football_predictions.countries.id',
            ondelete="SET NULL",
            name="fk_teams_country",
        ),
        nullable=True
    )

    venue_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey(
            'football_predictions.venues.id',
            ondelete="SET NULL",
            name="fk_teams_venue",
        ),
        nullable=True
    )

    name: Mapped[str] = mapped_column(String(120), nullable=False)
    short_name: Mapped[str] = mapped_column(String(50), nullable=False)
    code: Mapped[str] = mapped_column(String(10), nullable=False)
    founded_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    current_manager: Mapped[str | None] = mapped_column(String(100), nullable=True)
    website_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    logo_url: Mapped[str | None] = mapped_column(String(255), nullable=True)

    country: Mapped["Countries | None"] = relationship("Countries", back_populates="teams")
    venue: Mapped["Venues | None"] = relationship("Venues", back_populates="teams")

    season_teams: Mapped[list["SeasonTeams"]] = relationship(
        "SeasonTeams",
        back_populates="team",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )