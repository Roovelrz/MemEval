"""No-memory control adapter."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from .base import MemoryCaseRuntime, MemoryIndexResult, MemorySearchResult


class NoMemoryAdapter:
    """Intentionally returns no memory, for the no-memory experimental control."""

    name = "off"
    enabled = False

    def open_case(
        self,
        *,
        workspace: Path,
        case: dict[str, Any],
        dataset_id: str,
        port: int,
        service_log_path: Path,
    ) -> MemoryCaseRuntime:
        del case, dataset_id, port, service_log_path
        return MemoryCaseRuntime(workspace=workspace)

    def index(self, runtime: MemoryCaseRuntime) -> MemoryIndexResult:
        del runtime
        return MemoryIndexResult(response={}, items=[], health={}, failures=[], latency_ms=0.0)

    def search(
        self,
        runtime: MemoryCaseRuntime,
        *,
        query: str,
        top_k: int,
        search_multiplier: int,
        min_score: float,
    ) -> MemorySearchResult:
        del runtime, query, top_k, search_multiplier, min_score
        return MemorySearchResult(response={}, raw_results=[], retrieved=[], latency_ms=0.0)

    def close_case(self, runtime: MemoryCaseRuntime, *, keep_workspace: bool) -> None:
        if runtime.workspace.exists() and not keep_workspace:
            shutil.rmtree(runtime.workspace, ignore_errors=True)

    def run_metadata(self) -> dict[str, Any]:
        return {
            "memory_backend": "none",
            "memory_version": "NOT_APPLICABLE",
            "retrieval_backend": "none",
            "embedding_enabled": False,
            "llm_enabled": False,
        }

