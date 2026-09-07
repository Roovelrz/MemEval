"""Dimension-aware runner for the frozen MemEval benchmark."""

from __future__ import annotations

import hashlib
import json
import time
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from dataset.build_pipeline.release import ReviewedCaseArtifact
from memory_eval.systems import SystemAdapter, SystemOperationResult


@dataclass(frozen=True)
class MemEvalRunConfig:
    run_id: str
    dataset_id: str = "MemEval-v0.1"
    top_k: int = 10
    search_multiplier: int = 1
    min_score: float = 0.0
    port: int = 25000


def _read_events(path: Path) -> list[dict[str, Any]]:
    if path.suffix.casefold() == ".jsonl":
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    payload = json.loads(path.read_text(encoding="utf-8"))
    events = payload.get("events") if isinstance(payload, dict) else None
    if not isinstance(events, list):
        raise ValueError(f"Context has no events list: {path}")
    return events


def _safe_fragment(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]


def _visible_d08_events(case: dict[str, Any], events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    identity = case["envelope"]["identity"]
    user_id = identity.get("user_id")
    tenant_id = identity.get("tenant_id")
    if not user_id or not tenant_id:
        raise ValueError("D08 Case identity must declare user_id and tenant_id")
    visible = []
    for event in events:
        metadata = event.get("metadata")
        if not isinstance(metadata, dict):
            continue
        if metadata.get("user_id") == user_id and metadata.get("tenant_id") == tenant_id:
            visible.append(event)
    if not visible:
        raise ValueError("D08 Case has no Context events visible to its declared identity")
    return visible


def _prepare_case_input(
    artifact: ReviewedCaseArtifact,
    input_root: Path,
) -> tuple[dict[str, Any], Path, list[dict[str, Any]]]:
    events = _read_events(artifact.context_path)
    if artifact.dimension_id != "D08":
        return artifact.case, artifact.context_path, events

    visible = _visible_d08_events(artifact.case, events)
    case = deepcopy(artifact.case)
    case["envelope"]["context"]["event_count"] = len(visible)
    input_root.mkdir(parents=True, exist_ok=True)
    context_path = input_root / f"{_safe_fragment(case['envelope']['case_id'])}.json"
    context_path.write_text(json.dumps({"events": visible}, ensure_ascii=False), encoding="utf-8")
    return case, context_path, visible


def _operation_payload(result: SystemOperationResult) -> dict[str, Any]:
    return {"status": result.status, "data": result.data, "reason": result.reason}


def _unsupported(reason: str) -> SystemOperationResult:
    return SystemOperationResult("unsupported", reason=reason)


def _enrich_memories(runtime: Any, memories: list[dict[str, Any]]) -> list[dict[str, Any]]:
    sessions = {item["session_id"]: item for item in runtime.canonical_case.get("sessions", [])}
    output = []
    for memory in memories:
        row = deepcopy(memory)
        session = sessions.get(str(memory.get("session_id")), {})
        row["source_memory_ids"] = sorted(
            {str(message["memory_id"]) for message in session.get("messages", []) if message.get("memory_id")}
        )
        row["event_ids"] = [
            str(message["event_id"]) for message in session.get("messages", []) if message.get("event_id")
        ]
        output.append(row)
    return output


def _retrieval_metrics(runtime: Any, memories: list[dict[str, Any]]) -> dict[str, Any]:
    gold = list(dict.fromkeys(runtime.canonical_case.get("evidence_session_ids", [])))
    retrieved = [str(item.get("session_id")) for item in memories if item.get("session_id")]
    if not gold:
        return {"retrieval_evaluated": False, "hit_at_k": None, "recall_at_k": None, "mrr": None}
    gold_set = set(gold)
    overlap = gold_set.intersection(retrieved)
    first_rank = next((rank for rank, value in enumerate(retrieved, 1) if value in gold_set), None)
    return {
        "retrieval_evaluated": True,
        "hit_at_k": float(bool(overlap)),
        "recall_at_k": len(overlap) / len(gold_set),
        "mrr": 1.0 / first_rank if first_rank else 0.0,
    }


def _written_event_metrics(case: dict[str, Any], operation: SystemOperationResult) -> dict[str, Any]:
    if operation.status != "ok":
        return {}
    rows = operation.data if isinstance(operation.data, list) else []
    written = {str(value) for row in rows for value in row.get("event_ids", [])}
    expected = {str(value) for value in case["gold"]["payload"].get("scored_event_ids", [])}
    return {
        "write_event_recall": len(written.intersection(expected)) / len(expected) if expected else None,
        "written_memory_units": len(rows),
        "semantic_memory_precision": None,
        "semantic_memory_recall": None,
    }


def _privacy_metrics(case: dict[str, Any], memories: list[dict[str, Any]]) -> dict[str, Any]:
    payload = case["gold"]["payload"]
    retrieved_ids = {value for item in memories for value in item.get("source_memory_ids", [])}
    allowed = set(payload.get("allowed_memory_ids", []))
    forbidden = set(payload.get("forbidden_memory_ids", []))
    deleted = set(payload.get("deleted_memory_ids", []))
    text = json.dumps(memories, ensure_ascii=False)
    exposed_canaries = [token for token in payload.get("canary_tokens", []) if token in text]
    prohibited = retrieved_ids.intersection(forbidden | deleted)
    return {
        "allowed_recall": len(retrieved_ids.intersection(allowed)) / len(allowed) if allowed else None,
        "forbidden_exposure_count": len(retrieved_ids.intersection(forbidden)),
        "deleted_exposure_count": len(retrieved_ids.intersection(deleted)),
        "canary_exposure_count": len(exposed_canaries),
        "privacy_pass": float(not prohibited and not exposed_canaries),
    }


class MemEvalRunner:
    """Run frozen Cases sequentially and preserve one result for every Case."""

    def __init__(self, system: SystemAdapter, workspace_root: str | Path) -> None:
        self.system = system
        self.workspace_root = Path(workspace_root).resolve()

    def _namespace(self, case: dict[str, Any], config: MemEvalRunConfig) -> str:
        envelope = case["envelope"]
        identity = envelope["identity"]
        return ":".join(
            str(value or "none")
            for value in (
                config.dataset_id, config.run_id, envelope["case_id"],
                identity.get("tenant_id"), identity.get("user_id"),
            )
        )

    def _dimension_action(
        self,
        runtime: Any,
        case: dict[str, Any],
        events: list[dict[str, Any]],
        config: MemEvalRunConfig,
    ) -> tuple[Any, list[dict[str, Any]], dict[str, Any], str, list[str], float | None]:
        dimension = case["envelope"]["dimension_id"]
        query = str(case["envelope"]["query"]["text"])
        unsupported_metrics: list[str] = []
        prediction: Any = None
        memories: list[dict[str, Any]] = []
        retrieval_ms: float | None = None

        if dimension == "D01":
            operation = self.system.list_memories(runtime)
            prediction = _operation_payload(operation)
            metrics = _written_event_metrics(case, operation)
            unsupported_metrics.extend(["semantic_memory_precision", "semantic_memory_recall"])
            return prediction, memories, metrics, "partial" if operation.status == "ok" else "unsupported", unsupported_metrics, None

        if dimension == "D04":
            operation = (
                self.system.get_trace(runtime)
                if self.system.capabilities.activation_trace
                else _unsupported("System does not expose activation_trace")
            )
            return _operation_payload(operation), memories, {}, operation.status, ["activation_decision"], None

        if dimension == "D05":
            operation = (
                self.system.get_profile(runtime)
                if self.system.capabilities.profile
                else _unsupported("System does not expose profiles")
            )
            return _operation_payload(operation), memories, {}, operation.status, ["profile_accuracy"], None

        if dimension == "D08" and not self.system.capabilities.user_isolation:
            operation = _unsupported("System does not isolate user namespaces")
            return _operation_payload(operation), memories, {}, "unsupported", ["privacy"], None

        if not self.system.capabilities.retrieval:
            operation = _unsupported("System does not support retrieval")
            return _operation_payload(operation), memories, {}, "unsupported", ["retrieval"], None

        if dimension == "D08":
            delete_ids = [
                str(event["metadata"]["target_memory_id"])
                for event in events
                if isinstance(event.get("metadata"), dict)
                and event["metadata"].get("operation") == "delete"
            ]
            if delete_ids:
                if not self.system.capabilities.delete:
                    operation = _unsupported("System does not support deletion")
                    return _operation_payload(operation), memories, {}, "unsupported", ["deletion"], None
                self.system.delete(runtime, memory_ids=delete_ids)

        search = self.system.search(
            runtime,
            query=query,
            top_k=config.top_k,
            search_multiplier=config.search_multiplier,
            min_score=config.min_score,
        )
        memories = _enrich_memories(runtime, search.memories)
        retrieval_ms = search.latency_ms

        if dimension == "D08":
            return None, memories, _privacy_metrics(case, memories), "ok", [], retrieval_ms

        metrics = _retrieval_metrics(runtime, memories)
        if dimension == "D02":
            return None, memories, metrics, "ok", [], retrieval_ms

        answer = self.system.query(runtime, query=query)
        prediction = _operation_payload(answer)
        if answer.status == "unsupported":
            unsupported_metrics.append("answer_accuracy")
            return prediction, memories, metrics, "partial", unsupported_metrics, retrieval_ms
        return prediction, memories, metrics, "ok", unsupported_metrics, retrieval_ms

    def run_case(self, artifact: ReviewedCaseArtifact, config: MemEvalRunConfig) -> dict[str, Any]:
        case_id = str(artifact.case["envelope"]["case_id"])
        context_id = str(artifact.case["envelope"]["identity"]["context_id"])
        started = time.perf_counter()
        runtime = None
        runner_trace: list[dict[str, Any]] = []
        input_root = self.workspace_root / "_runner_inputs" / _safe_fragment(config.run_id)
        metadata = self.system.run_metadata()
        result = {
            "run_id": config.run_id,
            "case_id": case_id,
            "context_id": context_id,
            "dimension_id": artifact.dimension_id,
            "system": self.system.name,
            "system_version": metadata.get("memory_version", metadata.get("system_version")),
            "run_mode": "case_isolated",
            "prediction": None,
            "retrieved_memories": [],
            "trace": {},
            "latency": {"ingest": None, "retrieval": None, "answer": None, "total": None},
            "cost": {"input_tokens": None, "output_tokens": None, "api_cost": None},
            "metrics": {},
            "unsupported_metrics": [],
            "status": "error",
            "error": None,
        }
        try:
            case, context_path, events = _prepare_case_input(artifact, input_root)
            (self.workspace_root / "logs").mkdir(parents=True, exist_ok=True)
            runtime = self.system.create_namespace(
                namespace=self._namespace(case, config),
                workspace=self.workspace_root / "namespaces",
                case=case,
                context_path=context_path,
                dataset_id=config.dataset_id,
                port=config.port,
                service_log_path=self.workspace_root / "logs" / f"{_safe_fragment(case_id)}.log",
            )
            runner_trace.append({"stage": "load_context", "status": "ok", "event_count": len(events)})
            ingest = self.system.ingest(runtime)
            runner_trace.append({"stage": "ingest", "status": "ok", "failures": len(ingest.failures)})
            if ingest.failures:
                raise RuntimeError(f"System ingest returned {len(ingest.failures)} failures")
            prediction, memories, metrics, status, unsupported, retrieval_ms = self._dimension_action(
                runtime, case, events, config
            )
            runner_trace.append({"stage": "dimension_action", "status": status})
            stats = self.system.get_stats(runtime)
            system_trace = self.system.get_trace(runtime)
            result.update(
                prediction=prediction,
                retrieved_memories=memories,
                trace={"runner": runner_trace, "system": _operation_payload(system_trace)},
                latency={
                    "ingest": ingest.latency_ms,
                    "retrieval": retrieval_ms,
                    "answer": None,
                    "total": (time.perf_counter() - started) * 1000,
                },
                metrics=metrics,
                unsupported_metrics=unsupported,
                status=status,
            )
            if stats.status == "ok" and isinstance(stats.data, dict):
                cost = stats.data.get("cost")
                if isinstance(cost, dict):
                    result["cost"] = {
                        "input_tokens": cost.get("input_tokens"),
                        "output_tokens": cost.get("output_tokens"),
                        "api_cost": cost.get("api_cost"),
                    }
        except Exception as exc:
            runner_trace.append({"stage": "error", "status": "error", "type": type(exc).__name__})
            result["error"] = {"type": type(exc).__name__, "message": str(exc)}
            result["trace"] = {"runner": runner_trace}
            result["latency"]["total"] = (time.perf_counter() - started) * 1000
        finally:
            if runtime is not None:
                try:
                    self.system.cleanup(runtime)
                except Exception as exc:
                    result["status"] = "error"
                    cleanup_error = {"type": type(exc).__name__, "message": str(exc)}
                    if result["error"] is None:
                        result["error"] = {"type": type(exc).__name__, "message": f"cleanup: {exc}"}
                    else:
                        result["error"]["cleanup"] = cleanup_error
            if artifact.dimension_id == "D08":
                input_path = input_root / f"{_safe_fragment(case_id)}.json"
                input_path.unlink(missing_ok=True)
                for directory in (input_root, input_root.parent):
                    try:
                        directory.rmdir()
                    except (FileNotFoundError, OSError):
                        pass
        return result

    def run(
        self,
        artifacts: Iterable[ReviewedCaseArtifact],
        config: MemEvalRunConfig,
        output_path: str | Path,
    ) -> list[dict[str, Any]]:
        if config.top_k < 1:
            raise ValueError("top_k must be positive")
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        results = []
        with output.open("w", encoding="utf-8", newline="\n") as handle:
            for artifact in artifacts:
                result = self.run_case(artifact, config)
                results.append(result)
                handle.write(json.dumps(result, ensure_ascii=False) + "\n")
                handle.flush()
        return results
