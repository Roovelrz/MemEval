"""Minimal system boundary used by MemEval runners."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal, Protocol


@dataclass(frozen=True)
class SystemCapabilities:
    write_trace: bool = False
    retrieval: bool = False
    activation_trace: bool = False
    profile: bool = False
    delete: bool = False
    user_isolation: bool = False
    latency_stats: bool = False
    cost_stats: bool = False


@dataclass(frozen=True)
class SystemOperationResult:
    """Optional operations have no score; unsupported must remain distinct from zero."""

    status: Literal["ok", "unsupported"]
    data: Any = None
    reason: str = ""


class OptionalSystemOperations:
    """Honest defaults for systems without the optional observation APIs."""

    capabilities = SystemCapabilities()

    def query(self, runtime: SystemCaseRuntime, *, query: str) -> SystemOperationResult:
        return SystemOperationResult("unsupported", reason="Answer generation is not supported")

    def get_profile(self, runtime: SystemCaseRuntime) -> SystemOperationResult:
        return SystemOperationResult("unsupported", reason="Profile extraction is not supported")

    def get_trace(self, runtime: SystemCaseRuntime) -> SystemOperationResult:
        return SystemOperationResult("unsupported", reason="Trace observation is not supported")

    def get_stats(self, runtime: SystemCaseRuntime) -> SystemOperationResult:
        return SystemOperationResult("unsupported", reason="Statistics are not supported")

    def list_memories(self, runtime: SystemCaseRuntime) -> SystemOperationResult:
        return SystemOperationResult("unsupported", reason="Memory listing is not supported")

    def delete(self, runtime: SystemCaseRuntime, *, memory_ids: list[str]) -> SystemOperationResult:
        return SystemOperationResult("unsupported", reason="Memory deletion is not supported")


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
    """Stage-25 system contract; each runtime is one isolated namespace."""

    name: str
    capabilities: SystemCapabilities

    def create_namespace(
        self, *, namespace: str, workspace: Path, case: dict[str, Any],
        context_path: Path, dataset_id: str, port: int, service_log_path: Path,
    ) -> SystemCaseRuntime:
        ...

    def reset(self, runtime: SystemCaseRuntime) -> None:
        """Restore the namespace to its initial, not-yet-indexed Case state."""
        ...

    def cleanup(self, runtime: SystemCaseRuntime, *, keep_workspace: bool = False) -> None:
        ...

    def query(self, runtime: SystemCaseRuntime, *, query: str) -> SystemOperationResult:
        ...

    def list_memories(self, runtime: SystemCaseRuntime) -> SystemOperationResult:
        ...

    def delete(self, runtime: SystemCaseRuntime, *, memory_ids: list[str]) -> SystemOperationResult:
        ...

    def get_profile(self, runtime: SystemCaseRuntime) -> SystemOperationResult:
        ...

    def get_trace(self, runtime: SystemCaseRuntime) -> SystemOperationResult:
        ...

    def get_stats(self, runtime: SystemCaseRuntime) -> SystemOperationResult:
        ...

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
