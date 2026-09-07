"""System adapters that connect frozen MemEval Cases to memory backends."""

from .base import (
    OptionalSystemOperations, SystemAdapter, SystemCapabilities, SystemCaseRuntime,
    SystemIngestResult, SystemOperationResult, SystemSearchResult,
)
from .reme import ReMePreparedCase, ReMeSystemAdapter, build_reme_case

__all__ = [
    "OptionalSystemOperations",
    "SystemCapabilities",
    "SystemOperationResult",
    "ReMePreparedCase",
    "ReMeSystemAdapter",
    "SystemAdapter",
    "SystemCaseRuntime",
    "SystemIngestResult",
    "SystemSearchResult",
    "build_reme_case",
]
