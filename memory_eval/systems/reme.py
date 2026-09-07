"""MemEval wrapper around the existing ReMe CLI memory adapter."""

from __future__ import annotations

import json
import hashlib
import time
from copy import deepcopy
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from memory_eval.adapters.memory.base import MemoryAdapter
from memory_eval.adapters.memory.reme import write_case_workspace

from .base import (
    OptionalSystemOperations, SystemCapabilities, SystemCaseRuntime,
    SystemIngestResult, SystemOperationResult, SystemSearchResult,
)


@dataclass
class ReMeSystemRuntime(SystemCaseRuntime):
    namespace: str = ""
    dataset_id: str = ""
    port: int = 0
    service_log_path: Path = Path()
    initial_case: dict[str, Any] = field(default_factory=dict)
    trace: list[dict[str, Any]] = field(default_factory=list)
    indexed: bool = False
    closed: bool = False


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
        return [str(value) for value in payload.get("winning_fact_ids", [])]
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
        # Lifecycle commands are executed by the Runner, not stored as memories.
        metadata = event.get("metadata") or {}
        if metadata.get("operation") == "delete":
            continue
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
                "memory_id": str(metadata.get("memory_id") or ""),
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


class ReMeSystemAdapter(OptionalSystemOperations):
    """Use the stable ReMe ingestion/search adapter with frozen MemEval Cases."""

    name = "reme"
    capabilities = SystemCapabilities(
        write_trace=True, retrieval=True, delete=True,
        user_isolation=True, latency_stats=True,
    )

    def __init__(self, backend: MemoryAdapter) -> None:
        self.backend = backend
        self._active: dict[Path, ReMeSystemRuntime] = {}

    def create_namespace(
        self, *, namespace: str, workspace: Path, case: dict[str, Any],
        context_path: Path, dataset_id: str, port: int, service_log_path: Path,
    ) -> ReMeSystemRuntime:
        """Caller supplies the namespace's Context; never infer access rights from Gold."""
        digest = hashlib.sha256(namespace.encode("utf-8")).hexdigest()
        runtime = self.open_case(
            workspace=workspace / digest, case=case, context_path=context_path,
            dataset_id=dataset_id, port=port, service_log_path=service_log_path,
        )
        runtime.namespace = namespace
        return runtime

    def open_case(
        self,
        *,
        workspace: Path,
        case: dict[str, Any],
        context_path: Path,
        dataset_id: str,
        port: int,
        service_log_path: Path,
    ) -> ReMeSystemRuntime:
        workspace = workspace.resolve()
        for path, active in self._active.items():
            if workspace == path or workspace in path.parents or path in workspace.parents:
                raise ValueError("Namespace workspace overlaps an active namespace")
            if port == active.port:
                raise ValueError("Each active namespace needs a separate service port")
        prepared = build_reme_case(case, context_path)
        backend_runtime = self.backend.open_case(
            workspace=workspace,
            case=prepared.case,
            dataset_id=dataset_id,
            port=port,
            service_log_path=service_log_path,
        )
        runtime = ReMeSystemRuntime(
            case_id=prepared.case["case_id"],
            dimension_id=prepared.case["dimension_id"],
            backend_runtime=backend_runtime,
            canonical_case=prepared.case,
            event_to_session_id=prepared.event_to_session_id,
            memory_to_session_id=prepared.memory_to_session_id,
            namespace=prepared.case["case_id"], dataset_id=dataset_id, port=port,
            service_log_path=service_log_path, initial_case=deepcopy(prepared.case),
        )
        self._active[workspace] = runtime
        return runtime

    def _require_open(self, runtime: ReMeSystemRuntime) -> None:
        if runtime.closed or self._active.get(runtime.backend_runtime.workspace.resolve()) is not runtime:
            raise ValueError("Namespace is closed or belongs to another adapter")

    def ingest(self, runtime: ReMeSystemRuntime) -> SystemIngestResult:
        self._require_open(runtime)
        runtime.indexed = False
        started = time.perf_counter()
        try:
            result = self.backend.index(runtime.backend_runtime)
        except Exception as exc:
            runtime.trace.append({"operation": "ingest", "status": "error", "error": str(exc),
                                  "latency_ms": (time.perf_counter() - started) * 1000})
            raise
        runtime.indexed = not result.failures
        runtime.trace.append({
            "operation": "ingest", "status": "ok" if runtime.indexed else "error",
            "latency_ms": (time.perf_counter() - started) * 1000,
            "raw_response": result.response, "items": deepcopy(result.items),
            "health": deepcopy(result.health), "failures": deepcopy(result.failures),
        })
        return SystemIngestResult(
            raw_response=result.response,
            items=result.items,
            failures=result.failures,
            latency_ms=result.latency_ms,
        )

    def search(
        self,
        runtime: ReMeSystemRuntime,
        *,
        query: str,
        top_k: int,
        search_multiplier: int = 1,
        min_score: float = 0.0,
    ) -> SystemSearchResult:
        self._require_open(runtime)
        if not runtime.indexed:
            raise ValueError("Successfully ingest the namespace before searching")
        result = self.backend.search(
            runtime.backend_runtime,
            query=query,
            top_k=top_k,
            search_multiplier=search_multiplier,
            min_score=min_score,
        )
        if isinstance(result.response, dict) and result.response.get("success") is False:
            runtime.trace.append({"operation": "search", "status": "error",
                                  "latency_ms": result.latency_ms, "raw_response": result.response})
            raise RuntimeError("ReMe search failed")
        runtime.trace.append({
            "operation": "search", "status": "ok", "query": query,
            "latency_ms": result.latency_ms, "raw_response": result.response,
            "memories": deepcopy(result.retrieved),
        })
        return SystemSearchResult(
            raw_response=result.response,
            memories=result.retrieved,
            latency_ms=result.latency_ms,
        )

    def list_memories(self, runtime: ReMeSystemRuntime) -> SystemOperationResult:
        self._require_open(runtime)
        memories = []
        backend = runtime.backend_runtime
        for path in backend.written_files:
            if path.is_file():
                session_id = backend.path_map[path.name]
                session = next(s for s in runtime.canonical_case["sessions"] if s["session_id"] == session_id)
                memories.append({
                    "memory_id": session_id, "unit": "session",
                    "source_memory_ids": sorted({m["memory_id"] for m in session["messages"] if m.get("memory_id")}),
                    "event_ids": [m["event_id"] for m in session["messages"] if m.get("event_id")],
                    "path": path.relative_to(backend.workspace).as_posix(),
                    "content": path.read_text(encoding="utf-8"), "indexed": runtime.indexed,
                })
        return SystemOperationResult("ok", data=memories)

    def delete(self, runtime: ReMeSystemRuntime, *, memory_ids: list[str]) -> SystemOperationResult:
        self._require_open(runtime)
        requested = set(memory_ids)
        sessions = runtime.canonical_case["sessions"]
        known = {s["session_id"] for s in sessions}
        known.update(m[key] for s in sessions for m in s["messages"]
                     for key in ("event_id", "memory_id") if m.get(key))
        if requested - known:
            raise ValueError(f"Unknown memory IDs: {sorted(requested - known)}")
        if not requested:
            return SystemOperationResult("ok", data={"deleted_ids": []})
        started = time.perf_counter()
        remaining = []
        for session in sessions:
            if session["session_id"] in requested:
                continue
            messages = [m for m in session["messages"]
                        if not requested.intersection((m.get("event_id"), m.get("memory_id")))]
            if messages:
                remaining.append({**session, "messages": messages})
        backend = runtime.backend_runtime
        paths = [path.resolve() for path in backend.written_files]
        if any(backend.workspace.resolve() not in path.parents for path in paths):
            raise ValueError("Memory file lies outside its namespace")
        runtime.indexed = False
        for path in paths:
            path.unlink(missing_ok=True)
        runtime.canonical_case["sessions"] = remaining
        self._refresh_references(runtime)
        backend.path_map = write_case_workspace(backend.workspace, runtime.canonical_case, runtime.dataset_id)
        backend.written_files = [backend.workspace / path for path in backend.path_map
                                 if path.startswith("daily/")]
        result = self.ingest(runtime)
        if result.failures:
            raise RuntimeError("ReMe deletion reindex failed")
        data = {"deleted_ids": sorted(requested)}
        runtime.trace.append({"operation": "delete", "status": "ok", **data,
                              "latency_ms": (time.perf_counter() - started) * 1000})
        return SystemOperationResult("ok", data=data)

    @staticmethod
    def _refresh_references(runtime: ReMeSystemRuntime) -> None:
        runtime.event_to_session_id = {
            m["event_id"]: s["session_id"] for s in runtime.canonical_case["sessions"]
            for m in s["messages"] if m.get("event_id")
        }
        runtime.memory_to_session_id = {
            m["memory_id"]: s["session_id"] for s in runtime.canonical_case["sessions"]
            for m in s["messages"] if m.get("memory_id")
        }

    def reset(self, runtime: ReMeSystemRuntime) -> None:
        self._require_open(runtime)
        workspace = runtime.backend_runtime.workspace
        self.backend.close_case(runtime.backend_runtime, keep_workspace=False)
        runtime.indexed = False
        runtime.closed = True
        self._active.pop(workspace.resolve())
        runtime.canonical_case = deepcopy(runtime.initial_case)
        self._refresh_references(runtime)
        runtime.backend_runtime = self.backend.open_case(
            workspace=workspace, case=runtime.canonical_case, dataset_id=runtime.dataset_id,
            port=runtime.port, service_log_path=runtime.service_log_path,
        )
        runtime.trace.clear()
        runtime.closed = False
        self._active[workspace.resolve()] = runtime

    def get_trace(self, runtime: ReMeSystemRuntime) -> SystemOperationResult:
        return SystemOperationResult("ok", data={"kind": "adapter_operations", "events": deepcopy(runtime.trace)})

    def get_stats(self, runtime: ReMeSystemRuntime) -> SystemOperationResult:
        # Operation totals overlap: delete includes its reindex call; never sum these as total wall time.
        operations = {}
        for event in runtime.trace:
            stats = operations.setdefault(event["operation"], {"calls": 0, "latency_ms": 0.0})
            stats["calls"] += 1
            stats["latency_ms"] += event["latency_ms"]
        return SystemOperationResult("ok", data={
            "operations": operations, "add_latency_ms": runtime.backend_runtime.add_latency_ms,
            "cost": None, "cost_status": "unsupported",
        })

    def cleanup(self, runtime: ReMeSystemRuntime, *, keep_workspace: bool = False) -> None:
        self.close_case(runtime, keep_workspace=keep_workspace)

    def close_case(self, runtime: ReMeSystemRuntime, *, keep_workspace: bool = False) -> None:
        if runtime.closed:
            return
        self._require_open(runtime)
        self.backend.close_case(runtime.backend_runtime, keep_workspace=keep_workspace)
        runtime.closed = True
        self._active.pop(runtime.backend_runtime.workspace.resolve())

    def run_metadata(self) -> dict[str, Any]:
        return {"system_adapter": self.name, "capabilities": asdict(self.capabilities),
                "memory_unit": "session", **self.backend.run_metadata()}
