"""Business logic for country lookups."""

from __future__ import annotations

from typing import List, Optional

from core.db_error_handler import handle_integrity_error
from schemas.filters import FilterItem
from schemas.base import PageResponse
from core.exceptions import NotFoundError
from repositories.countries import CountriesRepository
from schemas.countries import (
    CountriesRead,
    CountriesCreate,
    CountriesUpdate)


class CountriesService:
    """Country use-cases; raises domain errors, not HTTP exceptions."""

    def __init__(self, repository: CountriesRepository) -> None:
        """Bind a countries repository.

        Args:
            repository: Data-access collaborator.
        """
        self.repository: CountriesRepository = repository

    async def create(self, data: CountriesCreate) -> CountriesRead:
        """Create and persist a new country record.
        Args:
            data: DTO containing country attributes to create.
        Returns:
            The created country serialized as a ``CountriesRead`` DTO.
        Raises:
            SQLAlchemyError: If database constraints are violated.
        """
        async with handle_integrity_error("country"):
            obj = await self.repository.create(data.model_dump())
        return CountriesRead.model_validate(obj)

    async def update(self, id: int, data: CountriesUpdate) -> CountriesRead:
        """Apply partial updates to an existing country record.
        Args:
            id: Country primary key.
            data: DTO containing fields to update (unset fields are ignored).
        Returns:
            The updated country serialized as a ``CountriesRead`` DTO.
        Raises:
            NotFoundError: If no country exists with the given ``id``.
        """
        obj = await self.repository.get(id)
        if not obj:
            raise NotFoundError("Country not found.")
        
        update_data = data.model_dump(exclude_unset=True)
        if update_data:
            async with handle_integrity_error("country"):
                obj = await self.repository.update(obj, update_data)
        return CountriesRead.model_validate(obj)

    async def delete(self, id: int) -> dict:
        """Delete an existing country record by primary key.
        Args:
            id: Country primary key.
        Raises:
            NotFoundError: If no country exists with the given ``id``.
        """
        obj = await self.repository.get(id)
        if not obj:
            raise NotFoundError("Country not found.")
        async with handle_integrity_error("country"):
            await self.repository.delete(obj)
        return {
            "id": id,
            "message": f"Country with ID={id} has been successfully deleted.",
            "success": True,
        }

    async def get(self, id: int) -> CountriesRead:
        """Return one country by id.

        Args:
            id: Country primary key.

        Returns:
            Serialized country DTO.

        Raises:
            NotFoundError: If no row exists for ``id``.
        """
        obj = await self.repository.get(id)
        if not obj:
            raise NotFoundError("Countries not found.")
        return CountriesRead.model_validate(obj)

    async def get_many(self, ids: List[int]) -> List[CountriesRead]:
        """Return countries matching the given ids.

        Args:
            ids: Primary keys to load.

        Returns:
            List of country DTOs.

        Raises:
            NotFoundError: If the query returns no rows.
        """
        objs = await self.repository.get_many_by_ids(ids)
        if not objs:
            raise NotFoundError("Countries not found.")
        return [CountriesRead.model_validate(obj) for obj in objs]

    async def get_many_by_field(
        self, field_values: List[str], field_name: str
    ) -> List[CountriesRead]:
        """Return countries matching values on a named column.

        Args:
            field_values: Values for the ``IN`` filter.
            field_name: Column / attribute name (e.g. ``name``, ``code_alpha2``).

        Returns:
            List of country DTOs.

        Raises:
            NotFoundError: If the query returns no rows.
        """
        objs = await self.repository.get_many_by_field(field_values, field_name)
        if not objs:
            raise NotFoundError("Countries not found.")
        return [CountriesRead.model_validate(obj) for obj in objs]

    async def get_many_by_filters(
        self, filters: List[FilterItem], skip: int = 0, limit: int = 100, order_by: Optional[str] = None, desc: bool = False
    ) -> PageResponse[CountriesRead]:
        """Query countries matching dynamic multi-field filter items.
        Args:
            filters: List of ``FilterItem`` criteria.
            skip: Number of records to skip (offset).
            limit: Maximum records to return (page size).
            order_by: Model attribute name to sort by.
            desc: If ``True``, orders descending; otherwise ascending.
        Returns:
            Paginated envelope containing matching country DTOs and total count.
        Raises:
            NotFoundError: If no matching countries are found.
        """
        objs, total = await self.repository.get_many_by_filters(
            filters, skip, limit, order_by, desc
        )
        if total == 0:
            raise NotFoundError("Countries not found.")
        return PageResponse(
            items=[CountriesRead.model_validate(obj) for obj in objs],
            total=total,
            skip=skip,
            limit=limit,
        )

    async def list(self, skip: int = 0, limit: int = 100) -> PageResponse[CountriesRead]:
        """Return a paginated list of countries.

        Args:
            skip: Offset.
            limit: Page size.

        Returns:
            Paginated envelope containing country DTOs and total count.
        """
        objs, total = await self.repository.list(skip, limit)
        return PageResponse(
            items=[CountriesRead.model_validate(obj) for obj in objs],
            total=total,
            skip=skip,
            limit=limit,
        )
