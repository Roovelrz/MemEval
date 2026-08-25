from __future__ import annotations

import json
import unittest

from memory_eval.datasets.models import EvalCase, EvalSession, MemoryHit
from memory_eval.runners.longmemeval import LongMemEvalRunner
from tests.helpers import workspace_directory


class RecordingAdapter:
    def __init__(self) -> None:
        self.calls: list[tuple] = []

    def reset(self, namespace: str) -> None:
        self.calls.append(("reset", namespace))

    def add_session(self, namespace: str, session_id: str, timestamp: str, messages: list[dict]) -> None:
        self.calls.append(("add", namespace, session_id, timestamp))

    def search(self, namespace: str, query: str, top_k: int) -> list[MemoryHit]:
        self.calls.append(("search", namespace, query, top_k))
        return [MemoryHit("evidence", 1.0, {"session_id": "s2", "timestamp": "2024/01/02"})]


class LongMemEvalRunnerTest(unittest.TestCase):
    def test_memory_mode_adds_in_order_and_writes_contract(self) -> None:
        case = EvalCase(
            id="q1",
            question_type="single-session-user",
            question="what?",
            gold_answer="answer",
            question_date="2024/01/03",
            sessions=[
                EvalSession("s1", "2024/01/01", [{"role": "user", "content": "one"}]),
                EvalSession("s2", "2024/01/02", [{"role": "assistant", "content": "two"}]),
            ],
            answer_session_ids=["s2"],
            is_abstention=False,
        )
        adapter = RecordingAdapter()
        runner = LongMemEvalRunner(adapter)
        with workspace_directory("runner") as directory:
            prepared, retrieval = runner.prepare([case], "run", directory, "memory", 10)
            prepared_row = json.loads(prepared.read_text(encoding="utf-8"))
            retrieval_row = json.loads(retrieval.read_text(encoding="utf-8"))

        self.assertEqual([call[2] for call in adapter.calls if call[0] == "add"], ["s1", "s2"])
        self.assertEqual(adapter.calls[-1][2:], ("what?", 10))
        self.assertEqual(prepared_row["retrieved_context"], ["evidence"])
        self.assertEqual(retrieval_row["retrieved"][0]["session_id"], "s2")
        self.assertEqual(retrieval_row["namespace"], "longmemeval:run:q1")


if __name__ == "__main__":
    unittest.main()
