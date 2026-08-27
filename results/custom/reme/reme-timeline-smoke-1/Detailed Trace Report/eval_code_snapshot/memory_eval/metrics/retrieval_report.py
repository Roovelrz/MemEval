"""Retrieval-only summary for prepare-only memory runs."""

from __future__ import annotations

import json
from pathlib import Path

from .retrieval import retrieval_scores


def build_retrieval_summary(
    retrieval_path: str | Path,
    output_path: str | Path,
    memory_adapter: str,
    top_k: int,
) -> dict:
    rows = [
        json.loads(line)
        for line in Path(retrieval_path).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    metrics: list[dict[str, float]] = []
    failed_cases: list[str] = []
    latencies: list[float] = []
    for row in rows:
        latencies.append(float(row.get("search_latency_ms", 0.0)))
        metric = retrieval_scores(
            answer_session_ids=[str(value) for value in row.get("answer_session_ids", [])],
            retrieved_session_ids=[entry.get("session_id") for entry in row.get("retrieved", [])],
            is_abstention=bool(row.get("is_abstention", False)),
        )
        if metric is None:
            continue
        metrics.append(metric)
        if metric["hit_at_k"] == 0.0:
            failed_cases.append(str(row["id"]))

    summary = {
        "dataset": "longmemeval_s_cleaned",
        "mode": "retrieval_only",
        "memory_adapter": memory_adapter,
        "top_k": top_k,
        "num_cases": len(rows),
        "retrieval_evaluated_cases": len(metrics),
        "retrieval_hit_at_k": (
            sum(value["hit_at_k"] for value in metrics) / len(metrics) if metrics else None
        ),
        "retrieval_recall_at_k": (
            sum(value["recall_at_k"] for value in metrics) / len(metrics) if metrics else None
        ),
        "avg_search_latency_ms": sum(latencies) / len(latencies) if latencies else 0.0,
        "failed_cases": failed_cases,
    }
    destination = Path(output_path)
    destination.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return summary
