from __future__ import annotations

import io
import json
import hashlib
import threading
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from scripts import run_answer_eval, run_judge_eval
from scripts.llm_eval_common import (
    calculate_usage_cost,
    complete,
    parse_judge_label,
    read_jsonl,
    render_answer_prompt,
    resolve_model_pricing,
    write_jsonl,
)
from tests.helpers import workspace_directory


class LlmEvalRunnersTest(unittest.TestCase):
    def test_length_finish_retries_once_with_8192_tokens(self) -> None:
        requested_limits: list[int] = []
        responses = [
            {
                "choices": [
                    {
                        "finish_reason": "length",
                        "message": {"content": "", "reasoning_content": "still thinking"},
                    }
                ]
            },
            {
                "choices": [
                    {"finish_reason": "stop", "message": {"content": "final answer"}}
                ],
                "usage": {"total_tokens": 10},
            },
        ]

        class FakeResponse:
            status = 200

            def __init__(self, payload: dict) -> None:
                self._body = io.BytesIO(json.dumps(payload).encode("utf-8"))

            def __enter__(self):
                return self

            def __exit__(self, *_: object) -> None:
                return None

            def read(self) -> bytes:
                return self._body.read()

        def fake_urlopen(request, timeout: float):
            del timeout
            requested_limits.append(json.loads(request.data.decode("utf-8"))["max_tokens"])
            return FakeResponse(responses[len(requested_limits) - 1])

        with patch("scripts.llm_eval_common.urllib.request.urlopen", side_effect=fake_urlopen):
            content, usage = complete(
                api_key="test-key",
                base_url="http://example.test/v1",
                model="fake-model",
                prompt="question",
                max_tokens=4096,
                temperature=0.0,
                timeout=5.0,
                retries=0,
                retry_backoff=0.0,
            )

        self.assertEqual(content, "final answer")
        self.assertEqual(requested_limits, [4096, 8192])
        self.assertEqual(usage["request_attempts"], 2)
        self.assertEqual(usage["length_recovery_count"], 1)
        self.assertEqual(usage["final_max_tokens"], 8192)

    def test_answer_and_judge_use_configured_concurrency(self) -> None:
        with workspace_directory("llm-concurrency") as directory:
            prepared = directory / "prepared.jsonl"
            answers = directory / "answers.jsonl"
            scores = directory / "scores.jsonl"
            write_jsonl(
                prepared,
                [
                    {"id": "case-1", "question": "问题1", "gold_answer": "答案1", "retrieved_context": []},
                    {"id": "case-2", "question": "问题2", "gold_answer": "答案2", "retrieved_context": []},
                ],
            )
            answer_args = SimpleNamespace(
                start=0,
                limit=0,
                workers=2,
                max_tokens=256,
                timeout=5.0,
                retries=0,
                retry_backoff=0.0,
                input=prepared,
                output=answers,
                failures=None,
                api_key_env="TEST_KEY",
                base_url_env="TEST_BASE",
                model_env="TEST_MODEL",
                api_key="test-key",
                base_url="http://example.test/v1",
                model="fake-answer",
                temperature=0.0,
                overwrite=False,
            )
            answer_barrier = threading.Barrier(2)

            def answer_complete(**_: object) -> tuple[str, dict[str, int]]:
                answer_barrier.wait(timeout=2)
                return "答案", {"total_tokens": 1}

            with patch.object(run_answer_eval, "complete", side_effect=answer_complete):
                self.assertEqual(run_answer_eval.run(answer_args), 0)
            self.assertEqual([row["id"] for row in read_jsonl(answers)], ["case-1", "case-2"])

            judge_args = SimpleNamespace(
                start=0,
                limit=0,
                workers=2,
                max_tokens=256,
                timeout=5.0,
                retries=0,
                retry_backoff=0.0,
                input=prepared,
                answers=answers,
                output=scores,
                failures=None,
                api_key_env="TEST_KEY",
                base_url_env="TEST_BASE",
                model_env="TEST_MODEL",
                api_key="test-key",
                base_url="http://example.test/v1",
                model="fake-judge",
                temperature=0.0,
                overwrite=False,
            )
            judge_barrier = threading.Barrier(2)

            def judge_complete(**_: object) -> tuple[str, dict[str, int]]:
                judge_barrier.wait(timeout=2)
                return json.dumps({"label": "CORRECT"}), {"total_tokens": 1}

            with patch.object(run_judge_eval, "complete", side_effect=judge_complete):
                self.assertEqual(run_judge_eval.run(judge_args), 0)
            self.assertEqual([row["id"] for row in read_jsonl(scores)], ["case-1", "case-2"])

    def test_deepseek_v4_flash_cost_uses_cache_hit_miss_and_output_rates(self) -> None:
        pricing = resolve_model_pricing("deepseek-v4-flash")
        cost = calculate_usage_cost(
            {
                "prompt_tokens": 1_500_000,
                "prompt_cache_hit_tokens": 1_000_000,
                "prompt_cache_miss_tokens": 500_000,
                "completion_tokens": 100_000,
            },
            pricing,
        )

        self.assertIsNotNone(pricing)
        self.assertIsNotNone(cost)
        self.assertAlmostEqual(cost["total_cost_usd"], 0.1008)

    def test_answer_prompt_contains_question_date_and_structured_memory_timestamp(self) -> None:
        prompt = render_answer_prompt(
            {
                "question_date": "2024-02-01",
                "question": "过去了多少天？",
                "retrieved_context": [
                    '<memory rank="1">\nsession_id: "s-1"\ntimestamp: "2024-01-25"\ncontent:\n已提交。\n</memory>'
                ],
            }
        )

        self.assertIn("Question date: 2024-02-01", prompt)
        self.assertIn('timestamp: "2024-01-25"', prompt)

    def test_judge_label_parser_accepts_json_or_one_unambiguous_plain_label(self) -> None:
        self.assertEqual(parse_judge_label('{"label": "CORRECT"}'), "CORRECT")
        self.assertEqual(parse_judge_label("The generated answer is WRONG."), "WRONG")
        with self.assertRaises(ValueError):
            parse_judge_label("It is not WRONG; it is CORRECT.")

    def test_answer_runner_writes_rows_and_resumes(self) -> None:
        with workspace_directory("answer-runner") as directory:
            prepared = directory / "prepared.jsonl"
            answers = directory / "answers.jsonl"
            write_jsonl(
                prepared,
                [
                    {
                        "id": "case-1",
                        "question": "我喜欢什么？",
                        "gold_answer": "茶",
                        "retrieved_context": ["用户说自己喜欢茶。"],
                    }
                ],
            )
            args = SimpleNamespace(
                start=0,
                limit=0,
                max_tokens=256,
                timeout=5.0,
                retries=0,
                retry_backoff=0.0,
                input=prepared,
                output=answers,
                failures=None,
                api_key_env="TEST_KEY",
                base_url_env="TEST_BASE",
                model_env="TEST_MODEL",
                api_key="test-key",
                base_url="http://example.test/v1",
                model="fake-answer",
                temperature=0.0,
                overwrite=False,
            )
            with patch.object(run_answer_eval, "complete", return_value=("茶", {"total_tokens": 1})) as complete:
                self.assertEqual(run_answer_eval.run(args), 0)
                complete.assert_called_once()
            answer_row = read_jsonl(answers)[0]
            self.assertEqual(answer_row["generated_answer"], "茶")
            self.assertEqual(
                hashlib.sha256((directory / "answer_prompts" / "case-1.txt").read_bytes()).hexdigest(),
                answer_row["prompt_sha256"],
            )
            write_jsonl(
                directory / "answer_failures.jsonl",
                [{"id": "case-1", "stage": "answer", "error": "old failure"}],
            )
            with patch.object(run_answer_eval, "complete") as complete:
                self.assertEqual(run_answer_eval.run(args), 0)
                complete.assert_not_called()
            self.assertEqual(read_jsonl(directory / "answer_failures.jsonl"), [])
            summary = json.loads((directory / "answer_summary.json").read_text(encoding="utf-8"))
            self.assertEqual(summary["successful_rows"], 1)
            self.assertEqual(summary["failed_rows"], 0)

    def test_judge_runner_parses_label_and_aggregates_accuracy(self) -> None:
        with workspace_directory("judge-runner") as directory:
            prepared = directory / "prepared.jsonl"
            answers = directory / "answers.jsonl"
            scores = directory / "scores.jsonl"
            write_jsonl(
                prepared,
                [
                    {"id": "case-1", "question": "问题", "gold_answer": "答案", "retrieved_context": []},
                    {"id": "case-2", "question": "问题2", "gold_answer": "答案2", "retrieved_context": []},
                ],
            )
            write_jsonl(
                answers,
                [
                    {"id": "case-1", "generated_answer": "答案"},
                    {"id": "case-2", "generated_answer": "错误"},
                ],
            )
            args = SimpleNamespace(
                start=0,
                limit=0,
                max_tokens=256,
                timeout=5.0,
                retries=0,
                retry_backoff=0.0,
                input=prepared,
                answers=answers,
                output=scores,
                failures=None,
                api_key_env="TEST_KEY",
                base_url_env="TEST_BASE",
                model_env="TEST_MODEL",
                api_key="test-key",
                base_url="http://example.test/v1",
                model="fake-judge",
                temperature=0.0,
                overwrite=False,
            )
            responses = [(json.dumps({"label": "CORRECT"}), {}), (json.dumps({"label": "WRONG"}), {})]
            with patch.object(run_judge_eval, "complete", side_effect=responses):
                self.assertEqual(run_judge_eval.run(args), 0)
            summary = json.loads((directory / "judge_summary.json").read_text(encoding="utf-8"))
            self.assertEqual(summary["successful_rows"], 2)
            self.assertEqual(summary["correct_rows"], 1)
            self.assertEqual(summary["accuracy"], 0.5)
            first_score = read_jsonl(scores)[0]
            self.assertEqual(
                hashlib.sha256((directory / "judge_prompts" / "case-1.txt").read_bytes()).hexdigest(),
                first_score["prompt_sha256"],
            )
            write_jsonl(
                directory / "judge_failures.jsonl",
                [{"id": "case-1", "stage": "judge", "error": "old failure"}],
            )
            with patch.object(run_judge_eval, "complete") as complete:
                self.assertEqual(run_judge_eval.run(args), 0)
                complete.assert_not_called()
            self.assertEqual(read_jsonl(directory / "judge_failures.jsonl"), [])


if __name__ == "__main__":
    unittest.main()
