"""Business logic for competitions lookups."""

from __future__ import annotations

from typing import List, Optional

from schemas.filters import FilterItem
from schemas.base import PageResponse
from core.exceptions import NotFoundError
from core.db_error_handler import handle_integrity_error
from repositories.competitions import CompetitionsRepository
from schemas.competitions import (
    CompetitionsRead,
    CompetitionsCreate,
    CompetitionsUpdate,
    CompetitionsReadWithCountry
)

class CompetitionsService:
    """Competitions use-cases; raises domain errors, not HTTP exceptions."""

    def __init__(self, repository: CompetitionsRepository) -> None:
        """Bind a competitions repository.

        Args:
            repository: Data-access collaborator.
        """
        self.repository: CompetitionsRepository = repository

    async def create(self, data: CompetitionsCreate) -> CompetitionsRead:
        """Create and persist a new competition record.
        Args:
            data: DTO containing competition attributes to create.
        Returns:
            The created competition serialized as a ``CompetitionsRead`` DTO.
        Raises:
            ConflictError: If database constraints are violated.
        """
        async with handle_integrity_error("competition"):
            obj = await self.repository.create(data.model_dump())
        return CompetitionsRead.model_validate(obj)

    async def update(self, id: int, data: CompetitionsUpdate) -> CompetitionsRead:
        """Apply partial updates to an existing competition record.

        Args:
            id: Competition primary key
            data: DTO containing field to update (unset fields are ignored).
        Returns:
            The updated competition serialized as a `CompetitionsRead` DTO.
        Raises:
            NotFoundError: If no competition exists with the given ``id``.
            ConflictError: If update violates unique constraints.
        """
        obj = await self.repository.get(id)
        if not obj:
            raise NotFoundError("Competition not found.")

        updated_data = data.model_dump(exclude_unset=True)
        if updated_data:
            async with handle_integrity_error("competition"):
                obj = await self.repository.update(obj, updated_data)
        return CompetitionsRead.model_validate(obj)

    async def delete(self, id: int) -> dict:
        """Delete an existing competition record by primary key.
        
        Args:
            id: Competition primary key.
        Raises:
            NotFoundError: If no competition exists with the given ``id``.
            ConflictError: If related child records prevent deletion.
        """
        obj = await self.repository.get(id)
        if not obj:
            raise NotFoundError("Competition not found.")
        async with handle_integrity_error("competition"):
            await self.repository.delete(obj)
        return {
            "id": id,
            "message": f"Competition with ID={id} has been successfully deleted.",
            "success": True,
        }

    async def get(self, id: int) -> CompetitionsRead:
        """Return one competition by id.
        
        Args:
            id: Competition primary key.

        Returns:
            Serialized competition DTO.

        Raises:
            NotFoundError: If no row exists for ``id``.
        """
        obj = await self.repository.get(id)
        if not obj:
            raise NotFoundError("Competition not found.")
        return CompetitionsRead.model_validate(obj)

    async def get_many(self, ids: List[int]) -> List[CompetitionsRead]:
        """Return competitions matching the given ids.
        
        Args:
            ids: Primary keys to load.

        Returns:
            List of competition DTOs.

        Raises:
            NotFoundError: If the query returns no rows.
        """
        objs = await self.repository.get_many_by_ids(ids)
        if not objs:
            raise NotFoundError("Competitions not found.")
        return [CompetitionsRead.model_validate(obj) for obj in objs]

    async def get_many_by_field(self, field_values: List[str], field_name: str) -> List[CompetitionsRead]:
        """Return competition matching values on a named column.
        
        Args:
            field_values: Values for the ``IN`` filter.
            field_name: Column / attribute name (e.g. ``name``, ``code``).

        Returns:
            List of competition DTOs.

        Raises:
            NotFoundError: If the query returns no rows.
        """
        objs = await self.repository.get_many_by_field(field_values, field_name)
        if not objs:
            raise NotFoundError("Competitions not found.")
        return [CompetitionsRead.model_validate(obj) for obj in objs]

    async def get_many_by_filters(
        self, filters: List[FilterItem], skip: int = 0, limit: int = 100, order_by: Optional[str] = None, desc: bool = False
    ) -> PageResponse[CompetitionsRead]:
        """Query competitions matching dynamic multi-field filter items.
        Args:
            filters: List of ``FilterItem`` criteria.
            skip: Number of records to skip (offset).
            limit: Maximum records to return (page size).
            order_by: Model attribute name to sort by.
            desc: If ``True``, orders descending, otherwise ascending.
        Returns:
            Paginated envelope of matching competitions DTOs.
        Raises:
            NotFoundError: If no matching competitions are found.
        """
        objs, total = await self.repository.get_many_by_filters(
            filters, skip, limit, order_by, desc
        )
        if total == 0:
            raise NotFoundError("Competitions not found.")
        return PageResponse(
            items=[CompetitionsRead.model_validate(obj) for obj in objs],
            total=total,
            skip=skip,
            limit=limit,
        )

    async def get_many_by_countries(
        self, countries: List[str]
    ) -> List[CompetitionsReadWithCountry]:
        """Retrieve competitions associated with specified country names.

        Args:
            countries: List of country names to filter by (e.g. ``['England', 'Germany']``).

        Returns:
            List of competition DTOs enriched with their associated country name.

        Raises:
            NotFoundError: If no competitions match the specified country names.
        """
        objs = await self.repository.get_many_by_country_name(countries)
        if not objs:
            raise NotFoundError("Competitions not found.")
        return [
            CompetitionsReadWithCountry(
                **CompetitionsRead.model_validate(competition).model_dump(),
                country_name=country,
            )
            for competition, country in objs
        ]

    async def list(self, skip: int = 0, limit: int = 100) -> PageResponse[CompetitionsRead]:
        """Return a paginated list of competitions.

        Args:
            skip: Offset.
            limit: Page size.

        Returns:
            Paginated envelope of competitions DTOs.
        """
        objs, total = await self.repository.list(skip, limit)
        return PageResponse(
            items=[CompetitionsRead.model_validate(obj) for obj in objs],
            total=total,
            skip=skip,
            limit=limit,
        )
