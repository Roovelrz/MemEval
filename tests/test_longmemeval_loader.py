from __future__ import annotations

import json
import unittest
from pathlib import Path

from memory_eval.datasets.longmemeval import load_longmemeval
from tests.helpers import workspace_directory


def record(case_id: str = "case_abs") -> dict:
    return {
        "question_id": case_id,
        "question_type": "knowledge-update",
        "question": "What is current?",
        "answer": "new",
        "question_date": "2024/02/01 (Thu) 00:00",
        "haystack_session_ids": ["new", "old"],
        "haystack_dates": ["2024/01/02 (Tue) 10:00", "2024/01/01 (Mon) 10:00"],
        "haystack_sessions": [
            [{"role": "user", "content": "new"}],
            [{"role": "user", "content": "old"}],
        ],
        "answer_session_ids": ["new"],
    }


class LongMemEvalLoaderTest(unittest.TestCase):
    def write(self, directory: Path, payload: object) -> Path:
        path = directory / "data.json"
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def test_maps_fields_sorts_sessions_and_marks_abstention(self) -> None:
        with workspace_directory("loader-map") as directory:
            case = load_longmemeval(self.write(directory, [record()]))[0]
        self.assertEqual(case.id, "case_abs")
        self.assertEqual(case.gold_answer, "new")
        self.assertEqual([session.session_id for session in case.sessions], ["old", "new"])
        self.assertTrue(case.is_abstention)

    def test_rejects_mismatched_haystack_lengths(self) -> None:
        item = record("case")
        item["haystack_dates"] = item["haystack_dates"][:1]
        with workspace_directory("loader-invalid") as directory:
            with self.assertRaisesRegex(ValueError, "haystack lengths differ"):
                load_longmemeval(self.write(directory, [item]))


if __name__ == "__main__":
    unittest.main()
