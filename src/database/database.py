"""Async SQLAlchemy engine, session factory, and optional Vault credential load."""

from __future__ import annotations

import asyncio
from typing import Any, AsyncGenerator, Dict, Optional

import structlog
from sqlalchemy import text
from sqlalchemy.engine import URL
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from configs.vault_client import VaultClient


class Database:
    """Manage the MySQL async engine and per-request sessions."""

    def __init__(self, **kwargs: Any) -> None:
        """Build the engine from settings kwargs (and Vault when configured).

        Args:
            **kwargs: Connection settings from ``Settings.model_dump()``.
                Recognized keys include ``host``, ``port``, ``user``,
                ``password``, ``db_charset``, pool settings and optional ``vault``.
        """
        self.log = structlog.get_logger(__name__)
        self.vault_config: Optional[Dict[str, Any]] = kwargs.pop("vault", None)
        self.connection_params: Dict[str, Any] = kwargs

        if self.vault_config:
            self.log.info("db_credentials_source", source="vault")
            self._load_credentials_from_vault()
        else:
            self.log.info("db_credentials_source", source="settings")
        self.database_url: URL = self._build_url()

        self.engine: AsyncEngine = create_async_engine(
            self.database_url,
            pool_pre_ping=True,
            pool_size=self.connection_params.get("db_pool_size", 10),
            max_overflow=self.connection_params.get("db_max_overflow", 20),
            pool_recycle=self.connection_params.get("db_pool_recycle", 1800),
            pool_timeout=self.connection_params.get("db_pool_timeout", 30),
            connect_args={
                "connect_timeout": self.connection_params.get("db_connect_timeout", 10)
            },
            echo=False,
        )

        self.session_factory: async_sessionmaker[AsyncSession] = async_sessionmaker(
            bind=self.engine,
            expire_on_commit=False,
            class_=AsyncSession,
        )

        self.log.info(
            "db_engine_initialized",
            host=self.connection_params.get("host"),
            pool_size=self.connection_params.get("db_pool_size", 10),
            max_overflow=self.connection_params.get("db_max_overflow", 20),
        )

    def _build_url(self) -> URL:
        """Construct the SQLAlchemy ``mysql+aiomysql`` URL.

        Returns:
            Connection URL object (not a string, so the password is never
            interpolated into a loggable string).
        """
        return URL.create(
            drivername="mysql+aiomysql",
            database=self.connection_params.get("database"),
            username=self.connection_params.get("user"),
            password=self.connection_params.get("password"),
            host=self.connection_params.get("host"),
            port=self.connection_params.get("port"),
            query={"charset": self.connection_params.get("db_charset")},
        )

    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Yield an async session for one request; roll back if the request fails.

        Commits are NOT done here. Write operations commit explicitly (see
        ``BaseRepository``) so commit errors become proper HTTP error responses
        instead of happening after the response was already sent.

        Yields:
            A bound ``AsyncSession`` for the current request unit of work.

        Raises:
            Exception: Re-raises after rollback so exception handlers can map it.
        """
        async with self.session_factory() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise

    async def ping(self, timeout: float = 3.0) -> bool:
        """Check database connectivity with a hard timeout (readiness probe).

        Args:
            timeout: Maximum seconds to wait for ``SELECT 1``.

        Returns:
            ``True`` if the database answered in time, otherwise ``False``.
        """
        try:
            async with asyncio.timeout(timeout):
                async with self.engine.connect() as conn:
                    await conn.execute(text("SELECT 1"))
            return True
        except Exception:
            self.log.exception("db_ping_failed")
            return False

    def _load_credentials_from_vault(self) -> None:
        """Overwrite connection params using Vault catalogue or creds path.

        Raises:
            RuntimeError: If Vault config has neither ``catalogue`` nor
                ``creds_path``.
        """
        vault_client: VaultClient = VaultClient(**self.vault_config["client_config"]).setup()

        if "catalogue" in self.vault_config:
            self.log.info("vault_lookup", method="catalogue")
            metadata: Dict = vault_client.get_kv_v2(**self.vault_config["catalogue"])
            creds: Dict = vault_client.read(metadata["vault_path"])

            self.connection_params.update(
                {
                    "host": metadata["db_hostname"],
                    "user": creds["username"],
                    "password": creds["password"],
                }
            )

        elif "creds_path" in self.vault_config:
            self.log.info("vault_lookup", method="creds_path")
            creds = vault_client.read(self.vault_config["creds_path"])
            self.connection_params.update(
                {
                    "user": creds["username"],
                    "password": creds["password"],
                }
            )

        else:
            raise RuntimeError(
                "Unknown method to retrieve database credentials from Vault"
            )
        self.log.info("vault_credentials_loaded")