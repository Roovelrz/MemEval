from __future__ import annotations

import json
import hashlib
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from scripts import run_answer_eval, run_judge_eval
from scripts.llm_eval_common import parse_judge_label, read_jsonl, render_answer_prompt, write_jsonl
from tests.helpers import workspace_directory


class LlmEvalRunnersTest(unittest.TestCase):
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
            with patch.object(run_answer_eval, "complete") as complete:
                self.assertEqual(run_answer_eval.run(args), 0)
                complete.assert_not_called()

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


if __name__ == "__main__":
    unittest.main()
