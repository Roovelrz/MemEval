"""MemEval wrapper around the existing ReMe CLI memory adapter."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from memory_eval.adapters.memory.base import MemoryAdapter

from .base import SystemCaseRuntime, SystemIngestResult, SystemSearchResult


@dataclass(frozen=True)
class ReMePreparedCase:
    case: dict[str, Any]
    event_to_session_id: dict[str, str]
    memory_to_session_id: dict[str, str]


def _load_context_events(context_path: Path) -> list[dict[str, Any]]:
    if context_path.suffix.casefold() == ".jsonl":
        with context_path.open(encoding="utf-8") as handle:
            return [json.loads(line) for line in handle if line.strip()]
    document = json.loads(context_path.read_text(encoding="utf-8"))
    events = document.get("events")
    if not isinstance(events, list):
        raise ValueError(f"Context has no events list: {context_path}")
    return events


def _gold_reference_ids(dimension_id: str, payload: dict[str, Any]) -> list[str]:
    if dimension_id == "D01":
        return [
            str(event_id)
            for memory in payload.get("gold_memories", [])
            for event_id in memory.get("evidence_event_ids", [])
        ]
    if dimension_id in {"D02", "D07"}:
        return [str(value) for value in payload.get("gold_evidence_ids", [])]
    if dimension_id == "D03":
        return [str(value) for value in payload.get("evidence_event_ids", [])]
    if dimension_id == "D04":
        return [str(value) for value in payload.get("required_memory_ids", [])]
    if dimension_id == "D05":
        return [
            str(event_id)
            for item in payload.get("profile_items", [])
            for event_id in item.get("evidence_event_ids", [])
        ]
    if dimension_id == "D06":
        return [str(item.get("fact_id", "")) for item in payload.get("fact_versions", [])]
    if dimension_id == "D08":
        return [
            str(value)
            for key in ("allowed_memory_ids", "forbidden_memory_ids", "deleted_memory_ids")
            for value in payload.get(key, [])
        ]
    return []


def build_reme_case(case: dict[str, Any], context_path: Path) -> ReMePreparedCase:
    """Convert one frozen MemEval Case and Context into ReMe's existing case shape."""

    envelope = case["envelope"]
    dimension_id = str(envelope["dimension_id"])
    events = _load_context_events(context_path)
    declared_count = int(envelope["context"]["event_count"])
    if len(events) != declared_count:
        raise ValueError(
            f"Case {envelope['case_id']!r} declares {declared_count} events, found {len(events)}"
        )

    sessions_by_id: dict[str, dict[str, Any]] = {}
    event_to_session_id: dict[str, str] = {}
    memory_to_session_id: dict[str, str] = {}
    default_session_id = context_path.stem

    for event in events:
        session_id = str(event.get("session_id") or default_session_id)
        session = sessions_by_id.setdefault(
            session_id,
            {
                "session_id": session_id,
                "timestamp": str(event.get("timestamp") or ""),
                "messages": [],
            },
        )
        if not session["timestamp"] and event.get("timestamp"):
            session["timestamp"] = str(event["timestamp"])
        event_id = str(event.get("event_id") or "")
        session["messages"].append(
            {
                "role": str(event.get("role") or "unknown"),
                "content": str(event.get("content") or ""),
                "event_id": event_id,
            }
        )
        if event_id:
            event_to_session_id[event_id] = session_id
        metadata = event.get("metadata")
        if isinstance(metadata, dict) and metadata.get("memory_id"):
            memory_to_session_id[str(metadata["memory_id"])] = session_id

    payload = case["gold"]["payload"]
    session_ids = set(sessions_by_id)
    evidence_session_ids: list[str] = []
    for reference_id in _gold_reference_ids(dimension_id, payload):
        session_id = event_to_session_id.get(reference_id)
        if session_id is None:
            session_id = memory_to_session_id.get(reference_id)
        if session_id is None and reference_id in session_ids:
            session_id = reference_id
        if session_id is None and dimension_id == "D06" and len(session_ids) == 1:
            session_id = next(iter(session_ids))
        if session_id and session_id not in evidence_session_ids:
            evidence_session_ids.append(session_id)

    query = envelope["query"]
    canonical_case = {
        "case_id": str(envelope["case_id"]),
        "dimension_id": dimension_id,
        "question": str(query["text"]),
        "question_date": query.get("timestamp"),
        "gold_answer": payload.get("gold_answer", ""),
        "sessions": list(sessions_by_id.values()),
        "evidence_session_ids": evidence_session_ids,
    }
    return ReMePreparedCase(
        case=canonical_case,
        event_to_session_id=event_to_session_id,
        memory_to_session_id=memory_to_session_id,
    )


class ReMeSystemAdapter:
    """Use the stable ReMe ingestion/search adapter with frozen MemEval Cases."""

    name = "reme"

    def __init__(self, backend: MemoryAdapter) -> None:
        self.backend = backend

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
        prepared = build_reme_case(case, context_path)
        backend_runtime = self.backend.open_case(
            workspace=workspace,
            case=prepared.case,
            dataset_id=dataset_id,
            port=port,
            service_log_path=service_log_path,
        )
        return SystemCaseRuntime(
            case_id=prepared.case["case_id"],
            dimension_id=prepared.case["dimension_id"],
            backend_runtime=backend_runtime,
            canonical_case=prepared.case,
            event_to_session_id=prepared.event_to_session_id,
            memory_to_session_id=prepared.memory_to_session_id,
        )

    def ingest(self, runtime: SystemCaseRuntime) -> SystemIngestResult:
        result = self.backend.index(runtime.backend_runtime)
        return SystemIngestResult(
            raw_response=result.response,
            items=result.items,
            failures=result.failures,
            latency_ms=result.latency_ms,
        )

    def search(
        self,
        runtime: SystemCaseRuntime,
        *,
        query: str,
        top_k: int,
        search_multiplier: int = 1,
        min_score: float = 0.0,
    ) -> SystemSearchResult:
        result = self.backend.search(
            runtime.backend_runtime,
            query=query,
            top_k=top_k,
            search_multiplier=search_multiplier,
            min_score=min_score,
        )
        return SystemSearchResult(
            raw_response=result.response,
            memories=result.retrieved,
            latency_ms=result.latency_ms,
        )

    def close_case(self, runtime: SystemCaseRuntime, *, keep_workspace: bool = False) -> None:
        self.backend.close_case(runtime.backend_runtime, keep_workspace=keep_workspace)

    def run_metadata(self) -> dict[str, Any]:
        return {"system_adapter": self.name, **self.backend.run_metadata()}
