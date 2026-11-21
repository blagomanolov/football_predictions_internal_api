# src/database_priv/database.py
"""Async SQLAlchemy engine and session factory for the *access‑control* database.

The privilege DB stores users, roles, and permissions. It is completely isolated from
the main football‑data DB, so credentials and connection parameters are taken
from the `PRV_*` environment variables (exposed via `Settings`).
"""

from __future__ import annotations

import asyncio
from typing import AsyncGenerator

import structlog
from sqlalchemy import text
from sqlalchemy.engine import URL
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from configs.config import settings


class PrivilegeDatabase:
    """Manage a dedicated async engine for the privilege database.

    All connection parameters are read directly from ``settings``; the class does
    **not** accept any kwargs – this keeps the API simple and prevents mismatched
    key names.
    """

    def __init__(self) -> None:
        self.log = structlog.get_logger(__name__)
        self.connection_params = {
            "host": settings.prv_db_host,
            "port": settings.prv_db_port,
            "user": settings.prv_db_user,
            "password": settings.prv_db_password,
            "database": settings.prv_db_name,
            "db_charset": settings.db_charset,
            "db_pool_size": settings.db_pool_size,
            "db_max_overflow": settings.db_max_overflow,
            "db_pool_recycle": settings.db_pool_recycle,
            "db_pool_timeout": settings.db_pool_timeout,
            "db_connect_timeout": settings.db_connect_timeout,
        }

        self.database_url: URL = self._build_url()
        self.engine: AsyncEngine = create_async_engine(
            self.database_url,
            pool_pre_ping=True,
            pool_size=self.connection_params.get("db_pool_size", 10),
            max_overflow=self.connection_params.get("db_max_overflow", 20),
            pool_recycle=self.connection_params.get("db_pool_recycle", 1800),
            pool_timeout=self.connection_params.get("db_pool_timeout", 30),
            connect_args={"connect_timeout": self.connection_params.get("db_connect_timeout", 10)},
            echo=False,
        )
        self.session_factory: async_sessionmaker[AsyncSession] = async_sessionmaker(
            bind=self.engine,
            expire_on_commit=False,
            class_=AsyncSession,
        )
        self.log.info(
            "privilege_db_engine_initialized",
            host=self.connection_params.get("host"),
            database=self.connection_params.get("database"),
            pool_size=self.connection_params.get("db_pool_size", 10),
            max_overflow=self.connection_params.get("db_max_overflow", 20),
        )

    def _build_url(self) -> URL:
        """Construct the ``mysql+aiomysql`` URL from ``self.connection_params``.
        The ``query`` dict must contain **strings**, not raw values; therefore we
        explicitly cast the charset to ``str``.
        """
        return URL.create(
            drivername="mysql+aiomysql",
            username=self.connection_params.get("user"),
            password=self.connection_params.get("password"),
            host=self.connection_params.get("host"),
            port=self.connection_params.get("port"),
            database=self.connection_params.get("database"),
            query={"charset": str(self.connection_params.get("db_charset"))},
        )

    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Yield a session that automatically rolls back on error."""
        async with self.session_factory() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise

    async def ping(self, timeout: float = 3.0) -> bool:
        """Health‑check: ``SELECT 1`` with a hard timeout."""
        try:
            async with asyncio.timeout(timeout):
                async with self.engine.connect() as conn:
                    await conn.execute(text("SELECT 1"))
            return True
        except Exception:
            self.log.exception("privilege_db_ping_failed")
            return False

