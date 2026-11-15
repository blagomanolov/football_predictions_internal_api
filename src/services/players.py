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

    async def get_many_by_field(self, field_values: List[str], field_name: str) -> List[PlayersRead]:
        """Return player matching values on a named column.
        
        Args:
            field_values: Values for the ``IN`` filter.
            field_name: Column/attribute name (e.g. ``name``, ``short_name``)
        Returns:
            List of player DTOs.
        Raises:
            NotFoundError: If the query returns no rows.
        """
        objs = await self.repository.get_many_by_field(field_values, field_name)
        if not objs:
            raise NotFoundError("Players not found.")
        return [PlayersRead.model_validate(obj) for obj in objs]

    async def list(self, skip: int = 0, limit: int = 100) -> PageResponse[PlayersRead]:
        """Return a paginated list of player.
        
        Args:
            skip: Offset.
            limit: Page size.

        Returns:
            Paginated envelope of player DTOs.
        """
        objs, total = await self.repository.list(skip, limit)
        return PageResponse(
            items=[PlayersRead.model_validate(obj) for obj in objs],
            total=total,
            skip=skip,
            limit=limit,
        )

    