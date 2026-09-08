from __future__ import annotations

import os
import shutil
import socket
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Callable, Iterator
from uuid import uuid4

import pytest

from dataset.build_pipeline import ReviewedBenchmark
from memory_eval.adapters.memory.base import MemoryCaseRuntime, MemoryIndexResult, MemorySearchResult
from memory_eval.adapters.memory.reme import (
    ReMeCliMemoryAdapter,
    create_bm25_config,
    resolve_reme_command,
    write_case_workspace,
)
from memory_eval.runners import MemEvalRunConfig, MemEvalRunner
from memory_eval.systems import ReMeSystemAdapter
from tests.helpers import workspace_directory


class ContractReMeBackend:
    """Deterministic ReMe workspace backend for runner integration tests."""

    name = "reme"
    enabled = True

    def open_case(
        self,
        *,
        workspace: Path,
        case: dict[str, Any],
        dataset_id: str,
        port: int,
        service_log_path: Path,
    ) -> MemoryCaseRuntime:
        del port, service_log_path
        path_map = write_case_workspace(workspace, case, dataset_id)
        written = [workspace / path for path in path_map if path.startswith("daily/")]
        return MemoryCaseRuntime(
            workspace=workspace,
            path_map=path_map,
            written_files=written,
            metadata={"case": case},
        )

    def index(self, runtime: MemoryCaseRuntime) -> MemoryIndexResult:
        items = [{"path": str(path), "success": True} for path in runtime.written_files]
        return MemoryIndexResult({"success": True}, items, {"n_chunks": len(items)}, [], 0.0)

    def search(
        self,
        runtime: MemoryCaseRuntime,
        *,
        query: str,
        top_k: int,
        search_multiplier: int,
        min_score: float,
    ) -> MemorySearchResult:
        del query, search_multiplier, min_score
        case = runtime.metadata["case"]
        available = {session["session_id"] for session in case["sessions"]}
        preferred = [value for value in case["evidence_session_ids"] if value in available]
        selected = preferred or [session["session_id"] for session in case["sessions"]]
        rows = [
            {"rank": rank, "session_id": session_id, "score": 1.0, "text": session_id}
            for rank, session_id in enumerate(selected[:top_k], 1)
        ]
        return MemorySearchResult({"results": rows}, rows, rows, 0.0)

    def close_case(self, runtime: MemoryCaseRuntime, *, keep_workspace: bool) -> None:
        if not keep_workspace:
            shutil.rmtree(runtime.workspace, ignore_errors=True)

    def run_metadata(self) -> dict[str, Any]:
        return {"memory_backend": "ReMe", "memory_version": "contract-test"}


EXPECTED_STATUSES = {
    "D01": "partial",
    "D02": "ok",
    "D03": "partial",
    "D04": "unsupported",
    "D05": "partial",
    "D06": "partial",
    "D07": "partial",
    "D08": "ok",
}


@pytest.fixture
def reme_dimension_runner() -> Iterator[Callable[[str], dict[str, Any]]]:
    with workspace_directory("stage29-reme-integration") as directory:
        benchmark = ReviewedBenchmark("dataset/MemEval-v0.1")

        def run(dimension_id: str) -> dict[str, Any]:
            artifact = next(benchmark.iter_cases(dimension_id))
            system = ReMeSystemAdapter(ContractReMeBackend())
            result = MemEvalRunner(system, directory / dimension_id).run_case(
                artifact,
                MemEvalRunConfig(f"stage29-{dimension_id.lower()}", top_k=10),
            )
            assert result["dimension_id"] == dimension_id
            assert result["error"] is None
            assert result["status"] == EXPECTED_STATUSES[dimension_id]
            return result

        yield run


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


@contextmanager
def _live_workspace_directory() -> Iterator[Path]:
    root = Path.cwd() / ".test-artifacts" / f"stage29-live-reme-{uuid4().hex}"
    root.mkdir(parents=True)
    try:
        yield root
    finally:
        for attempt in range(50):
            try:
                shutil.rmtree(root)
                break
            except PermissionError:
                if attempt == 49:
                    raise
                time.sleep(0.1)


@pytest.fixture
def live_reme_dimension_runner() -> Iterator[Callable[[str], dict[str, Any]]]:
    if os.environ.get("MEMEVAL_LIVE_REME") != "1":
        pytest.skip("set MEMEVAL_LIVE_REME=1 to run the local ReMe CLI integration matrix")
    command = resolve_reme_command(None)
    with _live_workspace_directory() as directory:
        benchmark = ReviewedBenchmark("dataset/MemEval-v0.1")

        def run(dimension_id: str) -> dict[str, Any]:
            artifact = next(benchmark.iter_cases(dimension_id))
            config_path = create_bm25_config(directory / f"{dimension_id.lower()}-bm25.yaml", 0.0)
            backend = ReMeCliMemoryAdapter(
                command=command,
                config_path=config_path,
                startup_timeout=60.0,
                vector_weight=0.0,
            )
            result = MemEvalRunner(
                ReMeSystemAdapter(backend), directory / f"{dimension_id}-work"
            ).run_case(
                artifact,
                MemEvalRunConfig(
                    f"stage29-live-{dimension_id.lower()}",
                    top_k=3,
                    port=_free_port(),
                ),
            )
            assert result["dimension_id"] == dimension_id
            assert result["error"] is None
            assert result["status"] == EXPECTED_STATUSES[dimension_id]
            return result

        yield run
