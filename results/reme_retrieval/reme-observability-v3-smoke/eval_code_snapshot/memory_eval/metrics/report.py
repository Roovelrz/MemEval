"""Aggregate AML binary scores and retrieval artifacts."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

from .retrieval import retrieval_scores


def _read_jsonl(path: str | Path) -> list[dict]:
    return [
        json.loads(line)
        for line in Path(path).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def build_summary(
    prepared_path: str | Path,
    retrieval_path: str | Path,
    scores_path: str | Path,
    output_path: str | Path,
    mode: str,
    top_k: int,
) -> dict:
    prepared = {row["id"]: row for row in _read_jsonl(prepared_path)}
    retrieval = {row["id"]: row for row in _read_jsonl(retrieval_path)}
    scores = {row["id"]: row for row in _read_jsonl(scores_path)}
    if set(prepared) != set(scores):
        raise ValueError("prepared/scores ID mismatch")
    if set(prepared) != set(retrieval):
        raise ValueError("prepared/retrieval ID mismatch")

    type_counts: dict[str, dict[str, int]] = defaultdict(lambda: {"num_cases": 0, "num_correct": 0})
    failed_cases: list[str] = []
    retrieval_values: list[dict[str, float]] = []
    latencies: list[float] = []

    for ident, item in prepared.items():
        score = scores[ident]
        question_type = str(item.get("question_type", "unknown"))
        type_counts[question_type]["num_cases"] += 1
        if bool(score.get("is_correct")):
            type_counts[question_type]["num_correct"] += 1
        else:
            failed_cases.append(ident)

        trace = retrieval[ident]
        latencies.append(float(trace.get("search_latency_ms", 0.0)))
        metric = retrieval_scores(
            answer_session_ids=[str(value) for value in trace.get("answer_session_ids", [])],
            retrieved_session_ids=[entry.get("session_id") for entry in trace.get("retrieved", [])],
            is_abstention=bool(trace.get("is_abstention", False)),
        )
        if metric is not None:
            retrieval_values.append(metric)

    num_cases = len(scores)
    num_correct = sum(bool(row.get("is_correct")) for row in scores.values())
    accuracy = num_correct / num_cases if num_cases else 0.0
    by_question_type = {
        question_type: {
            **counts,
            "accuracy": counts["num_correct"] / counts["num_cases"],
        }
        for question_type, counts in sorted(type_counts.items())
    }
    summary = {
        "dataset": "longmemeval_s_cleaned",
        "mode": mode,
        "num_cases": num_cases,
        "num_correct": num_correct,
        "accuracy": accuracy,
        "accuracy_pct": accuracy * 100,
        "top_k": top_k,
        "by_question_type": by_question_type,
        "avg_search_latency_ms": sum(latencies) / len(latencies) if latencies else 0.0,
        "retrieval_evaluated_cases": len(retrieval_values),
        "retrieval_recall_at_k": (
            sum(value["recall_at_k"] for value in retrieval_values) / len(retrieval_values)
            if retrieval_values
            else None
        ),
        "retrieval_hit_at_k": (
            sum(value["hit_at_k"] for value in retrieval_values) / len(retrieval_values)
            if retrieval_values
            else None
        ),
        "failed_cases": failed_cases,
    }
    destination = Path(output_path)
    destination.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return summary
