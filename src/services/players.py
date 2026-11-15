"""Business logic for players lookups."""

from __future__ import annotations

from typing import List, Optional

from schemas.filters import FilterItem
from schemas.base import PageResponse
from core.exceptions import NotFoundError
from core.db_error_handler import handle_integrity_error
from repositories.players import PlayersRepository
from schemas.players import (
    PlayersRead,
    PlayersCreate,
    PlayersUpdate,
    PlayersReadWithCountry
)

class PlayersService:
    """Players use-cases; raises domain errors, not HTTP exceptions."""

    def __init__(self, repository: PlayersRepository) -> None:
        """Bind a players repository.
        
        Args:
            repository: Data-access collaborator.
        """
        self.repository: PlayersRepository = repository

    async def create(self, data: PlayersCreate) -> PlayersRead:
        """
        Create and persist a new player record.

        Args:
            data: DTO cotnaining player attributes to create.
        Returns:
            The created player serialized as a `PlayersRead`` DTO.
        Raises:
            ConflictError: If database constraints are violated.
        """
        async with handle_integrity_error("player"):
            obj = await self.repository.create(data.model_dump())
        return PlayersRead.model_validate(obj)