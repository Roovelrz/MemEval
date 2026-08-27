from __future__ import annotations

import unittest

from memory_eval.dataset_integrity import build_dataset_validation


class DatasetIntegrityTest(unittest.TestCase):
    def test_validates_original_longmemeval_haystack_sessions(self) -> None:
        report = build_dataset_validation(
            [
                {
                    "question_id": "english-1",
                    "question": "What did I submit?",
                    "answer": "An application.",
                    "answer_session_ids": ["session-1"],
                    "haystack_session_ids": ["session-1"],
                    "haystack_dates": ["2024-01-01"],
                    "haystack_sessions": [
                        [{"role": "user", "content": "I submitted an application."}]
                    ],
                }
            ],
            source_case_count=1,
        )

        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["counts"]["actual_loaded_session_count"], 1)
        self.assertEqual(report["counts"]["actual_loaded_turn_count"], 1)
        self.assertEqual(report["counts"]["missing_evidence_id_count"], 0)

    def test_reports_selected_counts_duplicates_missing_evidence_and_timestamp_errors(self) -> None:
        report = build_dataset_validation(
            [
                {
                    "case_id": "case-1",
                    "question": "问题",
                    "gold_answer": "答案",
                    "evidence_session_ids": ["missing"],
                    "sessions": [
                        {"session_id": "same", "timestamp": "2024/01/01 (Mon) 08:00", "messages": []},
                        {"session_id": "same", "timestamp": "bad", "messages": []},
                    ],
                }
            ],
            source_case_count=20,
        )

        counts = report["counts"]
        self.assertEqual(counts["actual_loaded_case_count"], 1)
        self.assertEqual(counts["duplicate_session_id_count"], 1)
        self.assertEqual(counts["missing_evidence_id_count"], 1)
        self.assertEqual(counts["timestamp_anomaly_count"], 1)
        self.assertEqual(counts["unselected_case_count"], 19)
        self.assertEqual(counts["data_skipped_count"], 0)
        self.assertEqual(report["status"], "FAIL")


if __name__ == "__main__":
    unittest.main()
