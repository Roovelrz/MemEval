from __future__ import annotations

import json
import unittest
from pathlib import Path

from memory_eval.metrics.report import build_summary
from tests.helpers import workspace_directory


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")


class ReportTest(unittest.TestCase):
    def test_aggregates_answer_and_retrieval_metrics(self) -> None:
        with workspace_directory("report") as root:
            prepared = root / "prepared.jsonl"
            retrieval = root / "retrieval.jsonl"
            scores = root / "scores.jsonl"
            output = root / "summary.json"
            write_jsonl(
                prepared,
                [
                    {"id": "a", "question_type": "type-1"},
                    {"id": "b", "question_type": "type-1"},
                ],
            )
            write_jsonl(
                retrieval,
                [
                    {
                        "id": "a",
                        "answer_session_ids": ["s1"],
                        "is_abstention": False,
                        "retrieved": [{"session_id": "s1"}],
                        "search_latency_ms": 10,
                    },
                    {
                        "id": "b",
                        "answer_session_ids": [],
                        "is_abstention": True,
                        "retrieved": [],
                        "search_latency_ms": 20,
                    },
                ],
            )
            write_jsonl(
                scores,
                [
                    {"id": "a", "is_correct": True},
                    {"id": "b", "is_correct": False},
                ],
            )
            summary = build_summary(prepared, retrieval, scores, output, "memory", 10)

        self.assertEqual(summary["accuracy"], 0.5)
        self.assertEqual(summary["accuracy_pct"], 50.0)
        self.assertEqual(summary["by_question_type"]["type-1"]["accuracy"], 0.5)
        self.assertEqual(summary["retrieval_recall_at_k"], 1.0)
        self.assertEqual(summary["retrieval_evaluated_cases"], 1)
        self.assertEqual(summary["avg_search_latency_ms"], 15.0)
        self.assertEqual(summary["failed_cases"], ["b"])


if __name__ == "__main__":
    unittest.main()
