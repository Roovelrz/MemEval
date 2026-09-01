"""Common contract for memory systems evaluated by the retrieval runner."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol


@dataclass
class MemoryCaseRuntime:
    workspace: Path
    path_map: dict[str, str] = field(default_factory=dict)
    written_files: list[Path] = field(default_factory=list)
    add_latency_ms: float = 0.0
    process: Any = None
    log_file: Any = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class MemoryIndexResult:
    response: Any
    items: list[dict[str, Any]]
    health: dict[str, Any]
    failures: list[dict[str, Any]]
    latency_ms: float


@dataclass
class MemorySearchResult:
    response: Any
    raw_results: list[dict[str, Any]]
    retrieved: list[dict[str, Any]]
    latency_ms: float


class MemoryAdapter(Protocol):
    """Add sessions, index them, and retrieve memory for one isolated case."""

    name: str
    enabled: bool

    def open_case(
        self,
        *,
        workspace: Path,
        case: dict[str, Any],
        dataset_id: str,
        port: int,
        service_log_path: Path,
    ) -> MemoryCaseRuntime:
        ...

    def index(self, runtime: MemoryCaseRuntime) -> MemoryIndexResult:
        ...

    def search(
        self,
        runtime: MemoryCaseRuntime,
        *,
        query: str,
        top_k: int,
        search_multiplier: int,
        min_score: float,
    ) -> MemorySearchResult:
        ...

    def close_case(self, runtime: MemoryCaseRuntime, *, keep_workspace: bool) -> None:
        ...

    def run_metadata(self) -> dict[str, Any]:
        ...

