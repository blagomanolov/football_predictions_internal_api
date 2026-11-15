"""Application settings loaded from environment variables / env files."""

from __future__ import annotations

from functools import lru_cache
from typing import Any, Dict, Optional

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

from configs.constants import AppEnv
from configs.env_loader import load_base_env

ENV_FILE: Optional[str] = load_base_env()


class Settings(BaseSettings):
    """Runtime configuration for the API process.

    Real environment variables always win over values from the env file
    selected by ``CONFIG_ENV`` (see ``load_base_env``). Field aliases map to
    uppercase env var names.
    """

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    config_env: AppEnv = Field(default=AppEnv.local, alias="CONFIG_ENV")
    app_name: str = Field(..., alias="APP_NAME")
    version: str = Field(default="1.0.0", alias="VERSION")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    debug: bool = Field(default=False, alias="DEBUG")
    api_key: SecretStr = Field(..., alias="API_KEY")
    allowed_origins: list[str] = Field(default=["http://localhost:3000"], alias="ALLOWED_ORIGINS")
    trusted_hosts: list[str] = Field(default=["*"], alias="TRUSTED_HOSTS")

    rate_limit_default: str = Field(default="200/minute", alias="RATE_LIMIT_DEFAULT")
    rate_limit_storage_uri: str = Field(default="memory://", alias="RATE_LIMIT_STORAGE_URI")

    host: str = Field(..., alias="DB_HOST")
    port: int = Field(default=3306, alias="DB_PORT")
    user: str = Field(..., alias="DB_USER")
    password: str = Field(..., alias="DB_PASSWORD")
    database: str = Field(..., alias="DB_NAME")
    db_charset: str = Field(default="utf8mb4", alias="DB_CHARSET")
    db_pool_size: int = Field(default=10, alias="DB_POOL_SIZE")
    db_max_overflow: int = Field(default=20, alias="DB_MAX_OVERFLOW")
    db_pool_recycle: int = Field(default=1800, alias="DB_POOL_RECYCLE")
    db_pool_timeout: int = Field(default=30, alias="DB_POOL_TIMEOUT")
    db_connect_timeout: int = Field(default=10, alias="DB_CONNECT_TIMEOUT")

    vault: Optional[Dict[str, Any]] = None

    @property
    def docs_enabled(self) -> bool:
        """Swagger/ReDoc/OpenAPI are exposed everywhere except production."""
        return self.config_env != AppEnv.prod


@lru_cache
def get_settings() -> Settings:
    """Return the process-wide cached ``Settings`` instance."""
    return Settings()