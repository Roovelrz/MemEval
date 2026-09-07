from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from dataset.build_pipeline import ReviewedBenchmark
from memory_eval.adapters.memory.base import (
    MemoryCaseRuntime,
    MemoryIndexResult,
    MemorySearchResult,
)
from memory_eval.systems import ReMeSystemAdapter, build_reme_case
from tests.helpers import workspace_directory


class _RecordingMemoryAdapter:
    name = "reme"
    enabled = True

    def __init__(self) -> None:
        self.opened_case: dict[str, Any] | None = None
        self.closed = False

    def open_case(
        self,
        *,
        workspace: Path,
        case: dict[str, Any],
        dataset_id: str,
        port: int,
        service_log_path: Path,
    ) -> MemoryCaseRuntime:
        self.opened_case = case
        return MemoryCaseRuntime(
            workspace=workspace,
            metadata={
                "dataset_id": dataset_id,
                "port": port,
                "service_log_path": str(service_log_path),
            },
        )

    def index(self, runtime: MemoryCaseRuntime) -> MemoryIndexResult:
        return MemoryIndexResult(
            response={"success": True},
            items=[{"path": "session.md", "success": True}],
            health={"n_chunks": 1},
            failures=[],
            latency_ms=2.0,
        )

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
        hit = {"session_id": "evidence", "score": 1.0}
        return MemorySearchResult(
            response={"results": [hit]},
            raw_results=[hit],
            retrieved=[hit],
            latency_ms=3.0,
        )

    def close_case(self, runtime: MemoryCaseRuntime, *, keep_workspace: bool) -> None:
        del runtime, keep_workspace
        self.closed = True

    def run_metadata(self) -> dict[str, Any]:
        return {"memory_backend": "ReMe", "memory_version": "test"}


def test_reme_case_conversion_accepts_all_eight_frozen_dimensions() -> None:
    benchmark = ReviewedBenchmark("dataset/MemEval-v0.1")

    for dimension_id in [f"D{index:02d}" for index in range(1, 9)]:
        artifact = next(benchmark.iter_cases(dimension_id))
        prepared = build_reme_case(artifact.case, artifact.context_path)
        message_count = sum(len(session["messages"]) for session in prepared.case["sessions"])

        assert prepared.case["dimension_id"] == dimension_id
        assert prepared.case["question"]
        assert prepared.case["sessions"]
        assert message_count == artifact.case["envelope"]["context"]["event_count"]


def test_reme_system_adapter_delegates_existing_ingestion_and_search() -> None:
    benchmark = ReviewedBenchmark("dataset/MemEval-v0.1")
    artifact = next(benchmark.iter_cases("D02"))
    backend = _RecordingMemoryAdapter()
    adapter = ReMeSystemAdapter(backend)

    with workspace_directory("reme-system-adapter") as directory:
        runtime = adapter.open_case(
            workspace=directory / "workspace",
            case=artifact.case,
            context_path=artifact.context_path,
            dataset_id="MemEval-v0.1",
            port=25000,
            service_log_path=directory / "reme.log",
        )
        ingested = adapter.ingest(runtime)
        searched = adapter.search(runtime, query=runtime.canonical_case["question"], top_k=3)
        adapter.close_case(runtime)

    assert backend.opened_case is runtime.canonical_case
    assert set(runtime.canonical_case["evidence_session_ids"]) <= {
        session["session_id"] for session in runtime.canonical_case["sessions"]
    }
    assert ingested.failures == []
    assert searched.memories == [{"session_id": "evidence", "score": 1.0}]
    assert backend.closed is True
    assert adapter.run_metadata()["system_adapter"] == "reme"


def test_reme_case_conversion_rejects_context_count_mismatch() -> None:
    with workspace_directory("reme-context-count") as directory:
        context_path = directory / "context.json"
        context_path.write_text(json.dumps({"events": []}), encoding="utf-8")
        case = {
            "envelope": {
                "case_id": "fixture",
                "dimension_id": "D02",
                "context": {"event_count": 1},
                "query": {"text": "Where is the memory?", "timestamp": None},
            },
            "gold": {"payload": {"gold_answer": "here", "gold_evidence_ids": []}},
        }

        with pytest.raises(ValueError, match="declares 1 events, found 0"):
            build_reme_case(case, context_path)
