"""Business logic for teams lookups."""

from __future__ import annotations

from typing import List, Optional

from schemas.filters import FilterItem
from schemas.base import PageResponse
from core.exceptions import NotFoundError
from core.db_error_handler import handle_integrity_error
from repositories.teams import TeamsRepository
from schemas.teams import (
    TeamsRead,
    TeamsCreate,
    TeamsUpdate,
    TeamsReadWithCountryAndCityAndVenue
)

class TeamsService:
    """Teams use-cases; raises domain-errors, not HTTP exceptions."""
    def __init__(self, repository: TeamsRepository) -> None:
        """Bind a teams repository.

        Args:
            repository: Data-access collaborator.
        """
        self.repository:TeamsRepository = repository

    async def create(self, data: TeamsCreate) -> TeamsRead:
        """Create and persist a new teams record.
        Args:
            data: DTO containing team attributes to create.
        Returns:
            The created team serialized as a `TeamsRead` DTO.
        Raises:
            ConflictError: If database unique or foreign key constraints are violated.
        """
        async with handle_integrity_error("teams"):
            obj = await self.repository.create(data.model_dump())
        return TeamsRead.model_validate(obj)

    async def update(self, id: int, data: TeamsUpdate) -> TeamsRead:
        """Apply partial updates to an existing team record.

        Args:
            id: Team primary key
            data: DTO containing fied to update (unset fields are ignored)
        Returns:
            The updated team serialized as a ``TeamsRead`` DTO.
        Raises:
            NotFoundError: If no season exists with the given ``id``.
            ConflictError: If update violates unique or foreign key constraints.
        """
        obj = await self.repository.get(id)
        if not obj:
            raise NotFoundError("Team not found.")

        updated_data = data.model_dump(exclude_unset=True)
        if updated_data:
            async with handle_integrity_error("team"):
                obj = await self.repository.update(obj, updated_data)
        return TeamsRead.model_validate(obj)

    async def delete(self, id: int) -> dict:
        """
        Delete an existing team record by primary key.

        Args:
            id: Team primary key.
        Raises:
            NotFoundError: If no team exists with the given ``id``
            ConflictError: If related child records prevent deletion.
        """
        obj = await self.repository.get(id)
        if not obj:
            raise NotFoundError("Team not found.")
        async with handle_integrity_error("team"):
            await self.repository.delete(obj)
        return {
            "id": id,
            "message": f"Team with ID={id} has been successfully deleted.",
            "success": True,
        }

    async def get(self, id: int) -> TeamsRead:
        """Return one team by id.
        
        Args:
            id: Team primary key.
        Return:
            Serialized team DTO.
        Raises:
            NotFoundError: If no row exits for ``id``
        """
        obj = await self.repository.get(id)
        if not obj:
            raise NotFoundError("Team not found.")
        return TeamsRead.model_validate(obj)

    async def get_many(self, ids: List[int]) -> List[TeamsRead]:
        """Return teams matching the given ids.
        
        Args:
            ids: Primary keys to load.
        Returns:
            List of team DTOs.
        Raises:
            NotFoundError: If the query returns no rows.
        """
        objs = await self.repository.get_many_by_ids(ids)
        if not objs:
            raise NotFoundError("Team not found.")
        return [TeamsRead.model_validate(obj) for obj in objs]

    async def get_many_by_field(self, field_values: List[str], field_name: str) -> List[TeamsRead]:
        """Return team matching values on a named column.
        
        Args:
            field_values: Values for the ``IN`` filter.
            field_name: Column/attribute name (e.g. ``name``, ``short_name``)
        Returns:
            List of team DTOs.
        Raises:
            NotFoundError: If the query returns no rows.
        """
        objs = await self.repository.get_many_by_field(field_values, field_name)
        if not objs:
            raise NotFoundError("Teams not found.")
        return [TeamsRead.model_validate(obj) for obj in objs]

    async def get_many_by_filters(
            self, filters: List[FilterItem], skip: int = 0, limit: int = 100, order_by: Optional[str] = None, desc: bool = False 
    ) -> PageResponse[TeamsRead]:
        """Query team matching dynamic multi-field filter items.
        Args:
            filters: List of ``FilterItem`` criteria.
            skip: Number of records to skip (offset).
            limit: Maximum records to return (page size).
            order_by: Model attribute name to sort by.
            desc: If ``True``, orders descending, otherwise ascending.
        Returns:
            Paginated envelope of matching team DTOs.
        Raises:
            NotFoundError: If no matching teams are found.
        """
        objs, total = await self.repository.get_many_by_filters(
            filters, skip, limit, order_by, desc
        )
        if total == 0:
            raise NotFoundError("Season not found.")
        return PageResponse(
            items=[TeamsRead.model_validate(obj) for obj in objs],
            total=total,
            skip=skip,
            limit=limit
        )

    async def list(self, skip: int = 0, limit: int = 100) -> PageResponse[TeamsRead]:
        """Return a paginated list of teams.
        
        Args:
            skip: Offset.
            limit: Page size.

        Returns:
            Paginated envelope of team DTOs.
        """
        objs, total = await self.repository.list(skip, limit)
        return PageResponse(
            items=[TeamsRead.model_validate(obj) for obj in objs],
            total=total,
            skip=skip,
            limit=limit,
        )

    async def get_many_by_countries(
        self, countries: List[str]
    ) -> List[TeamsReadWithCountryAndCityAndVenue]:
        """Retrieve teams associated with specified country names.
        
        Args:
            countries: List of country names to filter by (e.g. ``['England', 'Germany']``).

        Returns:
            List of teams DTOs enriched with their associated country name.

        Raises:
            NotFoundError: If no teams match the specified country names.
        """
        objs = await self.repository.get_many_by_country_name(countries)
        if not objs:
            raise NotFoundError("Teams not found.")
        return [
            TeamsReadWithCountryAndCityAndVenue(
                **TeamsRead.model_validate(team).model_dump(),
                venue_name=venue_name,
                city_name=city_name,
                country_name=country_name,
                
                
            )
            for team, venue_name, city_name, country_name in objs
        ]

    async def get_many_by_cities(
            self, cities: List[str]
    ) -> List[TeamsReadWithCountryAndCityAndVenue]:
        """Retrieve teams associated with specified city names.
                
        Args:
            cities: List of city names to filter by (e.g. ``['Manchester', 'Liverpool']``).

        Returns:
            List of teams DTOs enriched with their associated city name.

        Raises:
            NotFoundError: If no teams match the specified city names.
        """
        objs = await self.repository.get_many_by_city_name(cities)
        if not objs:
            raise NotFoundError("Teams not found.")
        return [
            TeamsReadWithCountryAndCityAndVenue(
                **TeamsRead.model_validate(team).model_dump(),
                venue_name=venue_name,
                city_name=city_name,
                country_name=country_name,
            )
            for team, venue_name, city_name, country_name in objs
        ]