from __future__ import annotations

import json
import unittest

from memory_eval.metrics.retrieval_report import build_retrieval_summary
from tests.helpers import workspace_directory


class RetrievalReportTest(unittest.TestCase):
    def test_aggregates_retrieval_and_excludes_abstention(self) -> None:
        rows = [
            {
                "id": "hit",
                "answer_session_ids": ["s1", "s2"],
                "retrieved": [{"session_id": "s1"}],
                "is_abstention": False,
                "search_latency_ms": 10,
            },
            {
                "id": "miss",
                "answer_session_ids": ["s3"],
                "retrieved": [],
                "is_abstention": False,
                "search_latency_ms": 20,
            },
            {
                "id": "abstain",
                "answer_session_ids": [],
                "retrieved": [],
                "is_abstention": True,
                "search_latency_ms": 30,
            },
        ]
        with workspace_directory("retrieval-report") as directory:
            source = directory / "retrieval.jsonl"
            source.write_text(
                "".join(json.dumps(row) + "\n" for row in rows),
                encoding="utf-8",
            )
            summary = build_retrieval_summary(source, directory / "summary.json", "reme", 10)

        self.assertEqual(summary["retrieval_evaluated_cases"], 2)
        self.assertEqual(summary["retrieval_hit_at_k"], 0.5)
        self.assertEqual(summary["retrieval_recall_at_k"], 0.25)
        self.assertEqual(summary["avg_search_latency_ms"], 20.0)
        self.assertEqual(summary["failed_cases"], ["miss"])


if __name__ == "__main__":
    unittest.main()
