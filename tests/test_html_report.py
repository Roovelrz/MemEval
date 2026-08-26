from __future__ import annotations

import hashlib
import json
import unittest

from memory_eval.html_report import build_html_report
from memory_eval.result_layout import organize_result_layout
from memory_eval.trace_report import build_trace_report
from scripts.llm_eval_common import write_jsonl
from tests.helpers import workspace_directory


class HtmlReportTest(unittest.TestCase):
    def test_builds_static_dashboard_without_mutating_trace_sources(self) -> None:
        with workspace_directory("html-report") as directory:
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
                                        "turns": [{"role": "user", "content": "我单程通勤45分钟。", "has_answer": True}],
                                    },
                                    {"session_id": "distractor-pass", "timestamp": "2026-01-02", "turns": []},
                                ],
                            }
                        ],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            (directory / "run_config.json").write_text(
                json.dumps({"dataset": str(dataset_path), "top_k": 2}),
                encoding="utf-8",
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
                        "search_latency_ms": 3.0,
                        "retrieved": [
                            {"rank": 1, "session_id": "evidence-pass", "score": 2.0, "text": "我单程通勤45分钟。"},
                            {"rank": 2, "session_id": "distractor-pass", "score": 1.0, "text": "无关内容"},
                        ],
                    }
                ],
            )
            write_jsonl(
                directory / "add_trace.jsonl",
                [{"case_id": "case-pass", "add_status": "PASS", "added_sessions": 2, "expected_sessions": 2, "added_evidence_sessions": 1, "expected_evidence_sessions": 1, "add_latency_ms": 1.0, "index_latency_ms": 2.0}],
            )
            write_jsonl(
                directory / "prepared.jsonl",
                [{"id": "case-pass", "question": "通勤多久？", "gold_answer": "45分钟", "question_type": "single-session-user", "retrieved_context": ["我单程通勤45分钟。", "无关内容"]}],
            )
            write_jsonl(
                directory / "answers.jsonl",
                [{"id": "case-pass", "generated_answer": "45分钟。", "model": "fixture", "latency_ms": 5.0, "usage": {"prompt_tokens": 100, "completion_tokens": 10, "total_tokens": 110}}],
            )
            write_jsonl(
                directory / "scores.jsonl",
                [{"id": "case-pass", "is_correct": True, "label": "CORRECT", "judge_response": "CORRECT", "model": "fixture", "latency_ms": 7.0, "usage": {"prompt_tokens": 50, "completion_tokens": 5, "total_tokens": 55}}],
            )
            (directory / "end_to_end_summary.json").write_text(
                json.dumps(
                    {
                        "run_dir": str(directory),
                        "artifacts": {"trace_summary": str(directory / "trace" / "trace_summary.md")},
                    }
                ),
                encoding="utf-8",
            )

            build_trace_report(directory)
            source_paths = [
                directory / "trace" / "trace_summary.json",
                directory / "trace" / "cases" / "case-pass.json",
            ]
            before = {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in source_paths}

            manifest = build_html_report(directory)

            after = {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in source_paths}
            self.assertEqual(before, after)
            self.assertEqual(manifest["case_page_count"], 1)
            self.assertGreaterEqual(manifest["page_count"], 30)
            for relative in manifest["files"]:
                self.assertTrue((directory / "report" / relative).is_file(), relative)

            home = (directory / "report" / "index.html").read_text(encoding="utf-8")
            case = (directory / "report" / "cases" / "case-pass.html").read_text(encoding="utf-8")
            self.assertIn("综合能力评分", home)
            self.assertIn("工程健康度", home)
            self.assertIn("端到端能力四象限分析", home)
            self.assertIn("hit_at_k", home)
            self.assertIn("证据数量分层表现", home)
            self.assertIn("EVIDENCE", case)
            self.assertIn("root_cause", case)
            self.assertIn("我单程通勤45分钟。", case)
            self.assertTrue((directory / "report" / "capabilities" / "single-session-user.html").is_file())
            self.assertTrue((directory / "report" / "performance" / "token-usage.html").is_file())

            layout = organize_result_layout(directory)
            detailed = directory / "Detailed Trace Report"
            concise = directory / "Trace Summary"
            self.assertEqual(
                sorted(path.name for path in directory.iterdir()),
                ["Detailed Trace Report", "Trace Summary"],
            )
            self.assertTrue((detailed / "retrieval.jsonl").is_file())
            self.assertTrue((detailed / "trace" / "cases" / "case-pass.json").is_file())
            self.assertTrue((detailed / "result_layout_manifest.json").is_file())
            self.assertTrue((concise / "Dashboard" / "index.html").is_file())
            self.assertTrue((concise / "Dashboard.html").is_file())
            self.assertTrue((concise / "trace_summary.md").is_file())
            self.assertEqual(
                sorted(path.name for path in concise.iterdir()),
                ["Dashboard", "Dashboard.html", "summary.json", "trace_summary.md"],
            )
            summary_entrypoint = (concise / "Dashboard.html").read_text(encoding="utf-8")
            self.assertIn("Dashboard/index.html", summary_entrypoint)
            concise_summary = json.loads((concise / "summary.json").read_text(encoding="utf-8"))
            self.assertEqual(concise_summary["total_cases"], 1)
            self.assertNotIn("cases", concise_summary)
            self.assertEqual(layout["case_page_count"], 1)
            end_to_end = json.loads(
                (detailed / "end_to_end_summary.json").read_text(encoding="utf-8")
            )
            self.assertEqual(end_to_end["trace_summary_dir"], str(concise))
            self.assertEqual(
                end_to_end["artifacts"]["html_dashboard"],
                str(concise / "Dashboard.html"),
            )


if __name__ == "__main__":
    unittest.main()
