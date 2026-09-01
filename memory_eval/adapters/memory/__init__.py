"""Memory-system adapters used by retrieval evaluation."""

from .base import MemoryAdapter, MemoryCaseRuntime, MemoryIndexResult, MemorySearchResult
from .off import NoMemoryAdapter
from .registry import create_memory_adapter
from .reme import ReMeCliMemoryAdapter

__all__ = [
    "MemoryAdapter",
    "MemoryCaseRuntime",
    "MemoryIndexResult",
    "MemorySearchResult",
    "NoMemoryAdapter",
    "ReMeCliMemoryAdapter",
    "create_memory_adapter",
]

