"""Memory adapter registry."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .base import MemoryAdapter
from .off import NoMemoryAdapter
from .reme import ReMeCliMemoryAdapter


def create_memory_adapter(
    name: str,
    *,
    command: list[str] | None = None,
    config_path: Path | None = None,
    startup_timeout: float = 60.0,
    vector_weight: float = 0.0,
    **reme_hooks: Any,
) -> MemoryAdapter:
    selected = name.strip().lower()
    if selected == "off":
        return NoMemoryAdapter()
    if selected == "reme":
        if not command or config_path is None:
            raise ValueError("ReMe adapter requires a command and config_path")
        return ReMeCliMemoryAdapter(
            command=command,
            config_path=config_path,
            startup_timeout=startup_timeout,
            vector_weight=vector_weight,
            **reme_hooks,
        )
    raise ValueError("Unknown memory adapter {!r}; available: off, reme".format(name))

