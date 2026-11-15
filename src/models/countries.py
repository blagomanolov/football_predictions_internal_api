"""ORM model for ``football_predictions.countries``."""

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base
from models.timestampmixins import TimestampMixin


class Countries(Base, TimestampMixin):
    """Persisted country reference row."""

    __tablename__ = "countries"
    __table_args__ = {"schema": "football_predictions"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    code_alpha2: Mapped[str] = mapped_column(String(2), nullable=False, unique=True)
    code_alpha3: Mapped[str] = mapped_column(String(3), nullable=False, unique=True)
    confederation: Mapped[str] = mapped_column(String(20), nullable=False)
    flag_url: Mapped[str | None] = mapped_column(String(255), nullable=True)

    competitions: Mapped[list["Competitions"]] = relationship(
        "Competitions",
        back_populates="country",
        passive_deletes=True
    )

    venues: Mapped[list["Venues"]] = relationship(
        "Venues",
        back_populates="country",
        passive_deletes=True
    )

    teams: Mapped[list["Teams"]] = relationship(
        "Teams",
        back_populates="country",
        passive_deletes=True
    )

    players: Mapped[list["Players"]] = relationship(
        "Players",
        back_populates="country",
        passive_deletes=True
    )