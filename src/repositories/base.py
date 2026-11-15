"""Generic async repository helpers shared by resource repositories."""

from __future__ import annotations

from typing import Generic, List, Optional, Sequence, Type, TypeVar

from sqlalchemy import and_, func, inspect, select
from sqlalchemy.ext.asyncio import AsyncSession

from configs.constants import OPERATOR_MAP
from core.exceptions import AppError
from schemas.filters import FilterItem

ModelType = TypeVar("ModelType")


class BaseRepository(Generic[ModelType]):
    """CRUD helpers for a single SQLAlchemy mapped model.

    Write methods (``create``/``update``/``delete``) commit by default so that
    any commit-time database error is raised inside the service call (where it
    can be translated to a proper HTTP response). Pass ``commit=False`` to
    group several writes in one transaction and call ``commit()`` yourself.
    """

    def __init__(
        self,
        model: Type[ModelType],
        session: AsyncSession,
        id_field: str = "id",
    ) -> None:
        """Bind a model class and async session.

        Args:
            model: SQLAlchemy mapped class.
            session: Request-scoped async session.
            id_field: Primary key attribute name (default ``id``).
        """
        self.model: Type[ModelType] = model
        self.session: AsyncSession = session
        self.id_field: str = id_field
        self._allowed_columns: set[str] = {
            col.key for col in inspect(self.model).mapper.column_attrs
        }

    # ------------------------------------------------------------------ helpers

    def _order_clauses(self, order_by: Optional[str], desc: bool) -> list:
        """Build deterministic ORDER BY clauses.

        The primary key is always appended as a tie-breaker so offset/limit
        pagination never repeats or skips rows.

        Args:
            order_by: Column name to sort by; ``None`` means the primary key.
            desc: Sort descending when ``True``.

        Returns:
            List of SQLAlchemy ordering expressions.

        Raises:
            AppError: 422 if ``order_by`` is not a column of the model.
        """
        field = order_by or self.id_field
        if field not in self._allowed_columns:
            raise AppError(
                f"Invalid order_by field '{field}' on {self.model.__name__}.",
                code="invalid_order_by",
                status_code=422,
                details={"allowed_fields": sorted(self._allowed_columns)},
            )
        column = getattr(self.model, field)
        primary = column.desc() if desc else column.asc()
        if field == self.id_field:
            return [primary]
        return [primary, getattr(self.model, self.id_field).asc()]

    async def commit(self) -> None:
        """Commit the current transaction."""
        await self.session.commit()

    # -------------------------------------------------------------------- reads

    async def get(self, obj_id: int) -> Optional[ModelType]:
        """Fetch one row by primary key.

        Args:
            obj_id: Primary key value.

        Returns:
            The entity, or ``None`` if not found.
        """
        stmt = select(self.model).where(getattr(self.model, self.id_field) == obj_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_many_by_ids(self, obj_ids: Sequence[int]) -> List[ModelType]:
        """Fetch rows whose primary keys are in ``obj_ids``.

        Args:
            obj_ids: Primary key values.

        Returns:
            Matching entities (may be empty or a subset of requested ids).
        """
        stmt = (
            select(self.model)
            .where(getattr(self.model, self.id_field).in_(obj_ids))
            .order_by(getattr(self.model, self.id_field))
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_many_by_field(
        self, field_values: Sequence[str], field_name: str
    ) -> List[ModelType]:
        """Fetch rows where ``field_name`` is in ``field_values``.

        Args:
            field_values: Values to match (``IN`` clause).
            field_name: Model attribute name.

        Returns:
            Matching entities.

        Raises:
            AppError: 422 if ``field_name`` is not a column of the model.
        """
        if field_name not in self._allowed_columns:
            raise AppError(
                f"Invalid field '{field_name}' on {self.model.__name__}.",
                code="invalid_field",
                status_code=422,
                details={"allowed_fields": sorted(self._allowed_columns)},
            )
        stmt = (
            select(self.model)
            .where(getattr(self.model, field_name).in_(field_values))
            .order_by(getattr(self.model, self.id_field))
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        order_by: Optional[str] = None,
        desc: bool = False,
    ) -> tuple[List[ModelType], int]:
        """Return a paginated list of entities along with the total count.

        Args:
            skip: Number of rows to skip.
            limit: Maximum rows to return.
            order_by: Column to sort by (default: primary key).
            desc: Sort descending when ``True``.

        Returns:
            Tuple of (entities_page, total_count).
        """
        count_stmt = select(func.count()).select_from(self.model)
        total: int = (await self.session.execute(count_stmt)).scalar_one()

        stmt = (
            select(self.model)
            .order_by(*self._order_clauses(order_by, desc))
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all()), total

    async def get_many_by_filters(
        self,
        filters: List[FilterItem],
        skip: int = 0,
        limit: int = 100,
        order_by: Optional[str] = None,
        desc: bool = False,
    ) -> tuple[List[ModelType], int]:
        """Fetch entities matching dynamic multi-field criteria.

        Args:
            filters: ``FilterItem`` criteria (field name + comparison operators).
            skip: Number of rows to skip (offset).
            limit: Maximum rows to return (page size).
            order_by: Model attribute to sort by (default: primary key).
            desc: Sort descending when ``True``.

        Returns:
            Tuple of (matching_models_page, total_count).

        Raises:
            AppError: 422 if a filter or ``order_by`` references an attribute
                that is not a column on ``self.model``.
        """
        conditions: List = []

        for item in filters:
            if item.field not in self._allowed_columns:
                raise AppError(
                    f"Invalid filter field '{item.field}' on {self.model.__name__}.",
                    code="invalid_filter",
                    status_code=422,
                    details={"allowed_fields": sorted(self._allowed_columns)},
                )

            column = getattr(self.model, item.field)

            for op_name, op_func in OPERATOR_MAP.items():
                val = getattr(item, op_name, None)
                if val is not None and val != []:
                    conditions.append(op_func(column, val))

        base_stmt = select(self.model)
        count_stmt = select(func.count()).select_from(self.model)

        if conditions:
            base_stmt = base_stmt.where(and_(*conditions))
            count_stmt = count_stmt.where(and_(*conditions))

        total: int = (await self.session.execute(count_stmt)).scalar_one()

        stmt = (
            base_stmt.order_by(*self._order_clauses(order_by, desc))
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all()), total

    # ------------------------------------------------------------------- writes

    async def create(self, data: dict, *, commit: bool = True) -> ModelType:
        """Instantiate, persist, and refresh a new model instance.

        Args:
            data: Keyword attributes mapping column names to values.
            commit: Commit the transaction (default). Use ``False`` to batch writes.

        Returns:
            The newly created model instance with generated defaults (e.g. ``id``).

        Raises:
            sqlalchemy.exc.IntegrityError: On constraint violations
                (translated by ``handle_integrity_error`` in the service layer).
        """
        obj: ModelType = self.model(**data)
        self.session.add(obj)
        await self.session.flush()
        if commit:
            await self.session.commit()
        await self.session.refresh(obj)
        return obj

    async def update(self, obj: ModelType, data: dict, *, commit: bool = True) -> ModelType:
        """Apply attribute updates to a persisted entity, flush, commit, refresh.

        Args:
            obj: The existing SQLAlchemy model instance to be modified.
            data: Mapping of model attribute names to their new values.
            commit: Commit the transaction (default).

        Returns:
            The updated and refreshed model instance.

        Raises:
            sqlalchemy.exc.IntegrityError: On constraint violations.
        """
        for key, value in data.items():
            setattr(obj, key, value)
        await self.session.flush()
        if commit:
            await self.session.commit()
        await self.session.refresh(obj)
        return obj

    async def delete(self, obj: ModelType, *, commit: bool = True) -> None:
        """Remove a persistent entity from the database.

        Args:
            obj: The SQLAlchemy model instance to delete.
            commit: Commit the transaction (default).

        Raises:
            sqlalchemy.exc.IntegrityError: If foreign key constraints block deletion.
        """
        await self.session.delete(obj)
        await self.session.flush()
        if commit:
            await self.session.commit()