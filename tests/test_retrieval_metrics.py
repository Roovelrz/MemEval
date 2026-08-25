from __future__ import annotations

import unittest

from memory_eval.metrics.retrieval import retrieval_scores


class RetrievalMetricsTest(unittest.TestCase):
    def test_multiple_evidence_sessions(self) -> None:
        result = retrieval_scores(["a", "b"], ["b", "x"], is_abstention=False)
        self.assertEqual(result, {"recall_at_k": 0.5, "hit_at_k": 1.0})

    def test_abstention_is_skipped(self) -> None:
        self.assertIsNone(retrieval_scores(["a"], ["a"], is_abstention=True))


if __name__ == "__main__":
    unittest.main()
