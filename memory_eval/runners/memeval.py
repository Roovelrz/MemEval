"""Dimension-aware runner for the frozen MemEval benchmark."""

from __future__ import annotations

import hashlib
import json
import time
from collections import Counter
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable

from dataset.build_pipeline.release import ReviewedCaseArtifact
from memory_eval.progress import ProgressReporter
from memory_eval.systems import SystemAdapter, SystemOperationResult

from .context_cache import ContextCache


@dataclass(frozen=True)
class MemEvalRunConfig:
    run_id: str
    dataset_id: str = "MemEval-v0.1"
    top_k: int = 10
    search_multiplier: int = 1
    min_score: float = 0.0
    port: int = 25000
    reuse_context: bool = False


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


def _retrieval_status(result: dict[str, Any]) -> str:
    explicit = result.get("retrieval_status")
    if isinstance(explicit, str):
        return explicit
    trace = result.get("trace")
    runner = trace.get("runner") if isinstance(trace, dict) else None
    if isinstance(runner, list):
        for stage in reversed(runner):
            if isinstance(stage, dict) and stage.get("stage") == "dimension_action":
                return str(stage.get("status", "error"))
    return str(result.get("status", "error"))


def _d08_execution_identity(
    case: dict[str, Any], events: list[dict[str, Any]]
) -> dict[str, Any]:
    declared = case["envelope"]["identity"]
    scenario = case["envelope"].get("metadata", {}).get("scenario_type")
    if scenario != "deletion":
        return declared

    delete_events = [
        event
        for event in events
        if isinstance(event.get("metadata"), dict)
        and event["metadata"].get("operation") == "delete"
    ]
    target_ids = {
        str(event["metadata"].get("target_memory_id"))
        for event in delete_events
        if event["metadata"].get("target_memory_id")
    }
    lifecycle_events = [
        event
        for event in events
        if isinstance(event.get("metadata"), dict)
        and (
            event["metadata"].get("operation") == "delete"
            or str(event["metadata"].get("memory_id")) in target_ids
        )
    ]
    identities = {
        (event["metadata"].get("user_id"), event["metadata"].get("tenant_id"))
        for event in lifecycle_events
    }
    if not target_ids or len(lifecycle_events) < 2 or len(identities) != 1:
        raise ValueError(
            "D08 deletion Context must declare one execution identity for its write/delete lifecycle"
        )
    user_id, tenant_id = next(iter(identities))
    if not user_id or not tenant_id:
        raise ValueError("D08 deletion execution identity must declare user_id and tenant_id")
    return {**declared, "user_id": user_id, "tenant_id": tenant_id}


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

    case = deepcopy(artifact.case)
    case["envelope"]["identity"] = _d08_execution_identity(case, events)
    visible = _visible_d08_events(case, events)
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


def _evidence_session_ids(case: dict[str, Any], runtime: Any) -> list[str]:
    dimension = case["envelope"]["dimension_id"]
    payload = case["gold"]["payload"]
    if dimension in {"D02", "D07"}:
        references = payload.get("gold_evidence_ids", [])
    elif dimension == "D03":
        references = payload.get("evidence_event_ids", [])
    elif dimension == "D05":
        references = [
            event_id
            for item in payload.get("profile_items", [])
            for event_id in item.get("evidence_event_ids", [])
        ]
    elif dimension == "D06":
        references = payload.get("winning_fact_ids", [])
    else:
        references = []
    session_ids = {str(item["session_id"]) for item in runtime.canonical_case.get("sessions", [])}
    output = []
    for reference in references:
        value = str(reference)
        session_id = runtime.event_to_session_id.get(value) or runtime.memory_to_session_id.get(value)
        if session_id is None and value in session_ids:
            session_id = value
        if session_id is None and dimension == "D06" and len(session_ids) == 1:
            session_id = next(iter(session_ids))
        if session_id is not None and session_id not in output:
            output.append(session_id)
    return output


def _normalise_text(value: Any) -> str:
    return " ".join(str(value or "").casefold().split())


def _conflict_metrics(case: dict[str, Any], memories: list[dict[str, Any]]) -> dict[str, Any]:
    """D06: whether stale / winning fact values surface in retrieved memory text."""

    payload = case["gold"]["payload"]
    versions = payload.get("fact_versions") or []
    if not versions:
        return {}
    stale_ids = {str(value) for value in payload.get("stale_fact_ids", [])}
    winning_ids = {str(value) for value in payload.get("winning_fact_ids", [])}
    retrieved_text = _normalise_text(" ".join(str(item.get("text", "")) for item in memories))

    def hit_rate(rows: list[dict[str, Any]]) -> float | None:
        values = [_normalise_text(row.get("value")) for row in rows]
        values = [value for value in values if value]
        if not values:
            return None
        return sum(1 for value in values if value in retrieved_text) / len(values)

    stale_rows = [row for row in versions if str(row.get("fact_id")) in stale_ids]
    winning_rows = [row for row in versions if str(row.get("fact_id")) in winning_ids]
    return {
        "stale_fact_total": len(stale_rows),
        "stale_retrieval_rate": hit_rate(stale_rows),
        "winning_fact_total": len(winning_rows),
        "winning_fact_recall": hit_rate(winning_rows),
    }


def _temporal_metrics(case: dict[str, Any], runtime: Any, memories: list[dict[str, Any]]) -> dict[str, Any]:
    """D03: deleted-fact recall, only defined for lifecycle Cases (expected_active=False)."""

    payload = case["gold"]["payload"]
    lifecycle = payload.get("lifecycle") or {}
    if lifecycle.get("expected_active") is not False:
        return {}
    evidence_sessions = set(_evidence_session_ids(case, runtime))
    retrieved_sessions = {str(item.get("session_id")) for item in memories if item.get("session_id")}
    deleted_hit = bool(evidence_sessions & retrieved_sessions) if evidence_sessions else None
    return {"lifecycle_case": True, "deleted_hit": deleted_hit}


def _retrieval_metrics(
    case: dict[str, Any], runtime: Any, memories: list[dict[str, Any]]
) -> dict[str, Any]:
    gold = _evidence_session_ids(case, runtime)
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
    correct = written.intersection(expected)
    return {
        "write_event_precision": len(correct) / len(written) if written else None,
        "write_event_recall": len(correct) / len(expected) if expected else None,
        "unexpected_written_event_count": len(written - expected),
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

    def _new_result(
        self, artifact: ReviewedCaseArtifact, config: MemEvalRunConfig, run_mode: str
    ) -> dict[str, Any]:
        envelope = artifact.case["envelope"]
        metadata = self.system.run_metadata()
        return {
            "run_id": config.run_id,
            "case_id": str(envelope["case_id"]),
            "context_id": str(envelope["identity"]["context_id"]),
            "dimension_id": artifact.dimension_id,
            "system": self.system.name,
            "system_version": metadata.get("memory_version", metadata.get("system_version")),
            "run_mode": run_mode,
            "reuse_context": run_mode == "context_batch",
            "context_cache": None,
            "prediction": None,
            "retrieved_memories": [],
            "trace": {},
            "latency": {"ingest": None, "retrieval": None, "answer": None, "total": None},
            "cost": {"input_tokens": None, "output_tokens": None, "api_cost": None},
            "cost_scope": "case" if run_mode == "case_isolated" else "context_batch_cumulative",
            "metrics": {},
            "unsupported_metrics": [],
            "status": "error",
            "error": None,
        }

    def _complete_result(
        self,
        result: dict[str, Any],
        runtime: Any,
        case: dict[str, Any],
        events: list[dict[str, Any]],
        config: MemEvalRunConfig,
        runner_trace: list[dict[str, Any]],
        started: float,
        ingest_latency: float | None,
    ) -> None:
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
                "ingest": ingest_latency,
                "retrieval": retrieval_ms,
                "answer": None,
                "total": (time.perf_counter() - started) * 1000,
            },
            metrics=metrics,
            unsupported_metrics=unsupported,
            status=status,
            retrieval_status=status,
        )
        if stats.status == "ok" and isinstance(stats.data, dict):
            cost = stats.data.get("cost")
            if isinstance(cost, dict):
                result["cost"] = {
                    "input_tokens": cost.get("input_tokens"),
                    "output_tokens": cost.get("output_tokens"),
                    "api_cost": cost.get("api_cost"),
                }

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
            if not self.system.capabilities.retrieval:
                return (
                    _operation_payload(operation), memories, {}, operation.status,
                    ["profile_accuracy", "personalized_answer_accuracy"], None,
                )
            search = self.system.search(
                runtime,
                query=query,
                top_k=config.top_k,
                search_multiplier=config.search_multiplier,
                min_score=config.min_score,
            )
            memories = _enrich_memories(runtime, search.memories)
            metrics = _retrieval_metrics(case, runtime, memories)
            return (
                _operation_payload(operation), memories, metrics,
                "partial" if operation.status == "unsupported" else operation.status,
                ["profile_accuracy", "personalized_answer_accuracy"], search.latency_ms,
            )

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

        metrics = _retrieval_metrics(case, runtime, memories)
        if dimension == "D03":
            metrics.update(_temporal_metrics(case, runtime, memories))
        elif dimension == "D06":
            metrics.update(_conflict_metrics(case, memories))
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
        started = time.perf_counter()
        runtime = None
        runner_trace: list[dict[str, Any]] = []
        input_root = self.workspace_root / "_runner_inputs" / _safe_fragment(config.run_id)
        result = self._new_result(artifact, config, "case_isolated")
        result["context_cache"] = {
            "hit": False, "context_sha256": None,
            "ingest_owner_case_id": case_id, "query_index": 1, "query_count": 1,
        }
        try:
            case, context_path, events = _prepare_case_input(artifact, input_root)
            result["context_cache"]["context_sha256"] = hashlib.sha256(
                context_path.read_bytes()
            ).hexdigest()
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
            self._complete_result(
                result, runtime, case, events, config, runner_trace, started, ingest.latency_ms
            )
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

    def _run_context_batch(
        self,
        artifacts: list[ReviewedCaseArtifact],
        config: MemEvalRunConfig,
        on_result: Callable[[dict[str, Any]], None] | None = None,
    ) -> list[dict[str, Any]]:
        groups = ContextCache().group(artifacts)
        results: list[dict[str, Any]] = []
        input_root = self.workspace_root / "_runner_inputs" / _safe_fragment(config.run_id)
        (self.workspace_root / "logs").mkdir(parents=True, exist_ok=True)

        for group in groups:
            owner = group.artifacts[0]
            owner_id = str(owner.case["envelope"]["case_id"])
            runtime = None
            prepared_path: Path | None = None
            group_results: list[dict[str, Any]] = []
            group_started = time.perf_counter()
            try:
                owner_case, context_path, events = _prepare_case_input(owner, input_root)
                prepared_path = context_path if owner.dimension_id == "D08" else None
                runtime = self.system.create_namespace(
                    namespace=self._namespace(owner_case, config),
                    workspace=self.workspace_root / "namespaces",
                    case=owner_case,
                    context_path=context_path,
                    dataset_id=config.dataset_id,
                    port=config.port,
                    service_log_path=self.workspace_root / "logs" / f"{_safe_fragment(owner_id)}.log",
                )
                ingest = self.system.ingest(runtime)
                if ingest.failures:
                    raise RuntimeError(f"System ingest returned {len(ingest.failures)} failures")

                for index, artifact in enumerate(group.artifacts, 1):
                    started = group_started if index == 1 else time.perf_counter()
                    result = self._new_result(artifact, config, "context_batch")
                    result["context_cache"] = {
                        "hit": index > 1,
                        "context_sha256": group.context_sha256,
                        "ingest_owner_case_id": owner_id,
                        "query_index": index,
                        "query_count": len(group.artifacts),
                    }
                    trace = [
                        {"stage": "load_context", "status": "ok", "event_count": len(events),
                         "cache_hit": index > 1},
                        {"stage": "ingest", "status": "reused" if index > 1 else "ok",
                         "failures": 0},
                    ]
                    try:
                        case = owner_case if artifact is owner else artifact.case
                        self._complete_result(
                            result, runtime, case, events, config, trace, started,
                            None if index > 1 else ingest.latency_ms,
                        )
                    except Exception as exc:
                        trace.append({"stage": "error", "status": "error", "type": type(exc).__name__})
                        result["error"] = {"type": type(exc).__name__, "message": str(exc)}
                        result["trace"] = {"runner": trace}
                        result["latency"]["total"] = (time.perf_counter() - started) * 1000
                    group_results.append(result)
            except Exception as exc:
                for index, artifact in enumerate(group.artifacts, 1):
                    result = self._new_result(artifact, config, "context_batch")
                    result["context_cache"] = {
                        "hit": False,
                        "context_sha256": group.context_sha256,
                        "ingest_owner_case_id": owner_id,
                        "query_index": index,
                        "query_count": len(group.artifacts),
                    }
                    result["error"] = {"type": type(exc).__name__, "message": str(exc)}
                    result["trace"] = {"runner": [{"stage": "ingest", "status": "error"}]}
                    result["latency"]["total"] = (time.perf_counter() - group_started) * 1000
                    group_results.append(result)
            finally:
                if runtime is not None:
                    try:
                        self.system.cleanup(runtime)
                    except Exception as exc:
                        target = group_results[-1]
                        target["status"] = "error"
                        target["error"] = {
                            "type": type(exc).__name__, "message": f"cleanup: {exc}"
                        }
                if prepared_path is not None:
                    prepared_path.unlink(missing_ok=True)
                    for directory in (input_root, input_root.parent):
                        try:
                            directory.rmdir()
                        except (FileNotFoundError, OSError):
                            pass
            results.extend(group_results)
            if on_result is not None:
                for result in group_results:
                    on_result(result)
        return results

    def _write_summary(
        self,
        results: list[dict[str, Any]],
        config: MemEvalRunConfig,
        output: Path,
        wall_latency_ms: float,
        *,
        resume_enabled: bool = False,
        resumed_case_count: int = 0,
        executed_case_count: int | None = None,
    ) -> Path:
        dimensions = {}
        for dimension_id in sorted({row["dimension_id"] for row in results}):
            rows = [row for row in results if row["dimension_id"] == dimension_id]
            metric_names = sorted({name for row in rows for name in row["metrics"]})
            dimensions[dimension_id] = {
                "case_count": len(rows),
                "status_counts": dict(Counter(row["status"] for row in rows)),
                "metrics": {
                    name: (
                        sum(values) / len(values) if (values := [
                            float(row["metrics"][name]) for row in rows
                            if isinstance(row["metrics"].get(name), (int, float))
                        ]) else None
                    )
                    for name in metric_names
                },
                "unsupported_metric_counts": dict(Counter(
                    name for row in rows for name in row["unsupported_metrics"]
                )),
            }
        summary = {
            "schema_version": "memeval_run_summary_v1",
            "run_id": config.run_id,
            "dataset_id": config.dataset_id,
            "system": self.system.name,
            "system_version": self.system.run_metadata().get("memory_version"),
            "run_mode": "context_batch" if config.reuse_context else "case_isolated",
            "reuse_context": config.reuse_context,
            "top_k": config.top_k,
            "search_multiplier": config.search_multiplier,
            "min_score": config.min_score,
            "case_count": len(results),
            "context_count": len({row["context_id"] for row in results}),
            "ingest_count": sum(
                1 for row in results if not (row.get("context_cache") or {}).get("hit", False)
            ),
            "status_counts": dict(Counter(row["status"] for row in results)),
            "dimensions": dimensions,
            "system_metadata": self.system.run_metadata(),
            "wall_latency_ms": wall_latency_ms,
            "results_path": str(output.resolve()),
            "resume": {
                "enabled": resume_enabled,
                "resumed_case_count": resumed_case_count,
                "executed_case_count": (
                    len(results) if executed_case_count is None else executed_case_count
                ),
            },
        }
        path = output.with_name("run_summary.json")
        path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return path

    def run(
        self,
        artifacts: Iterable[ReviewedCaseArtifact],
        config: MemEvalRunConfig,
        output_path: str | Path,
        *,
        resume: bool = False,
    ) -> list[dict[str, Any]]:
        if config.top_k < 1:
            raise ValueError("top_k must be positive")
        rows = list(artifacts)
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        started = time.perf_counter()
        selected_ids = [str(row.case["envelope"]["case_id"]) for row in rows]
        if len(selected_ids) != len(set(selected_ids)):
            raise ValueError("MemEval selection contains duplicate case IDs")

        existing_rows: list[dict[str, Any]] = []
        if resume and output.is_file():
            for line_number, line in enumerate(
                output.read_text(encoding="utf-8").splitlines(), start=1
            ):
                if not line.strip():
                    continue
                try:
                    value = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise ValueError(
                        f"Cannot resume invalid JSONL at {output}:{line_number}: {exc}"
                    ) from exc
                if not isinstance(value, dict):
                    raise ValueError(f"Cannot resume non-object row at {output}:{line_number}")
                existing_rows.append(value)

        expected_mode = "context_batch" if config.reuse_context else "case_isolated"
        for result in existing_rows:
            if result.get("run_id") != config.run_id:
                raise ValueError("Cannot resume results written by a different run_id")
            if result.get("run_mode") != expected_mode:
                raise ValueError("Cannot resume with a different context-batch mode")
            result.setdefault("retrieval_status", _retrieval_status(result))

        latest_by_id = {
            str(result.get("case_id")): result
            for result in existing_rows
            if result.get("case_id") is not None
        }
        completed_ids = {
            case_id
            for case_id in selected_ids
            if case_id in latest_by_id and _retrieval_status(latest_by_id[case_id]) != "error"
        }
        pending = [
            artifact
            for artifact in rows
            if str(artifact.case["envelope"]["case_id"]) not in completed_ids
        ]
        progress = ProgressReporter("Retrieval", len(rows), completed=len(completed_ids))

        mode = "a" if resume and output.is_file() else "w"
        try:
            with output.open(mode, encoding="utf-8", newline="\n") as handle:
                def persist(result: dict[str, Any]) -> None:
                    handle.write(json.dumps(result, ensure_ascii=False) + "\n")
                    handle.flush()
                    progress.advance(
                        item_id=str(result["case_id"]), status=str(result.get("status", "unknown"))
                    )

                if config.reuse_context:
                    self._run_context_batch(pending, config, on_result=persist)
                else:
                    for artifact in pending:
                        persist(self.run_case(artifact, config))
        finally:
            progress.close()

        # Keep exactly one latest row per selected Case after a successful invocation.
        latest_by_id = {
            str(result["case_id"]): result
            for result in (
                json.loads(line)
                for line in output.read_text(encoding="utf-8").splitlines()
                if line.strip()
            )
        }
        results = [latest_by_id[case_id] for case_id in selected_ids]
        for result in results:
            result.setdefault("retrieval_status", _retrieval_status(result))
        with output.open("w", encoding="utf-8", newline="\n") as handle:
            for result in results:
                handle.write(json.dumps(result, ensure_ascii=False) + "\n")
        self._write_summary(
            results,
            config,
            output,
            (time.perf_counter() - started) * 1000,
            resume_enabled=resume,
            resumed_case_count=len(completed_ids),
            executed_case_count=len(pending),
        )
        return results
