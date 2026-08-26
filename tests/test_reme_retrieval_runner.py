from __future__ import annotations

import json
import unittest

from scripts.run_reme_retrieval_eval import (
    deduplicate_sessions,
    evaluate_retrieval,
    normalize_case,
    render_answer_context,
    snapshot_eval_code,
)
from tests.helpers import workspace_directory


class ReMeRetrievalRunnerTest(unittest.TestCase):
    def test_eval_code_snapshot_records_exact_source_hashes(self) -> None:
        with workspace_directory("eval-code-snapshot") as directory:
            snapshot = snapshot_eval_code(directory, {"commit": "abc", "dirty": True})
            manifest = json.loads(
                (directory / "eval_code_snapshot" / "manifest.json").read_text(encoding="utf-8")
            )

            self.assertGreater(snapshot["file_count"], 0)
            self.assertEqual(manifest["git_commit"], "abc")
            self.assertTrue(manifest["git_dirty"])
            self.assertTrue(any(item["path"] == "scripts/run_reme_retrieval_eval.py" for item in manifest["files"]))

    def test_normalizes_clean_case_and_preserves_evidence(self) -> None:
        case = normalize_case(
            {
                "case_id": "case-1",
                "question": "记得什么？",
                "gold_answer": "答案",
                "question_date": "2024-01-03",
                "answer_session_ids": ["s-2"],
                "sessions": [
                    {
                        "session_id": "s-1",
                        "timestamp": "2024-01-01",
                        "turns": [{"role": "user", "content": "普通内容"}],
                    },
                    {
                        "session_id": "s-2",
                        "timestamp": "2024-01-02",
                        "is_evidence_session": True,
                        "turns": [{"role": "assistant", "content": "证据"}],
                    },
                ],
            },
            0,
        )

        self.assertEqual(case["case_id"], "case-1")
        self.assertEqual(case["question_date"], "2024-01-03")
        self.assertEqual(case["evidence_session_ids"], ["s-2"])
        self.assertEqual(case["sessions"][1]["messages"][0]["content"], "证据")

    def test_normalizes_original_longmemeval_shape(self) -> None:
        case = normalize_case(
            {
                "question_id": "raw-1",
                "question": "问题",
                "answer": "答案",
                "answer_session_ids": ["s-1"],
                "haystack_session_ids": ["s-1"],
                "haystack_dates": ["2024-01-01"],
                "haystack_sessions": [[{"role": "user", "content": "内容"}]],
            },
            0,
        )

        self.assertEqual(case["case_id"], "raw-1")
        self.assertEqual(case["sessions"][0]["session_id"], "s-1")
        self.assertEqual(case["evidence_session_ids"], ["s-1"])

    def test_deduplicates_chunks_before_session_metrics(self) -> None:
        path_map = {"daily/case/s-1.md": "s-1", "daily/case/s-2.md": "s-2"}
        retrieved = deduplicate_sessions(
            [
                {"path": "daily/case/s-1.md", "score": 3.0, "text": "chunk 1"},
                {"path": "daily/case/s-1.md", "score": 2.0, "text": "chunk 2"},
                {"path": "daily/case/s-2.md", "score": 1.0, "text": "chunk 3"},
            ],
            top_k=10,
            path_map=path_map,
        )

        self.assertEqual([item["session_id"] for item in retrieved], ["s-1", "s-2"])
        self.assertEqual(evaluate_retrieval(retrieved, ["s-2"]), {"hit": 1, "recall": 1.0, "mrr": 0.5})

    def test_answer_context_restores_session_timestamp_outside_reme_chunk(self) -> None:
        context = render_answer_context(
            {
                "rank": 2,
                "session_id": "evidence-1",
                "timestamp": "2024-01-02T10:00:00Z",
                "score": 3.5,
                "text": "# Conversation Session\n\n用户两天前提交了申请。",
            }
        )

        self.assertIn('session_id: "evidence-1"', context)
        self.assertIn('timestamp: "2024-01-02T10:00:00Z"', context)
        self.assertIn("<memory rank=\"2\">", context)


if __name__ == "__main__":
    unittest.main()
