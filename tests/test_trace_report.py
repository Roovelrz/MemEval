from __future__ import annotations

import json
import unittest

from memory_eval.trace_report import build_trace_report
from scripts.llm_eval_common import write_jsonl
from tests.helpers import workspace_directory


class TraceReportTest(unittest.TestCase):
    def test_builds_pass_and_retrieval_miss_traces_from_existing_artifacts(self) -> None:
        with workspace_directory("trace-report") as directory:
            dataset_path = directory / "dataset.json"
            dataset_path.write_text(
                json.dumps(
                    {
                        "dataset_id": "fixture-v1",
                        "cases": [
                            {
                                "case_id": "case-pass",
                                "question_type": "single-session-user",
                                "question": "通勤多久？",
                                "gold_answer": "45分钟",
                                "answer_session_ids": ["evidence-pass"],
                                "sessions": [
                                    {
                                        "session_id": "evidence-pass",
                                        "timestamp": "2026-01-01",
                                        "turns": [
                                            {
                                                "role": "user",
                                                "content": "我单程通勤45分钟。",
                                                "has_answer": True,
                                            }
                                        ],
                                    },
                                    {
                                        "session_id": "distractor-pass",
                                        "timestamp": "2026-01-02",
                                        "turns": [],
                                    },
                                ],
                            },
                            {
                                "case_id": "case-miss",
                                "question_type": "single-session-user",
                                "question": "最喜欢什么饮料？",
                                "gold_answer": "茶",
                                "answer_session_ids": ["evidence-miss"],
                                "sessions": [
                                    {
                                        "session_id": "evidence-miss",
                                        "timestamp": "2026-01-03",
                                        "turns": [
                                            {
                                                "role": "user",
                                                "content": "我最喜欢茶。",
                                                "has_answer": True,
                                            }
                                        ],
                                    },
                                    {
                                        "session_id": "distractor-miss",
                                        "timestamp": "2026-01-04",
                                        "turns": [],
                                    },
                                ],
                            },
                        ],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            (directory / "run_config.json").write_text(
                json.dumps({"dataset": str(dataset_path), "top_k": 2}), encoding="utf-8"
            )
            write_jsonl(
                directory / "retrieval.jsonl",
                [
                    {
                        "case_id": "case-pass",
                        "question": "通勤多久？",
                        "gold_answer": "45分钟",
                        "question_type": "single-session-user",
                        "evidence_session_ids": ["evidence-pass"],
                        "session_count": 2,
                        "hit_at_k": 1,
                        "recall_at_k": 1.0,
                        "mrr": 1.0,
                        "retrieved": [
                            {
                                "rank": 1,
                                "session_id": "evidence-pass",
                                "score": 2.0,
                                "text": "我单程通勤45分钟。",
                            },
                            {
                                "rank": 2,
                                "session_id": "distractor-pass",
                                "score": 1.0,
                                "text": "无关内容",
                            },
                        ],
                    },
                    {
                        "case_id": "case-miss",
                        "question": "最喜欢什么饮料？",
                        "gold_answer": "茶",
                        "question_type": "single-session-user",
                        "evidence_session_ids": ["evidence-miss"],
                        "session_count": 2,
                        "hit_at_k": 0,
                        "recall_at_k": 0.0,
                        "mrr": 0.0,
                        "retrieved": [
                            {
                                "rank": 1,
                                "session_id": "distractor-miss",
                                "score": 1.0,
                                "text": "无关内容",
                            }
                        ],
                    },
                ],
            )
            write_jsonl(
                directory / "prepared.jsonl",
                [
                    {
                        "id": "case-pass",
                        "question": "通勤多久？",
                        "gold_answer": "45分钟",
                        "question_type": "single-session-user",
                        "retrieved_context": ["我单程通勤45分钟。", "无关内容"],
                    },
                    {
                        "id": "case-miss",
                        "question": "最喜欢什么饮料？",
                        "gold_answer": "茶",
                        "question_type": "single-session-user",
                        "retrieved_context": ["无关内容"],
                    },
                ],
            )
            write_jsonl(
                directory / "answers.jsonl",
                [
                    {"id": "case-pass", "generated_answer": "45分钟。", "model": "answer-model"},
                    {"id": "case-miss", "generated_answer": "茶", "model": "answer-model"},
                ],
            )
            write_jsonl(
                directory / "scores.jsonl",
                [
                    {
                        "id": "case-pass",
                        "is_correct": True,
                        "label": "CORRECT",
                        "judge_response": "```json\n{\"label\": \"CORRECT\"}\n```",
                        "model": "judge-model",
                    },
                    {
                        "id": "case-miss",
                        "is_correct": True,
                        "label": "CORRECT",
                        "judge_response": "CORRECT",
                        "model": "judge-model",
                    },
                ],
            )

            summary = build_trace_report(directory)

            self.assertEqual(summary["total_cases"], 2)
            self.assertEqual(summary["quadrants"]["A_retrieval_pass_answer_pass"], 1)
            self.assertEqual(summary["quadrants"]["D_retrieval_fail_answer_pass"], 1)
            self.assertEqual(summary["root_cause_distribution"]["PASS"], 1)
            self.assertEqual(summary["root_cause_distribution"]["RETRIEVAL_MISS"], 1)
            self.assertTrue((directory / "trace" / "trace_summary.md").is_file())
            self.assertTrue((directory / "trace" / "trace_index.md").is_file())
            self.assertTrue((directory / "trace" / "judge_review.md").is_file())

            trace_summary = (directory / "trace" / "trace_summary.md").read_text(encoding="utf-8")
            trace_index = (directory / "trace" / "trace_index.md").read_text(encoding="utf-8")
            self.assertIn("# Trace 汇总报告", trace_summary)
            self.assertIn("## 本次结果解读", trace_summary)
            self.assertIn("## Retrieval × Answer 四象限", trace_summary)
            self.assertIn("# Trace Index", trace_index)

            pass_trace = (directory / "trace" / "cases" / "case-pass.md").read_text(
                encoding="utf-8"
            )
            self.assertIn("Equivalent after whitespace and punctuation normalization.", pass_trace)
            self.assertIn("Successfully added sessions | NOT_RECORDED", pass_trace)
            self.assertIn("````text", pass_trace)


if __name__ == "__main__":
    unittest.main()
