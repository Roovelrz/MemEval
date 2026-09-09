"""Adapt MemEval runner results to the existing Trace Dashboard artifacts."""

from __future__ import annotations

import json
import math
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from dataset.build_pipeline.release import ReviewedCaseArtifact
from memory_eval.systems import build_reme_case
from memory_eval.trace_report import (
    NOT_APPLICABLE,
    NOT_RECORDED,
    _case_analysis,
    _render_case,
    _render_index,
    _render_judge_review,
    _render_summary,
    _summary,
)


ANSWER_DIMENSIONS = frozenset({"D02", "D03", "D05", "D06", "D07"})
RETRIEVAL_DIMENSIONS = frozenset({"D02", "D03", "D05", "D06", "D07", "D08"})

DIMENSION_METRIC_AUDIT = {
    "D01": {
        "document_metrics": ["Write Precision", "Write Recall"],
        "trace_fields": ["write_event_precision", "write_event_recall"],
        "coverage": "ADAPTED",
        "note": "Write Precision 当前按事件 ID 对齐计算；语义内容精确率仍为 NOT_RECORDED。",
    },
    "D02": {
        "document_metrics": ["Hit@K", "Recall@K", "MRR"],
        "trace_fields": ["hit_at_k", "recall_at_k", "mrr"],
        "coverage": "EXISTING",
        "note": "三个指标均已从 Eval 结果流入 Trace 和 Dashboard。",
    },
    "D03": {
        "document_metrics": ["Temporal Accuracy", "Retention Recall", "Deleted Hit Rate"],
        "trace_fields": ["answer_accuracy", "recall_at_k", "deleted_hit_rate"],
        "coverage": "ADAPTED",
        "note": "答案准确率近似 Temporal Accuracy，检索召回率近似 Long-gap Recall；Deleted Hit Rate 已按 lifecycle Case 聚合（ReMe 不执行内容删除，测陈旧残留）。",
    },
    "D04": {
        "document_metrics": ["Activation Recall", "Utilization Rate", "E2E Accuracy"],
        "trace_fields": ["activation_decision", "should_activate"],
        "coverage": "ADAPTED_UNSUPPORTED",
        "note": "ReMe 当前不暴露主动调用轨迹；Answer/Judge 指标为 NOT_APPLICABLE。",
    },
    "D05": {
        "document_metrics": ["Profile Precision", "Preference Recall", "Profile Consistency"],
        "trace_fields": ["recall_at_k", "personalized_answer_accuracy"],
        "missing_metrics": ["profile_precision", "profile_consistency"],
        "coverage": "PARTIAL",
        "note": "已有 Evidence 召回率和个性化答案准确率；ReMe 当前不提供画像快照。",
    },
    "D06": {
        "document_metrics": ["Latest-value", "Conflict Resolution", "Stale Retrieval"],
        "trace_fields": ["answer_accuracy", "stale_retrieval_rate", "winning_fact_recall"],
        "coverage": "ADAPTED",
        "note": "Judge 准确率覆盖最新值判断；Stale Retrieval 与 Winning Recall 按事实文本在检索结果中的出现计算。",
    },
    "D07": {
        "document_metrics": ["Recall Degradation", "P95 Retrieval Latency", "Cost"],
        "trace_fields": ["recall_at_k", "recall_degradation", "p95_search_latency_ms", "cost"],
        "coverage": "ADAPTED",
        "note": "Recall Degradation 已按同 scale_group 的 100K 与 10M 配对聚合；P95 检索时延与成本已记录。",
    },
    "D08": {
        "document_metrics": ["Sensitive Exposure", "Cross-user Leakage"],
        "trace_fields": ["canary_exposure_count", "forbidden_exposure_count"],
        "coverage": "ADAPTED",
        "note": "复用已有的敏感词、跨用户禁止记忆和已删除记忆暴露计数。",
    },
}


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return value


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    rows = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"Expected JSON object at {path}:{line_number}")
        rows.append(value)
    return rows


def _write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def _row_map(path: Path) -> dict[str, dict[str, Any]]:
    output = {}
    for row in _read_jsonl(path):
        ident = str(row.get("id", row.get("case_id", "")))
        if not ident:
            raise ValueError(f"Trace row has no ID: {path}")
        if ident in output:
            raise ValueError(f"Duplicate Trace row ID {ident!r}: {path}")
        output[ident] = row
    return output


def _mean(values: Iterable[Any]) -> float | None:
    usable = [float(value) for value in values if isinstance(value, (int, float))]
    return sum(usable) / len(usable) if usable else None


def _p95(values: Iterable[Any]) -> float | None:
    rows = sorted(float(value) for value in values if isinstance(value, (int, float)))
    if not rows:
        return None
    index = min(len(rows) - 1, max(0, math.ceil(0.95 * len(rows)) - 1))
    return rows[index]


def _safe_name(value: str) -> str:
    cleaned = "".join(char if char.isalnum() or char in "._-" else "_" for char in value)
    return cleaned.strip("._") or "unnamed"


class MemEvalTraceAdapter:
    """Build legacy-compatible Trace inputs plus MemEval-specific detail."""

    def __init__(
        self,
        benchmark_root: str | Path,
        artifacts: Iterable[ReviewedCaseArtifact],
        run_dir: str | Path,
        *,
        top_k: int,
        answer_api_key_env: str = "DEEPSEEK_API_KEY",
        answer_base_url_env: str = "DEEPSEEK_BASE_URL",
        answer_model_env: str = "DEEPSEEK_MODEL",
        judge_api_key_env: str = "DEEPSEEK_API_KEY",
        judge_base_url_env: str = "DEEPSEEK_BASE_URL",
        judge_model_env: str = "DEEPSEEK_MODEL",
    ) -> None:
        self.benchmark_root = Path(benchmark_root).resolve()
        self.run_dir = Path(run_dir).resolve()
        self.top_k = top_k
        self.answer_env = {
            "api_key_env": answer_api_key_env,
            "base_url_env": answer_base_url_env,
            "model_env": answer_model_env,
        }
        self.judge_env = {
            "api_key_env": judge_api_key_env,
            "base_url_env": judge_base_url_env,
            "model_env": judge_model_env,
        }
        self.artifacts = {
            str(artifact.case["envelope"]["case_id"]): artifact for artifact in artifacts
        }
        if not self.artifacts:
            raise ValueError("MemEval Trace Adapter requires at least one Case")

    @staticmethod
    def _gold_answer(artifact: ReviewedCaseArtifact) -> Any | None:
        payload = artifact.case["gold"]["payload"]
        if "gold_answer" not in payload:
            return None
        value = payload["gold_answer"]
        return None if value is None or (isinstance(value, str) and not value.strip()) else value

    @staticmethod
    def _system_events(result: dict[str, Any]) -> list[dict[str, Any]]:
        trace = result.get("trace")
        system = trace.get("system") if isinstance(trace, dict) else None
        data = system.get("data") if isinstance(system, dict) else None
        events = data.get("events") if isinstance(data, dict) else None
        return [event for event in events if isinstance(event, dict)] if isinstance(events, list) else []

    def _prepared_row(
        self,
        artifact: ReviewedCaseArtifact,
        result: dict[str, Any],
        canonical: dict[str, Any],
    ) -> dict[str, Any]:
        memories = result.get("retrieved_memories", [])
        contexts = [
            (
                f'<memory rank="{memory.get("rank", index)}" '
                f'session_id="{memory.get("session_id", "")}" '
                f'score="{memory.get("score", "")}">\n'
                f'{memory.get("text", "")}\n</memory>'
            )
            for index, memory in enumerate(memories, 1)
            if isinstance(memory, dict)
        ]
        gold_answer = self._gold_answer(artifact)
        return {
            "id": canonical["case_id"],
            "case_id": canonical["case_id"],
            "dimension_id": artifact.dimension_id,
            "question_type": artifact.dimension_id,
            "question": canonical["question"],
            "question_date": canonical.get("question_date") or NOT_RECORDED,
            "gold_answer": gold_answer if gold_answer is not None else NOT_APPLICABLE,
            "evidence_session_ids": canonical["evidence_session_ids"],
            "answer_context_schema": "memeval-ranked-memories-v1",
            "retrieved_context": contexts,
            "retrieved_context_metadata": [
                {
                    "rank": memory.get("rank", index),
                    "session_id": memory.get("session_id"),
                    "score": memory.get("score"),
                }
                for index, memory in enumerate(memories, 1)
                if isinstance(memory, dict)
            ],
        }

    def _metrics_by_k(
        self, canonical: dict[str, Any], memories: list[dict[str, Any]]
    ) -> dict[str, dict[str, float]]:
        gold = set(map(str, canonical["evidence_session_ids"]))
        if not gold:
            return {}
        retrieved = [str(memory.get("session_id")) for memory in memories]
        output = {}
        for cutoff in (1, 3, 5, 10):
            if cutoff > self.top_k:
                continue
            overlap = gold.intersection(retrieved[:cutoff])
            output[str(cutoff)] = {
                "hit": float(bool(overlap)),
                "recall": len(overlap) / len(gold),
            }
        return output

    def _retrieval_row(
        self,
        artifact: ReviewedCaseArtifact,
        result: dict[str, Any],
        canonical: dict[str, Any],
    ) -> dict[str, Any] | None:
        if artifact.dimension_id not in RETRIEVAL_DIMENSIONS:
            return None
        memories = [
            dict(memory) for memory in result.get("retrieved_memories", [])
            if isinstance(memory, dict)
        ]
        evidence = set(map(str, canonical["evidence_session_ids"]))
        retrieved = [str(memory.get("session_id")) for memory in memories]
        evidence_ranks = [index for index, ident in enumerate(retrieved, 1) if ident in evidence]
        metrics = result.get("metrics", {})
        gold_answer = self._gold_answer(artifact)
        return {
            "case_id": canonical["case_id"],
            "dimension_id": artifact.dimension_id,
            "question_type": artifact.dimension_id,
            "question": canonical["question"],
            "question_date": canonical.get("question_date") or NOT_RECORDED,
            "gold_answer": gold_answer if gold_answer is not None else NOT_APPLICABLE,
            "session_count": len(canonical["sessions"]),
            "evidence_session_ids": canonical["evidence_session_ids"],
            "retrieved": memories,
            "raw_result_count": len(memories),
            "hit_at_k": metrics.get("hit_at_k"),
            "recall_at_k": metrics.get("recall_at_k"),
            "mrr": metrics.get("mrr"),
            "metrics_by_k": self._metrics_by_k(canonical, memories),
            "mean_evidence_rank": _mean(evidence_ranks),
            "retrieved_evidence_count": len(evidence.intersection(retrieved)),
            "missing_evidence_count": len(evidence - set(retrieved)),
            "index_latency_ms": result.get("latency", {}).get("ingest"),
            "search_latency_ms": result.get("latency", {}).get("retrieval"),
            "search_status": "FAIL" if result.get("status") == "error" else "PASS",
            "search_request_count": 1,
            "search_http_status": NOT_RECORDED,
            "search_retry_count": NOT_RECORDED,
            "returned_session_count": len(memories),
            "raw_search_file": NOT_RECORDED,
        }

    def _add_row(
        self,
        result: dict[str, Any],
        canonical: dict[str, Any],
    ) -> dict[str, Any]:
        ingest = next(
            (event for event in self._system_events(result) if event.get("operation") == "ingest"),
            {},
        )
        ingest_ok = ingest.get("status") == "ok" and result.get("status") != "error"
        sessions = canonical["sessions"]
        expected_turns = sum(len(session.get("messages", [])) for session in sessions)
        health = ingest.get("health") if isinstance(ingest.get("health"), dict) else {}
        items = ingest.get("items") if isinstance(ingest.get("items"), list) else []
        failures = ingest.get("failures") if isinstance(ingest.get("failures"), list) else []
        return {
            "case_id": canonical["case_id"],
            "add_mode": "memeval-system-adapter",
            "expected_sessions": len(sessions),
            "added_sessions": len(sessions) if ingest_ok else 0,
            "expected_turns": expected_turns,
            "added_turns": expected_turns if ingest_ok else 0,
            "expected_evidence_sessions": len(canonical["evidence_session_ids"]),
            "added_evidence_sessions": len(canonical["evidence_session_ids"]) if ingest_ok else 0,
            "failed_session_ids": failures,
            "duplicate_session_ids": len(sessions) - len({s["session_id"] for s in sessions}),
            "empty_content_session_ids": [],
            "namespace": NOT_RECORDED,
            "user_id": NOT_RECORDED,
            "workspace": NOT_RECORDED,
            "add_request_count": len(sessions),
            "add_latency_ms": NOT_RECORDED,
            "add_status": "PASS" if ingest_ok else "FAIL",
            "add_error": result.get("error") or NOT_RECORDED,
            "index_status": "PASS" if ingest_ok else "FAIL",
            "embedding_status": NOT_APPLICABLE,
            "embedding_call_count": 0,
            "embedding_failure_count": 0,
            "extraction_status": NOT_APPLICABLE,
            "extraction_call_count": 0,
            "extraction_failure_count": 0,
            "service_port": NOT_RECORDED,
            "service_log": NOT_RECORDED,
            "index_request_count": 1,
            "index_http_status": NOT_RECORDED,
            "index_latency_ms": result.get("latency", {}).get("ingest"),
            "indexed_document_count": len(items) if items else len(sessions),
            "indexed_chunk_count": health.get("n_chunks", NOT_RECORDED),
            "chunks_with_embedding": health.get("chunks_with_embedding", 0),
            "index_failed_paths": failures,
            "raw_reindex_file": NOT_RECORDED,
        }

    def write_inputs(self, results: list[dict[str, Any]]) -> int:
        result_ids = [str(result.get("case_id", "")) for result in results]
        if len(result_ids) != len(set(result_ids)):
            raise ValueError("MemEval results contain duplicate Case IDs")
        if set(result_ids) != set(self.artifacts):
            raise ValueError("MemEval results do not match the selected frozen Cases")

        prepared_rows = []
        llm_rows = []
        retrieval_rows = []
        add_rows = []
        for result in results:
            artifact = self.artifacts[str(result["case_id"])]
            canonical = build_reme_case(artifact.case, artifact.context_path).case
            prepared = self._prepared_row(artifact, result, canonical)
            prepared_rows.append(prepared)
            if (
                artifact.dimension_id in ANSWER_DIMENSIONS
                and self._gold_answer(artifact) is not None
                and result.get("retrieval_status", result.get("status")) != "error"
            ):
                llm_rows.append(prepared)
            retrieval = self._retrieval_row(artifact, result, canonical)
            if retrieval is not None:
                retrieval_rows.append(retrieval)
            add_rows.append(self._add_row(result, canonical))

        _write_jsonl(self.run_dir / "prepared.jsonl", prepared_rows)
        _write_jsonl(self.run_dir / "llm_input.jsonl", llm_rows)
        _write_jsonl(self.run_dir / "retrieval.jsonl", retrieval_rows)
        _write_jsonl(self.run_dir / "add_trace.jsonl", add_rows)
        for name in ("failures.jsonl", "answer_failures.jsonl", "judge_failures.jsonl", "api_errors.jsonl"):
            (self.run_dir / name).touch(exist_ok=True)

        run_summary = _read_json(self.run_dir / "run_summary.json")
        metadata = run_summary.get("system_metadata", {})
        run_config = {
            "task": "memeval_reme_answer_judge",
            "run_id": run_summary["run_id"],
            "dataset_id": run_summary["dataset_id"],
            "dataset_name": "Agent Memory Eval",
            "dataset_version": "v0.1",
            "source_dataset": "MemEval multi-source frozen release",
            "language": "mixed",
            "translated": False,
            "dataset_case_count": 298,
            "selected_case_ids": result_ids,
            "top_k": self.top_k,
            "memory_backend": metadata.get("memory_backend", run_summary.get("system")),
            "memory_version": metadata.get("memory_version", run_summary.get("system_version")),
            "embedding_enabled": metadata.get("embedding_enabled", False),
            "start_time_utc": run_summary.get("created_at", datetime.now(timezone.utc).isoformat()),
            "source_root": str(self.benchmark_root),
        }
        (self.run_dir / "run_config.json").write_text(
            json.dumps(run_config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        retrieval_summary = {
            "task": "memeval_retrieval",
            "requested_cases": len(results),
            "successful_cases": sum(result.get("status") != "error" for result in results),
            "failed_cases": sum(result.get("status") == "error" for result in results),
            "added_sessions": sum(row["added_sessions"] for row in add_rows),
            "indexed_document_count": sum(
                int(row["indexed_document_count"])
                for row in add_rows if isinstance(row["indexed_document_count"], (int, float))
            ),
            "indexed_chunk_count": sum(
                int(row["indexed_chunk_count"])
                for row in add_rows if isinstance(row["indexed_chunk_count"], (int, float))
            ),
            "add_success_rate": _mean(row["add_status"] == "PASS" for row in add_rows),
            "index_success_rate": _mean(row["index_status"] == "PASS" for row in add_rows),
            "search_success_rate": _mean(
                row["search_status"] == "PASS" for row in retrieval_rows
            ),
            "embedding": {
                "enabled": metadata.get("embedding_enabled", False),
                "status": NOT_APPLICABLE if not metadata.get("embedding_enabled", False) else NOT_RECORDED,
                "call_count": 0 if not metadata.get("embedding_enabled", False) else NOT_RECORDED,
                "failure_count": 0 if not metadata.get("embedding_enabled", False) else NOT_RECORDED,
            },
        }
        (self.run_dir / "summary.json").write_text(
            json.dumps(retrieval_summary, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        (self.run_dir / "run_metadata.json").write_text(
            json.dumps(
                {
                    "run_id": run_summary["run_id"],
                    "adapter": "memeval-trace-v1",
                    "created_at_utc": datetime.now(timezone.utc).isoformat(),
                },
                ensure_ascii=False,
                indent=2,
            ) + "\n",
            encoding="utf-8",
        )
        return len(llm_rows)

    @staticmethod
    def _usage_cost(*rows: dict[str, Any] | None) -> dict[str, Any]:
        usages = [row.get("usage", {}) for row in rows if isinstance(row, dict)]
        costs = [usage.get("cost") for usage in usages if isinstance(usage, dict)]
        recorded = [cost for cost in costs if isinstance(cost, dict)]
        return {
            "input_tokens": sum(int(usage.get("prompt_tokens", 0) or 0) for usage in usages),
            "output_tokens": sum(int(usage.get("completion_tokens", 0) or 0) for usage in usages),
            "api_cost": (
                sum(float(cost.get("total_cost_usd", 0.0)) for cost in recorded)
                if recorded else None
            ),
        }

    def apply_llm_outputs(self, results_path: str | Path) -> list[dict[str, Any]]:
        results_path = Path(results_path)
        results = _read_jsonl(results_path)
        eligible = set(_row_map(self.run_dir / "llm_input.jsonl"))
        answers = _row_map(self.run_dir / "answers.jsonl")
        scores = _row_map(self.run_dir / "scores.jsonl")
        answer_failures = _row_map(self.run_dir / "answer_failures.jsonl")
        judge_failures = _row_map(self.run_dir / "judge_failures.jsonl")

        for result in results:
            case_id = str(result["case_id"])
            result.setdefault("retrieval_status", result.get("status"))
            if case_id not in eligible:
                result["answer"] = {"status": NOT_APPLICABLE}
                result["judge"] = {"status": NOT_APPLICABLE}
                continue
            answer = answers.get(case_id)
            score = scores.get(case_id)
            answer_failure = answer_failures.get(case_id)
            judge_failure = judge_failures.get(case_id)
            result["answer"] = {"status": "ok", **answer} if answer else {
                "status": "error", "failure": answer_failure or {"error": "Answer output missing"}
            }
            result["judge"] = {"status": "ok", **score} if score else {
                "status": "error", "failure": judge_failure or {"error": "Judge output missing"}
            }
            result.setdefault("trace", {}).setdefault("runner", []).extend(
                [
                    {"stage": "answer", "status": "ok" if answer else "error"},
                    {"stage": "judge", "status": "ok" if score else "error"},
                ]
            )
            result["trace"]["llm"] = {"answer": result["answer"], "judge": result["judge"]}
            result.setdefault("latency", {})["answer"] = answer.get("latency_ms") if answer else None
            result["latency"]["judge"] = score.get("latency_ms") if score else None
            result["cost"] = self._usage_cost(answer, score)
            if answer and score:
                result["system_prediction"] = result.get("prediction")
                result["prediction"] = {
                    "status": "ok",
                    "generated_answer": answer["generated_answer"],
                }
                answer_metric = (
                    "personalized_answer_accuracy"
                    if result.get("dimension_id") == "D05"
                    else "answer_accuracy"
                )
                result.setdefault("metrics", {})[answer_metric] = float(bool(score["is_correct"]))
                result["unsupported_metrics"] = [
                    name for name in result.get("unsupported_metrics", [])
                    if name != answer_metric
                ]
                result["status"] = result["retrieval_status"]
                if result.get("status") == "partial" and not result["unsupported_metrics"]:
                    result["status"] = "ok"
                if (result.get("error") or {}).get("stage") in {
                    "answer", "judge", "answer_judge"
                }:
                    result["error"] = None
            else:
                result["status"] = "error"
                failure = answer_failure or judge_failure or {"error": "Answer/Judge output missing"}
                result["error"] = {
                    "type": str(failure.get("error_type", "LLMStageError")),
                    "message": str(failure.get("error", "Answer/Judge output missing")),
                    "stage": str(failure.get("stage", "answer_judge")),
                }

        _write_jsonl(results_path, results)
        self._refresh_run_summary(results)
        return results

    def _refresh_run_summary(self, results: list[dict[str, Any]]) -> None:
        path = self.run_dir / "run_summary.json"
        summary = _read_json(path)
        dimensions = {}
        for dimension_id in sorted({str(row["dimension_id"]) for row in results}):
            rows = [row for row in results if row["dimension_id"] == dimension_id]
            names = sorted({name for row in rows for name in row.get("metrics", {})})
            dimensions[dimension_id] = {
                "case_count": len(rows),
                "status_counts": dict(Counter(row["status"] for row in rows)),
                "metrics": {
                    name: _mean(row.get("metrics", {}).get(name) for row in rows)
                    for name in names
                },
                "unsupported_metric_counts": dict(
                    Counter(name for row in rows for name in row.get("unsupported_metrics", []))
                ),
            }
        eligible = [row for row in results if row["case_id"] in set(_row_map(self.run_dir / "llm_input.jsonl"))]
        answer_rows = [row.get("answer") for row in eligible if row.get("answer", {}).get("status") == "ok"]
        judge_rows = [row.get("judge") for row in eligible if row.get("judge", {}).get("status") == "ok"]
        summary.update(
            status_counts=dict(Counter(row["status"] for row in results)),
            dimensions=dimensions,
            answer_judge={
                "eligible_case_count": len(eligible),
                "answer_success_count": len(answer_rows),
                "judge_success_count": len(judge_rows),
                "answer_model": answer_rows[0].get("model") if answer_rows else NOT_RECORDED,
                "judge_model": judge_rows[0].get("model") if judge_rows else NOT_RECORDED,
                "answer_env": self.answer_env,
                "judge_env": self.judge_env,
                "cost": self._usage_cost(*answer_rows, *judge_rows),
            },
        )
        path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    def _dimension_dashboard_metrics(
        self, results: list[dict[str, Any]]
    ) -> dict[str, dict[str, Any]]:
        rows = {
            dimension: [row for row in results if row.get("dimension_id") == dimension]
            for dimension in ("D01", "D02", "D03", "D04", "D05", "D06", "D07", "D08")
        }

        def payload(row: dict[str, Any]) -> dict[str, Any]:
            artifact = self.artifacts[str(row["case_id"])]
            return artifact.case["gold"]["payload"]

        def mean_metric(selected: list[dict[str, Any]], name: str) -> Any:
            return _mean(row.get("metrics", {}).get(name) for row in selected)

        def answer_metric(selected: list[dict[str, Any]], name: str = "answer_accuracy") -> Any:
            return mean_metric(selected, name)

        d01 = rows["D01"]
        d02 = rows["D02"]
        d03 = rows["D03"]
        d04 = rows["D04"]
        d05 = rows["D05"]
        d06 = rows["D06"]
        d07 = rows["D07"]
        d08 = rows["D08"]
        d04_unsupported = sum(
            "activation_decision" in row.get("unsupported_metrics", []) for row in d04
        )
        d08_sensitive_total = sum(len(payload(row).get("canary_tokens", [])) for row in d08)
        d08_forbidden_total = sum(
            len(payload(row).get("forbidden_memory_ids", [])) for row in d08
        )
        d08_deleted_total = sum(
            len(payload(row).get("deleted_memory_ids", [])) for row in d08
        )

        def total_metric(selected: list[dict[str, Any]], name: str) -> float:
            return sum(
                float(row.get("metrics", {}).get(name, 0) or 0) for row in selected
            )

        # D03: deleted-fact recall over lifecycle Cases (expected_active=False).
        d03_lifecycle = [
            row for row in d03
            if (payload(row).get("lifecycle") or {}).get("expected_active") is False
        ]
        d03_deleted_hit_rate = _mean(
            row.get("metrics", {}).get("deleted_hit") for row in d03_lifecycle
        )

        # D07: paired scale-group Recall Degradation (small scale minus large scale).
        scale_groups: dict[str, dict[str, list[float]]] = {}
        for row in d07:
            gold = payload(row)
            group_id = str(gold.get("scale_group_id") or "")
            level = str(gold.get("scale_level") or "")
            if not group_id or not level:
                continue
            recall = row.get("metrics", {}).get("recall_at_k")
            if isinstance(recall, (int, float)):
                scale_groups.setdefault(group_id, {}).setdefault(level, []).append(float(recall))
        degradation_values: list[float] = []
        recall_by_scale: dict[str, Any] = {}
        for group_levels in scale_groups.values():
            for level, values in group_levels.items():
                recall_by_scale[level] = _mean(values)
            smallest = group_levels.get("100K") or (min(
                (values for values in group_levels.values()), default=None
            ) if group_levels else None)
            largest = group_levels.get("10M")
            if isinstance(smallest, list) and isinstance(largest, list):
                degradation_values.append(_mean(smallest) - _mean(largest))
        d07_p95_latency = _p95([
            row.get("latency", {}).get("retrieval") for row in d07
        ])

        return {
            "D01": {
                "title": "记忆抽取与写入",
                "source": "LongMemEval",
                "tests": "从历史对话中抽取应写入记忆的事实（写入精确率 / 召回率）",
                "case_count": len(d01),
                "availability": "MEASURED" if d01 else NOT_RECORDED,
                "answer_judge": NOT_APPLICABLE,
                "metrics": {
                    "write_precision": mean_metric(d01, "write_event_precision"),
                    "write_recall": mean_metric(d01, "write_event_recall"),
                    "written_memory_units": sum(
                        int(row.get("metrics", {}).get("written_memory_units", 0) or 0)
                        for row in d01
                    ),
                    "unexpected_written_event_count": int(
                        total_metric(d01, "unexpected_written_event_count")
                    ),
                },
                "metric_scope": "event_id_alignment",
            },
            "D02": {
                "title": "长期记忆检索",
                "source": "LongMemEval",
                "tests": "长期记忆的证据检索命中与排序质量（Hit@K / Recall@K / MRR）",
                "case_count": len(d02),
                "availability": "MEASURED" if d02 else NOT_RECORDED,
                "answer_judge": "MEASURED" if answer_metric(d02) is not None else NOT_RECORDED,
                "metrics": {
                    "hit_at_k": mean_metric(d02, "hit_at_k"),
                    "recall_at_k": mean_metric(d02, "recall_at_k"),
                    "mrr": mean_metric(d02, "mrr"),
                    "answer_accuracy": answer_metric(d02),
                },
            },
            "D03": {
                "title": "长时间跨度对话",
                "source": "LoCoMo",
                "tests": "时间推理、长间隔回忆与删除后遗忘（Deleted Hit Rate）",
                "case_count": len(d03),
                "availability": "MEASURED" if d03 else NOT_RECORDED,
                "answer_judge": "MEASURED" if answer_metric(d03) is not None else NOT_RECORDED,
                "metrics": {
                    "answer_accuracy": answer_metric(d03),
                    "recall_at_k": mean_metric(d03, "recall_at_k"),
                    "deleted_hit_rate": d03_deleted_hit_rate,
                },
                "lifecycle_case_count": len(d03_lifecycle),
            },
            "D04": {
                "title": "主动调用与记忆使用",
                "source": "PrefEval",
                "tests": "系统是否自主激活记忆调用（Activation Precision / Recall）",
                "case_count": len(d04),
                "availability": (
                    "UNSUPPORTED"
                    if d04 and d04_unsupported == len(d04)
                    else "PARTIAL" if d04_unsupported
                    else "MEASURED" if d04
                    else NOT_RECORDED
                ),
                "answer_judge": NOT_APPLICABLE,
                "metrics": {
                    "activation_recall": mean_metric(d04, "activation_recall"),
                    "required_activation_cases": sum(
                        bool(payload(row).get("should_activate")) for row in d04
                    ),
                    "unsupported_activation_cases": d04_unsupported,
                    "utilization_rate": NOT_APPLICABLE,
                    "e2e_accuracy": NOT_APPLICABLE,
                },
            },
            "D05": {
                "title": "用户画像与偏好",
                "source": "PersonaMem-v2",
                "tests": "用户偏好画像的召回与个性化回答准确率",
                "case_count": len(d05),
                "availability": "MEASURED" if d05 else NOT_RECORDED,
                "answer_judge": "MEASURED" if answer_metric(d05, "personalized_answer_accuracy") is not None else NOT_RECORDED,
                "metrics": {
                    "recall_at_k": mean_metric(d05, "recall_at_k"),
                    "personalized_answer_accuracy": answer_metric(d05, "personalized_answer_accuracy"),
                },
            },
            "D06": {
                "title": "动态更新与冲突",
                "source": "MemoryAgentBench",
                "tests": "冲突事实的最新值解析（Latest-value）与陈旧值抑制（Stale Retrieval）",
                "case_count": len(d06),
                "availability": "MEASURED" if d06 else NOT_RECORDED,
                "answer_judge": "MEASURED" if answer_metric(d06) is not None else NOT_RECORDED,
                "metrics": {
                    "answer_accuracy": answer_metric(d06),
                    "stale_retrieval_rate": mean_metric(d06, "stale_retrieval_rate"),
                    "winning_fact_recall": mean_metric(d06, "winning_fact_recall"),
                },
            },
            "D07": {
                "title": "超大规模长上下文",
                "source": "BEAM",
                "tests": "上下文规模增长下的检索退化（Recall Degradation）与时延",
                "case_count": len(d07),
                "availability": "MEASURED" if d07 else NOT_RECORDED,
                "answer_judge": "MEASURED" if answer_metric(d07) is not None else NOT_RECORDED,
                "metrics": {
                    "recall_at_k": mean_metric(d07, "recall_at_k"),
                    "recall_degradation": _mean(degradation_values) if degradation_values else None,
                    "p95_search_latency_ms": d07_p95_latency,
                    "answer_accuracy": answer_metric(d07),
                },
                "recall_by_scale": recall_by_scale,
                "scale_group_count": len(scale_groups),
            },
            "D08": {
                "title": "隐私与用户隔离",
                "source": "AgentMemBench",
                "tests": "跨用户隔离、删除完整性与金丝雀泄露防护",
                "case_count": len(d08),
                "availability": "MEASURED" if d08 else NOT_RECORDED,
                "answer_judge": NOT_APPLICABLE,
                "metrics": {
                    "sensitive_exposure_rate": (
                        total_metric(d08, "canary_exposure_count") / d08_sensitive_total
                        if d08_sensitive_total else None
                    ),
                    "cross_user_leakage_rate": (
                        total_metric(d08, "forbidden_exposure_count") / d08_forbidden_total
                        if d08_forbidden_total else None
                    ),
                    "deleted_memory_hit_rate": (
                        total_metric(d08, "deleted_exposure_count") / d08_deleted_total
                        if d08_deleted_total else None
                    ),
                    "privacy_pass_rate": mean_metric(d08, "privacy_pass"),
                    "allowed_recall": mean_metric(d08, "allowed_recall"),
                },
                "denominators": {
                    "sensitive_canaries": d08_sensitive_total,
                    "forbidden_memories": d08_forbidden_total,
                    "deleted_memories": d08_deleted_total,
                },
            },
        }

    def _timeline(self, result: dict[str, Any]) -> list[dict[str, str]]:
        dimension = str(result["dimension_id"])
        runner = result.get("trace", {}).get("runner", [])
        runner_status = {
            str(event.get("stage")): str(event.get("status"))
            for event in runner if isinstance(event, dict)
        }
        system_events = self._system_events(result)
        operation_status = {
            str(event.get("operation")): str(event.get("status")) for event in system_events
        }

        def stage(key: str, label: str, raw_status: str | None, reason: str) -> dict[str, str]:
            status = "pass" if raw_status in {"ok", "reused"} else (
                "fail" if raw_status == "error" else "unknown"
            )
            return {"key": key, "label": label, "status": status, "reason": reason}

        stages = [
            stage("load", "Load Context", runner_status.get("load_context"), "读取冻结 Context"),
            stage("ingest", "ReMe Ingest", runner_status.get("ingest"), "写入并建立索引"),
        ]
        if dimension in RETRIEVAL_DIMENSIONS:
            stages.append(stage("search", "ReMe Search", operation_status.get("search"), "检索相关记忆"))
        if dimension == "D01":
            value = result.get("metrics", {}).get("write_event_recall")
            stages.append(stage("write", "Write Evaluation", "ok" if value == 1.0 else "error", f"write_event_recall={value}"))
        elif dimension == "D04":
            stages.append(stage("activation", "Activation Trace", "unsupported", "ReMe 未暴露主动激活决策 Trace"))
        elif dimension == "D05":
            profile_status = result.get("system_prediction", result.get("prediction", {})).get("status")
            stages.append(stage("profile", "Profile Evaluation", profile_status, "检查 Profile 能力"))
        elif dimension == "D08":
            if "delete" in operation_status:
                stages.append(stage("delete", "Lifecycle Delete", operation_status["delete"], "删除后重建索引"))
            privacy = result.get("metrics", {}).get("privacy_pass")
            stages.append(stage("privacy", "Privacy Evaluation", "ok" if privacy == 1.0 else "error", f"privacy_pass={privacy}"))

        if dimension in ANSWER_DIMENSIONS:
            stages.extend(
                [
                    stage("answer", "Answer", result.get("answer", {}).get("status"), "基于检索记忆生成回答"),
                    stage("judge", "Judge", result.get("judge", {}).get("status"), "对照 Gold 判分"),
                ]
            )
        else:
            stages.extend(
                [
                    {
                        "key": "answer", "label": "Answer",
                        "status": "not_applicable", "reason": "该维度无 gold_answer，不适用",
                    },
                    {
                        "key": "judge", "label": "Judge",
                        "status": "not_applicable", "reason": "该维度无 gold_answer，不适用",
                    },
                ]
            )
        stages.append(
            stage(
                "final", "Final", "error" if result.get("status") == "error" else "ok",
                f"status={result.get('status')}",
            )
        )
        return stages

    @staticmethod
    def _override_final(analysis: dict[str, Any], result: dict[str, Any]) -> None:
        status = str(result.get("status"))
        dimension = str(result.get("dimension_id"))
        judge_correct = analysis["judge"].get("is_correct")
        if status == "error":
            root = "PIPELINE_FAILURE"
            explanation = str((result.get("error") or {}).get("message", "Case pipeline failed"))
        elif isinstance(judge_correct, bool) and judge_correct is False:
            root = analysis["final"]["root_cause"]
            explanation = analysis["final"]["explanation"]
        elif status == "unsupported":
            root = "UNSUPPORTED_CAPABILITY"
            explanation = f"{dimension} requires a capability that ReMe does not expose."
        elif status == "partial":
            root = "PARTIAL_CAPABILITY"
            explanation = f"{dimension} completed with explicitly unsupported metrics."
        elif dimension == "D08" and result.get("metrics", {}).get("privacy_pass") != 1.0:
            root = "PRIVACY_FAILURE"
            explanation = "The privacy, deletion, or canary exposure checks did not all pass."
        elif isinstance(judge_correct, bool):
            root = analysis["final"]["root_cause"]
            explanation = analysis["final"]["explanation"]
        else:
            root = "PASS"
            explanation = f"{dimension} completed its applicable metrics without a runtime error."
        suggestions = {
            "UNSUPPORTED_CAPABILITY": "Implement the missing System Adapter capability before scoring it.",
            "PARTIAL_CAPABILITY": "Review unsupported_metrics and keep them separate from zero scores.",
            "PRIVACY_FAILURE": "Inspect identity filtering, deletion, and exposed memory IDs.",
        }
        analysis["final"].update(
            root_cause=root,
            explanation=explanation,
            suggested_fix=suggestions.get(root, analysis["final"].get("suggested_fix")),
            pipeline_complete=status != "error",
        )

    def build_trace(self, results_path: str | Path) -> dict[str, Any]:
        results = _read_jsonl(Path(results_path))
        prepared = _row_map(self.run_dir / "prepared.jsonl")
        retrieval = _row_map(self.run_dir / "retrieval.jsonl")
        adds = _row_map(self.run_dir / "add_trace.jsonl")
        answers = _row_map(self.run_dir / "answers.jsonl")
        scores = _row_map(self.run_dir / "scores.jsonl")
        failures = _row_map(self.run_dir / "failures.jsonl")
        answer_failures = _row_map(self.run_dir / "answer_failures.jsonl")
        judge_failures = _row_map(self.run_dir / "judge_failures.jsonl")

        cases = []
        for result in results:
            case_id = str(result["case_id"])
            artifact = self.artifacts[case_id]
            canonical = build_reme_case(artifact.case, artifact.context_path).case
            analysis = _case_analysis(
                ident=case_id,
                run_dir=self.run_dir,
                dataset_case=canonical,
                prepared=prepared.get(case_id),
                retrieval=retrieval.get(case_id),
                answer=answers.get(case_id),
                score=scores.get(case_id),
                add_trace=adds.get(case_id),
                retrieval_failure=failures.get(case_id),
                answer_failure=answer_failures.get(case_id),
                judge_failure=judge_failures.get(case_id),
                top_k=self.top_k,
            )
            analysis["case"].update(
                dimension_id=artifact.dimension_id,
                payload_type=artifact.case["gold"]["payload_type"],
                status=result["status"],
            )
            analysis["dimension"] = {
                "dimension_id": artifact.dimension_id,
                "payload_type": artifact.case["gold"]["payload_type"],
                "gold_payload": artifact.case["gold"]["payload"],
                "metrics": result.get("metrics", {}),
                "unsupported_metrics": result.get("unsupported_metrics", []),
                "prediction": result.get("prediction"),
                "system_prediction": result.get("system_prediction"),
                "context_cache": result.get("context_cache"),
                "run_mode": result.get("run_mode"),
                "status": result.get("status"),
                "error": result.get("error"),
                "latency": result.get("latency"),
                "cost": result.get("cost"),
                "system_trace": result.get("trace", {}).get("system"),
            }
            analysis["timeline"] = self._timeline(result)
            self._override_final(analysis, result)
            cases.append(analysis)

        trace_dir = self.run_dir / "trace"
        case_dir = trace_dir / "cases"
        case_dir.mkdir(parents=True, exist_ok=True)
        for case in cases:
            name = _safe_name(str(case["case"]["case_id"]))
            (case_dir / f"{name}.json").write_text(
                json.dumps(case, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
            )
            markdown = _render_case(case) + "\n\n## MemEval Dimension\n\n```json\n" + json.dumps(
                case["dimension"], ensure_ascii=False, indent=2
            ) + "\n```\n"
            (case_dir / f"{name}.md").write_text(markdown, encoding="utf-8")

        summary = _summary(cases, self.run_dir, self.top_k)
        non_error = sum(result.get("status") != "error" for result in results)
        judged = [case for case in cases if isinstance(case["judge"].get("is_correct"), bool)]
        summary.update(
            schema_version="memeval_trace_summary_v1",
            dataset=str(self.benchmark_root),
            dataset_id="MemEval-v0.1",
            dataset_name="Agent Memory Eval",
            dataset_version="v0.1",
            source_dataset="MemEval multi-source frozen release",
            language="mixed",
            translated=False,
            case_count=len(cases),
            successful_pipeline_cases=non_error,
            failed_pipeline_cases=len(cases) - non_error,
            pipeline_success_rate=non_error / len(cases) if cases else None,
            grounded_end_to_end_accuracy=(
                _mean(case["final"]["retrieval_pass"] and case["final"]["answer_pass"] for case in judged)
                if judged else None
            ),
        )
        dimensions = {}
        for dimension_id in sorted({str(result["dimension_id"]) for result in results}):
            dimension_results = [result for result in results if result["dimension_id"] == dimension_id]
            metric_names = sorted({
                name for result in dimension_results for name in result.get("metrics", {})
            })
            dimensions[dimension_id] = {
                "case_count": len(dimension_results),
                "status_counts": dict(Counter(result["status"] for result in dimension_results)),
                "metrics": {
                    name: _mean(result.get("metrics", {}).get(name) for result in dimension_results)
                    for name in metric_names
                },
                "unsupported_metric_counts": dict(Counter(
                    name for result in dimension_results
                    for name in result.get("unsupported_metrics", [])
                )),
            }
            summary.setdefault("question_type_breakdown", {}).setdefault(dimension_id, {}).update(
                dimensions[dimension_id]
            )
        summary["dimension_breakdown"] = dimensions
        summary["dimension_metrics"] = self._dimension_dashboard_metrics(results)
        summary["dimension_metric_audit"] = DIMENSION_METRIC_AUDIT
        summary["cases"] = [
            {
                **row,
                "dimension_id": case["case"]["dimension_id"],
                "status": case["case"]["status"],
                "metrics": case["dimension"]["metrics"],
                "unsupported_metrics": case["dimension"]["unsupported_metrics"],
            }
            for row, case in zip(summary["cases"], cases, strict=True)
        ]
        (trace_dir / "trace_summary.json").write_text(
            json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        (trace_dir / "trace_summary.md").write_text(_render_summary(summary), encoding="utf-8")
        (trace_dir / "trace_index.md").write_text(_render_index(cases), encoding="utf-8")
        (trace_dir / "judge_review.md").write_text(_render_judge_review(cases), encoding="utf-8")
        return summary
