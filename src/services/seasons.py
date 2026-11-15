"""Business logic for seasons lookups."""

from __future__ import annotations

from typing import List, Optional

from schemas.filters import FilterItem
from schemas.base import PageResponse
from core.exceptions import NotFoundError
from core.db_error_handler import handle_integrity_error
from repositories.seasons import SeasonsRepository
from schemas.seasons import (
    SeasonsRead,
    SeasonsCreate,
    SeasonsUpdate,
    SeasonsReadWithCompetitions,
    SeasonsReadWithCountryAndCompetitions,
)

class SeasonsService:
    """Seasons use-cases; raises domain errors, not HTTP exceptions."""

    def __init__(self, repository: SeasonsRepository) -> None:
        """Bind a seasons repository.

        Args:
            repository: Data-access collaborator.
        """
        self.repository: SeasonsRepository = repository

    async def create(self, data: SeasonsCreate) -> SeasonsRead:
        """Create and persist a new season record.
        Args:
            data: DTO containing season attributes to create.
        Returns:
            The created season serialized as a ``SeasonsRead`` DTO.
        Raises:
            ConflictError: If database unique or foreign key constraints are violated.
        """
        async with handle_integrity_error("season"):
            obj = await self.repository.create(data.model_dump())
        return SeasonsRead.model_validate(obj)

    async def update(self, id: int, data: SeasonsUpdate) -> SeasonsRead:
        """Apply partial updates to an existing season record.

        Args:
            id: Season primary key
            data: DTO containing field to update (unset fields are ignored).
        Returns:
            The updated season serialized as a `SeasonsRead` DTO.
        Raises:
            NotFoundError: If no season exists with the given ``id``.
            ConflictError: If update violates unique or foreign key constraints.
        """
        obj = await self.repository.get(id)
        if not obj:
            raise NotFoundError("Season not found.")

        updated_data = data.model_dump(exclude_unset=True)
        if updated_data:
            async with handle_integrity_error("season"):
                obj = await self.repository.update(obj, updated_data)
        return SeasonsRead.model_validate(obj)

    async def delete(self, id: int) -> dict:
        """
        Delete an existing season record by primary key.

        Args: 
            id: Season primary key.
        Raises:
            NotFoundError: If no season exists with the given ``id``.
            ConflictError: If related child records prevent deletion.
        """
        obj = await self.repository.get(id)
        if not obj:
            raise NotFoundError("Season not found.")
        async with handle_integrity_error("season"):
            await self.repository.delete(obj)
        return {
            "id": id,
            "message": f"Season with ID={id} has been successfully deleted.",
            "success": True,
        }

    async def get(self, id: int) -> SeasonsRead:
        """Return one competition by id.
        
        Args:
            id: Season primary key.
        
        Returns:
            Serialized season DTO.

        Raises:
            NotFoundError: If no row exists for ``id``.
        """
        obj = await self.repository.get(id)
        if not obj:
            raise NotFoundError("Season not found.")
        return SeasonsRead.model_validate(obj)

    async def get_many(self, ids: List[int]) -> List[SeasonsRead]:
        """Return season matching the given ids.
        
        Args:
            ids: Primary keys to load.
        
        Returns:
            List of season DTOs.

        Raises:
            NotFoundError: If the query returns no rows.
        """
        objs = await self.repository.get_many_by_ids(ids)
        if not objs:
            raise NotFoundError("Season not found.")
        return [SeasonsRead.model_validate(obj) for obj in objs]

    async def get_many_by_field(self, field_values: List[str], field_name: str) -> List[SeasonsRead]:
        """Return season matching values on a named column.
        
        Args:
            field_values: Values for the ``IN`` filter.
            field_name: Column / attribute name (e.g. ``name``, ``start_date``).

        Returns:
            List of seasons DTOs.

        Raises:
            NotFoundError: If the query returns no rows.
        """
        objs = await self.repository.get_many_by_field(field_values, field_name)
        if not objs:
            raise NotFoundError("Seaseon not found.")
        return [SeasonsRead.model_validate(obj) for obj in objs]

    async def get_many_by_filters(
        self, filters: List[FilterItem], skip: int = 0, limit: int = 100, order_by: Optional[str] = None, desc: bool = False
    ) -> PageResponse[SeasonsRead]:
        """Query season matching dynamic multi-field filter items.
        Args:
            filters: List of ``FilterItem`` criteria.
            skip: Number of records to skip (offset).
            limit: Maximum records to return (page size).
            order_by: Model attribute name to sort by.
            desc: If ``True``, orders descending, otherwise ascending.
        Returns:
            Paginated envelope of matching season DTOs.
        Raises:
            NotFoundError: If no matching seasons are found.
        """
        objs, total = await self.repository.get_many_by_filters(
            filters, skip, limit, order_by, desc
        )
        if total == 0:
            raise NotFoundError("Season not found.")
        return PageResponse(
            items=[SeasonsRead.model_validate(obj) for obj in objs],
            total=total,
            skip=skip,
            limit=limit,
        )

    async def list(self, skip: int = 0, limit: int = 100) -> PageResponse[SeasonsRead]:
        """Return a paginated list of seasons.

        Args:
            skip: Offset.
            limit: Page size.

        Returns:
            Paginated envelope of season DTOs.
        """
        objs, total = await self.repository.list(skip, limit)
        return PageResponse(
            items=[SeasonsRead.model_validate(obj) for obj in objs],
            total=total,
            skip=skip,
            limit=limit,
        )


    async def get_many_by_countries(
        self, countries: List[str]
    ) -> List[SeasonsReadWithCountryAndCompetitions]:
        """Retrieve seasons associated with specified country names.

        Args:
            countries: List of country names to filter by (e.g. ``['England', 'Germany']``).

        Returns:
            List of seasons DTOs enriched with their associated country name.

        Raises:
            NotFoundError: If no seasons match the specified country names.
        """
        objs = await self.repository.get_many_by_country_name(countries)
        if not objs:
            raise NotFoundError("Seasons not found.")
        return [
            SeasonsReadWithCountryAndCompetitions(
                **SeasonsRead.model_validate(season).model_dump(),
                competition_name=competition,
                country_name=country,
            )
            for season, competition, country in objs
        ]