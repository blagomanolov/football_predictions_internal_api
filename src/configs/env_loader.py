"""Resolve which environment file to load for pydantic-settings."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv


def load_base_env() -> Optional[str]:
    """Load ``.env``, then return the path to ``.env.{CONFIG_ENV}`` if it exists.

    Reads the project-root ``.env`` (if present) to obtain ``CONFIG_ENV``
    (default ``local``), then looks for ``.env.<config_env>`` two levels above
    this package (``football_api/``).

    In containers there are normally no env files: configuration comes from
    real environment variables, which pydantic-settings reads (and which take
    priority over file values). A missing file is therefore not an error.

    Returns:
        Absolute path string to the environment-specific env file, or ``None``
        when the file does not exist.
    """
    root: Path = Path(__file__).resolve().parents[2]
    base_env_file: Path = root / ".env"
    if base_env_file.exists():
        load_dotenv(base_env_file)

    config_env = os.getenv("CONFIG_ENV", "local")
    env_file: Path = root / f".env.{config_env}"
    return str(env_file) if env_file.exists() else None