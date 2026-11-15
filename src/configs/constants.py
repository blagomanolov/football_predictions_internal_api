"""Shared enumerations used across configuration and domain code."""

from enum import auto
from typing import Callable
from strenum import StrEnum


class AppEnv(StrEnum):
    """Deployment environment selector (maps to ``.env.{value}``)."""

    dev = auto()
    prod = auto()
    local = auto()


class IngestionStatus(StrEnum):
    """Lifecycle states for data ingestion pipelines."""

    NEW = "NEW"
    PROCESSING = "PROCESSING"
    QA = "QA"
    ERROR = "ERROR"
    FINISHED = "FINISHED"

OPERATOR_MAP: dict[str, Callable] = {
    "eq": lambda col, val: col == val,
    "in_": lambda col, val: col.in_(val),
    "lt": lambda col, val: col < val,
    "lte": lambda col, val: col <= val,
    "gt": lambda col, val: col > val,
    "gte": lambda col, val: col >= val,
    "like": lambda col, val: col.ilike(f"%{val}%"), 
}