"""Minimal system boundary used by MemEval runners."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol


@dataclass
class SystemCaseRuntime:
    """One isolated benchmark Case opened by a memory system."""

    case_id: str
    dimension_id: str
    backend_runtime: Any
    canonical_case: dict[str, Any]
    event_to_session_id: dict[str, str] = field(default_factory=dict)
    memory_to_session_id: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class SystemIngestResult:
    raw_response: Any
    items: list[dict[str, Any]]
    failures: list[dict[str, Any]]
    latency_ms: float


@dataclass(frozen=True)
class SystemSearchResult:
    raw_response: Any
    memories: list[dict[str, Any]]
    latency_ms: float


class SystemAdapter(Protocol):
    """Stage-24 core that later memory-system adapters can implement."""

    name: str

    def open_case(
        self,
        *,
        workspace: Path,
        case: dict[str, Any],
        context_path: Path,
        dataset_id: str,
        port: int,
        service_log_path: Path,
    ) -> SystemCaseRuntime:
        ...

    def ingest(self, runtime: SystemCaseRuntime) -> SystemIngestResult:
        ...

    def search(
        self,
        runtime: SystemCaseRuntime,
        *,
        query: str,
        top_k: int,
        search_multiplier: int = 1,
        min_score: float = 0.0,
    ) -> SystemSearchResult:
        ...

    def close_case(self, runtime: SystemCaseRuntime, *, keep_workspace: bool = False) -> None:
        ...

    def run_metadata(self) -> dict[str, Any]:
        ...
