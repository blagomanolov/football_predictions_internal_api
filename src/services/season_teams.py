"""Business logic for season_teams lookups."""

from __future__ import annotations

from typing import List, Optional

from schemas.filters import FilterItem
from schemas.base import PageResponse
from core.exceptions import NotFoundError
from core.db_error_handler import handle_integrity_error
from repositories.season_teams import SeasonTeamsRepository
from schemas.season_teams import (
    SeasonTeamsRead,
    SeasonTeamsCreate,
    SeasonTeamsUpdate,
    SeasonTeamsWithSeasonAndTeam,
)

class SeasonTeamsService:
    """SeasonTeams use cases; raises domain errors, not HTTP exceptions."""
    def __init__(self, repository: SeasonTeamsRepository) -> None:
        """Bind a season_teams repository.
        
        Args:
            repository: Data-acess collaborator."""
        self.repository: SeasonTeamsRepository = repository

    async def create(self, data: SeasonTeamsCreate) -> SeasonTeamsRead:
        """Create and persist a new season_team record.
        Args:
            data: DTO containing season_team attributes to create.
        Returns:
            The created season_team serialized as a `SeasonTeamsRead`` DTO.
        Raises:
            ConflictError: If database unique or fk constraints are vilated.
        """
        async with handle_integrity_error("season_team"):
            obj = await self.repository.create(data.model_dump())
        return SeasonTeamsRead.model_validate(obj)

    async def update(self, id: int, data: SeasonTeamsUpdate) -> SeasonTeamsRead:
        """Apply partial updates to an existing season_team record.
        
        Args:
            id: Season team primary key
            data: DTO containing field to update (unset fields are ignored).
        Returns:
            The updated season_team serialized as a ``SeasonTeamsRead`` DTO.
        Raises:
            NotFoundError: If no season_team exists with the given ``id``.
            ConflictError: If update violates unique or foreign key constraints.
        """
        obj = await self.repository.get(id)
        if not obj:
            raise NotFoundError("SeasonTeam not found.")

        updated_data = data.model_dump(exclude_unset=True)
        if updated_data:
            async with handle_integrity_error("season_team"):
                obj = await self.repository.update(id, updated_data)
        return SeasonTeamsRead.model_validate(obj)

    async def delete(self, id: int) -> dict:
        """
        Delete an existing season_team record by primary key.

        Args: 
            id: Season team primary key.
        Raises:
            NotFoundError: If no season team exists with the given ``id``.
            ConflictError: If related child records prevent deletion.
        """
        obj = await self.repository.get(id)
        if not obj:
            raise NotFoundError("Season team not found.")
        async with handle_integrity_error("season"):
            await self.repository.delete(obj)
        return {
            "id": id,
            "message": f"Season team with ID={id} has been successfully deleted.",
            "success": True,
        }

    async def get(self, id: int) -> SeasonTeamsRead:
        """Return one season_team by id.
        
        Args:
            id: Season team primary key.
        
        Returns:
            Serialized season_team DTO.

        Raises:
            NotFoundError: If no row exists for ``id``.
        """
        obj = await self.repository.get(id)
        if not obj:
            raise NotFoundError("Season team not found.")
        return SeasonTeamsRead.model_validate(obj)

    async def get_many(self, ids: List[int]) -> List[SeasonTeamsRead]:
        """Return season_team matching the given ids.
                
        Args:
            ids: Primary keys to load.
        
        Returns:
            List of season_team DTOs.

        Raises:
            NotFoundError: If the query returns no rows.
        """
        objs = await self.repository.get_many_by_ids(ids)
        if not objs:
            raise NotFoundError("Season team not found.")
        return [SeasonTeamsRead.model_validate(obj) for obj in objs]

    async def get_many_by_field(self, field_values: List[str], field_name: str) -> List[SeasonTeamsRead]:
        """Return season_team matching values on a named column.
        
        Args:
            field_values: Values for the ``IN`` filter.
            field_name: Column / attribute name (e.g. ``name``, ``start_date``).

        Returns:
            List of season_teams DTOs.

        Raises:
            NotFoundError: If the query returns no rows.
        """
        objs = await self.repository.get_many_by_field(field_values, field_name)
        if not objs:
            raise NotFoundError("Season team not found.")
        return [SeasonTeamsRead.model_validate(obj) for obj in objs]

    async def get_many_by_filters(
        self, filters: List[FilterItem], skip: int = 0, limit: int = 100, order_by: Optional[str] = None, desc: bool = False
    ) -> PageResponse[SeasonTeamsRead]:
        """Query season_teams matching dynamic multi-field filter items.
        Args:
            filters: List of ``FilterItem`` criteria.
            skip: Number of records to skip (offset).
            limit: Maximum records to return (page size).
            order_by: Model attribute name to sort by.
            desc: If ``True``, orders descending, otherwise ascending.
        Returns:
            Paginated envelope of matching season_team DTOs.
        Raises:
            NotFoundError: If no matching season_teams are found.
        """
        objs, total = await self.repository.get_many_by_filters(
            filters, skip, limit, order_by, desc
        )
        if total == 0:
            raise NotFoundError("Season team not found.")
        return PageResponse(
            items=[SeasonTeamsRead.model_validate(obj) for obj in objs],
            total=total,
            skip=skip,
            limit=limit
        )

    async def list(self, skip: int = 0, limit: int = 100) -> PageResponse[SeasonTeamsRead]:
        """Return a paginated list of season_teams.

        Args:
            skip: Offset.
            limit: Page size.

        Returns:
            Paginated envelope of season_teams DTOs.
        """
        objs, total = await self.repository.list(skip, limit)
        return PageResponse(
            items=[SeasonTeamsRead.model_validate(obj) for obj in objs],
            total=total,
            skip=skip,
            limit=limit,
        )

    async def get_many_by_countries(
        self, countries: List[str]
    ) -> List[SeasonTeamsWithSeasonAndTeam]:
        """Retrieve season_teams associated with specified country names.

        Args:
            countries: List of country names to filter by (e.g. ``['England', 'Germany']``).

        Returns:
            List of season_teams DTOs enriched with their associated country name.

        Raises:
            NotFoundError: If no season_teams match the specified country names.
        """
        objs = await self.repository.get_many_by_country_name(countries)
        if not objs:
            raise NotFoundError("SeasonTeams not found.")
        return [
            SeasonTeamsWithSeasonAndTeam(
                **SeasonTeamsRead.model_validate(season_team).model_dump(),
                season_name=season,
                team_name=team,
                country_name=country
            )
            for season_team, season, team, country in objs
        ]