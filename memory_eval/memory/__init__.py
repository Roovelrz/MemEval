"""Memory adapter protocol and local smoke implementation."""

from .base import MemoryAdapter
from .in_memory import InMemorySessionAdapter

__all__ = ["InMemorySessionAdapter", "MemoryAdapter"]
