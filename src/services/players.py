"""Business logic for players lookups."""

from __future__ import annotations

from typing import List, Optional

from schemas.filters import FilterItem
from schemas.base import PageResponse
from core.exceptions import NotFoundError, AppError
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

    async def list_by_market_value_range(
            self, *, min_eur: int | None, max_eur: int | None, skip: int, limit: int
    ) -> PageResponse[PlayersRead]:
        if min_eur is None and max_eur is None:
            raise AppError(
                "Provide at least one market-value bound.",
                code="Ivalid market_value_range.",
                status_code=422
            )

        players, total = await self.repository.list_by_market_value_range(
            min_eur=min_eur, max_eur=max_eur, skip=skip, limit=limit
        )

        return PageResponse(
            items=[PlayersRead.model_validate(player) for player in players],
            total=total,
            skip=skip,
            limit=limit
        )

    async def get_many_by_countries(
        self, countries: List[str]
    ) -> List[PlayersReadWithCountry]:
        """Retrieve players associated with specified country names.

        Args:
            countries: List of country names to filter by (e.g. ``['England', 'Germany']``).

        Returns:
            List of players DTOs enriched with their associated country name.

        Raises:
            NotFoundError: If no players match the specified country names.
        """
        objs = await self.repository.get_many_by_country_name(countries)
        if not objs:
            raise NotFoundError("Players not found.")
        return [
            PlayersReadWithCountry(
                **PlayersRead.model_validate(player).model_dump(),
                country_name=country,
            )
            for player, country in objs
        ]

    async def get_many(self, ids: List[int]) -> List[PlayersRead]:
        """Return players matching the given ids.
        
        Args:
            ids: Primary key to load.
        Returns:
            List of player DTOs.
        Raises:
            NotFoundError: If the query returns no rows.
        """
        objs = await self.repository.get_many_by_ids(ids)
        if not objs:
            raise NotFoundError("Players not found.")
        return [PlayersRead.model_validate(obj) for obj in objs]

    async def get(self, id: int) -> PlayersRead:
        """Return one player by id.
        
        Args:
            id: Player primary key.

        Returns:
            Serialized player DTO.

        Raises:
            NotFoundError: If no row exists for ``id``.
        """
        obj = await self.repository.get(id)
        if not obj:
            raise NotFoundError("Player not found.")
        return PlayersRead.model_validate(obj)

    async def get_many_by_filters(
        self, filters: List[FilterItem], skip: int = 0, limit: int = 100, order_by: Optional[str] = None, desc: bool = False
    ) -> PageResponse[PlayersRead]:
        """Query players matching dynamic multi-field filter items.
        Args:
            filters: List of ``FilterItem`` criteria.
            skip: Number of records to skip (offset).
            limit: Maximum records to return (page size).
            order_by: Model attribute name to sort by.
            desc: If ``True``, orders descending, otherwise ascending.
        Returns:
            Paginated envelope of matching players DTOs.
        Raises:
            NotFoundError: If no matching players are found.
        """
        objs, total = await self.repository.get_many_by_filters(
            filters, skip, limit, order_by, desc
        )
        if total == 0:
            raise NotFoundError("Players not found.")
        return PageResponse(
            items=[PlayersRead.model_validate(obj) for obj in objs],
            total=total,
            skip=skip,
            limit=limit,
        )

    async def update(self, id: int, data: PlayersUpdate) -> PlayersRead:
        """Apply partial updates to an existing player record.

        Args:
            id: Player primary key
            data: DTO containing field to update (unset fields are ignored).
        Returns:
            The updated player serialized as a `PlayerRead` DTO.
        Raises:
            NotFoundError: If no player exists with the given ``id``.
            ConflictError: If update violates unique constraints.
        """
        obj = await self.repository.get(id)
        if not obj:
            raise NotFoundError("Player not found.")

        updated_data = data.model_dump(exclude_unset=True)
        if updated_data:
            async with handle_integrity_error("player"):
                obj = await self.repository.update(obj, updated_data)
        return PlayersRead.model_validate(obj)

    async def delete(self, id: int) -> dict:
        """Delete an existing player record by primary key.
        
        Args:
            id: Player primary key.
        Raises:
            NotFoundError: If no player exists with the given ``id``.
            ConflictError: If related child records prevent deletion.
        """
        obj = await self.repository.get(id)
        if not obj:
            raise NotFoundError("Player not found.")
        async with handle_integrity_error("player"):
            await self.repository.delete(obj)
        return {
            "id": id,
            "message": f"Player with ID={id} has been successfully deleted.",
            "success": True,
        }