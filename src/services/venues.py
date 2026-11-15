"""Business logic for venues lookups."""

from __future__ import annotations

from typing import List, Optional

from schemas.filters import FilterItem
from schemas.base import PageResponse
from core.exceptions import NotFoundError
from core.db_error_handler import handle_integrity_error
from repositories.venues import VenuesRepository
from schemas.venues import (
    VenuesRead,
    VenuesCreate,
    VenuesUpdate,
    VenuesReadWithCountry
)

class VenuesService:
    """Venues use-cases; raises domain errors, not HTTP exceptions."""

    def __init__(self, repository: VenuesRepository) -> None:
        """Bind a venues repository.

        Args:
            repository: Data-access collaborator.
        """
        self.repository: VenuesRepository = repository

    async def create(self, data: VenuesCreate) -> VenuesRead:
        """Create and persist a new venues record.
        Args:
            data: DTO containing venues attributes to create.
        Returns:
            The created venues serialized as a ``VenuesRead`` DTO.
        Raises:
            ConflictError: If database unique or foreign key constraints are violated.
        """
        async with handle_integrity_error("venue"):
            obj = await self.repository.create(data.model_dump())
        return VenuesRead.model_validate(obj)

    async def update(self, id: int, data: VenuesUpdate) -> VenuesRead:
        """Apply partial updates to an existing venues record.

        Args:
            id: Venues primary key
            data: DTO containing field to update (unset fields are ignored).
        Returns:
            The updated venues serialized as a `VenuesRead` DTO.
        Raises:
            NotFoundError: If no venues exists with the given ``id``.
            ConflictError: If update violates unique or foreign key constraints.
        """
        obj = await self.repository.get(id)
        if not obj:
            raise NotFoundError("Venues not found.")

        updated_data = data.model_dump(exclude_unset=True)
        if updated_data:
            async with handle_integrity_error("venue"):
                obj = await self.repository.update(obj, updated_data)
        return VenuesRead.model_validate(obj)

    async def delete(self, id: int) -> dict:
        """Delete an existing venues record by primary key.
        
        Args:
            id: Venues primary key.
        Raises:
            NotFoundError: If no venues exists with the given ``id``.
            ConflictError: If related child records prevent deletion.
        """
        obj = await self.repository.get(id)
        if not obj:
            raise NotFoundError("Venues not found.")
        async with handle_integrity_error("venue"):
            await self.repository.delete(obj)
        return {
            "id": id,
            "message": f"Venues with ID={id} has been successfully deleted.",
            "success": True,
        }

    async def get(self, id: int) -> VenuesRead:
        """Return one venues by id.
        
        Args:
            id: Venues primary key.

        Returns:
            Serialized venues DTO.

        Raises:
            NotFoundError: If no row exists for ``id``.
        """
        obj = await self.repository.get(id)
        if not obj:
            raise NotFoundError("Venues not found.")
        return VenuesRead.model_validate(obj)

    async def get_many(self, ids: List[int]) -> List[VenuesRead]:
        """Return venues matching the given ids.
        
        Args:
            ids: Primary keys to load.

        Returns:
            List of venues DTOs.

        Raises:
            NotFoundError: If the query returns no rows.
        """
        objs = await self.repository.get_many_by_ids(ids)
        if not objs:
            raise NotFoundError("Venues not found.")
        return [VenuesRead.model_validate(obj) for obj in objs]

    async def get_many_by_field(self, field_values: List[str], field_name: str) -> List[VenuesRead]:
        """Return venues matching values on a named column.
        
        Args:
            field_values: Values for the ``IN`` filter.
            field_name: Column / attribute name (e.g. ``name``, ``code``).

        Returns:
            List of venues DTOs.

        Raises:
            NotFoundError: If the query returns no rows.
        """
        objs = await self.repository.get_many_by_field(field_values, field_name)
        if not objs:
            raise NotFoundError("Venues not found.")
        return [VenuesRead.model_validate(obj) for obj in objs]

    async def get_many_by_filters(
        self, filters: List[FilterItem], skip: int = 0, limit: int = 100, order_by: Optional[str] = None, desc: bool = False
    ) -> PageResponse[VenuesRead]:
        """Query venues matching dynamic multi-field filter items.
        Args:
            filters: List of ``FilterItem`` criteria.
            skip: Number of records to skip (offset).
            limit: Maximum records to return (page size).
            order_by: Model attribute name to sort by.
            desc: If ``True``, orders descending, otherwise ascending.
        Returns:
            Paginated envelope of matching venues DTOs.
        Raises:
            NotFoundError: If no matching venues are found.
        """
        objs, total = await self.repository.get_many_by_filters(
            filters, skip, limit, order_by, desc
        )
        if total == 0:
            raise NotFoundError("Venues not found.")
        return PageResponse(
            items=[VenuesRead.model_validate(obj) for obj in objs],
            total=total,
            skip=skip,
            limit=limit,
        )

    async def get_many_by_countries(
        self, countries: List[str]
    ) -> List[VenuesReadWithCountry]:
        """Retrieve venues associated with specified country names.

        Args:
            countries: List of country names to filter by (e.g. ``['England', 'Germany']``).

        Returns:
            List of venues DTOs enriched with their associated country name.

        Raises:
            NotFoundError: If no venues match the specified country names.
        """
        objs = await self.repository.get_many_by_country_name(countries)
        if not objs:
            raise NotFoundError("Venues not found.")
        return [
            VenuesReadWithCountry(
                **VenuesRead.model_validate(venues).model_dump(),
                country_name=country,
            )
            for venues, country in objs
        ]

    async def list(self, skip: int = 0, limit: int = 100) -> PageResponse[VenuesRead]:
        """Return a paginated list of venues.

        Args:
            skip: Offset.
            limit: Page size.

        Returns:
            Paginated envelope of venues DTOs.
        """
        objs, total = await self.repository.list(skip, limit)
        return PageResponse(
            items=[VenuesRead.model_validate(obj) for obj in objs],
            total=total,
            skip=skip,
            limit=limit,
        )
