"""Run ReMe retrieval, Answer generation, and Judge as one reproducible job.

The stages remain independently runnable.  This script only orchestrates
them and keeps all artifacts for a run under one directory:

    retrieval -> prepared.jsonl -> answers.jsonl -> scores.jsonl -> trace/ -> report/

It intentionally does not put API keys in command lines or JSON artifacts.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from scripts.llm_eval_common import (
        ANSWER_PROMPT_SHA256,
        ANSWER_PROMPT_VERSION,
        JUDGE_PROMPT_SHA256,
        JUDGE_PROMPT_VERSION,
    )
except ModuleNotFoundError:  # pragma: no cover - direct script execution path
    from llm_eval_common import (
        ANSWER_PROMPT_SHA256,
        ANSWER_PROMPT_VERSION,
        JUDGE_PROMPT_SHA256,
        JUDGE_PROMPT_VERSION,
    )


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from memory_eval.dataset_registry import (
    DEFAULT_DATASET_ID,
    default_output_root,
    resolve_dataset,
)
DETAILED_DIR_NAME = "Detailed Trace Report"
SUMMARY_DIR_NAME = "Trace Summary"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run ReMe retrieval + Answer + Judge")
    parser.add_argument("--dataset", default=DEFAULT_DATASET_ID, help="Registered dataset ID or a dataset path")
    parser.add_argument("--data", type=Path, default=None, help="Dataset path override kept for backward compatibility")
    parser.add_argument("--cases", "--limit", dest="cases", type=int, default=1, help="0 means all")
    parser.add_argument("--start", type=int, default=0)
    parser.add_argument("--shuffle", action="store_true")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--top-k", type=int, default=10)
    parser.add_argument("--search-multiplier", type=int, default=3)
    parser.add_argument("--min-score", type=float, default=0.0)
    parser.add_argument("--base-port", type=int, default=23330)
    parser.add_argument("--startup-timeout", type=float, default=60.0)
    parser.add_argument("--reme-cmd", default=None)
    parser.add_argument("--reme-config", type=Path, default=None)
    parser.add_argument("--vector-weight", type=float, default=0.0)
    parser.add_argument("--memory-model", default="none", help="label stored for the retrieval stage")
    parser.add_argument("--memory-adapter", default="reme", choices=("reme",))
    parser.add_argument(
        "--retrieval-workers",
        type=int,
        default=2,
        help="Concurrent isolated ReMe services; use 1 locally if memory is tight",
    )
    parser.add_argument("--keep-workspaces", action="store_true")
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--run-id", default="")
    parser.add_argument("--baseline-run", type=Path, default=None, help="optional prior run for trace comparison")

    parser.add_argument("--answer-output", type=Path, default=None)
    parser.add_argument("--answer-api-key-env", default="DEEPSEEK_API_KEY")
    parser.add_argument("--answer-base-url-env", default="DEEPSEEK_BASE_URL")
    parser.add_argument("--answer-model-env", default="DEEPSEEK_MODEL")
    parser.add_argument("--answer-base-url", default=None)
    parser.add_argument("--answer-model", default=None)
    parser.add_argument("--answer-max-tokens", type=int, default=4096)
    parser.add_argument("--answer-temperature", type=float, default=0.0)
    parser.add_argument("--answer-timeout", type=float, default=120.0)
    parser.add_argument("--answer-retries", type=int, default=3)
    parser.add_argument("--answer-workers", type=int, default=4, help="Concurrent Answer API requests")
    parser.add_argument("--answer-cache-hit-input-price", type=float, default=None, help="USD per 1M tokens")
    parser.add_argument("--answer-cache-miss-input-price", type=float, default=None, help="USD per 1M tokens")
    parser.add_argument("--answer-output-price", type=float, default=None, help="USD per 1M tokens")
    parser.add_argument("--answer-price-multiplier", type=float, default=1.0)

    parser.add_argument("--judge-output", type=Path, default=None)
    parser.add_argument("--judge-api-key-env", default="DEEPSEEK_API_KEY")
    parser.add_argument("--judge-base-url-env", default="DEEPSEEK_BASE_URL")
    parser.add_argument("--judge-model-env", default="DEEPSEEK_MODEL")
    parser.add_argument("--judge-base-url", default=None)
    parser.add_argument("--judge-model", default=None)
    parser.add_argument("--judge-max-tokens", type=int, default=4096)
    parser.add_argument("--judge-temperature", type=float, default=0.0)
    parser.add_argument("--judge-timeout", type=float, default=120.0)
    parser.add_argument("--judge-retries", type=int, default=3)
    parser.add_argument("--judge-workers", type=int, default=4, help="Concurrent Judge API requests")
    parser.add_argument("--judge-cache-hit-input-price", type=float, default=None, help="USD per 1M tokens")
    parser.add_argument("--judge-cache-miss-input-price", type=float, default=None, help="USD per 1M tokens")
    parser.add_argument("--judge-output-price", type=float, default=None, help="USD per 1M tokens")
    parser.add_argument("--judge-price-multiplier", type=float, default=1.0)
    return parser.parse_args()


def _stage_command(script: Path, *args: str) -> list[str]:
    return [sys.executable, str(script), *args]


def _run_stage(name: str, command: list[str]) -> int:
    print(f"\n=== {name} ===", flush=True)
    completed = subprocess.run(command, cwd=str(REPO_ROOT), check=False)
    return completed.returncode


def _read_optional(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"read_error": "invalid JSON"}
    return value if isinstance(value, dict) else {"read_error": "expected JSON object"}


def _output_path(value: Path | None, run_dir: Path, default_name: str) -> Path:
    if value is None:
        return run_dir / default_name
    return value.resolve() if value.is_absolute() else run_dir / value


def run(args: argparse.Namespace) -> int:
    run_started_at = datetime.now(timezone.utc)
    if args.cases < 0 or args.start < 0:
        raise ValueError("--cases/--limit and --start must be non-negative")
    if args.top_k < 1 or args.search_multiplier < 1:
        raise ValueError("--top-k and --search-multiplier must be positive")
    if args.retrieval_workers < 1 or args.answer_workers < 1 or args.judge_workers < 1:
        raise ValueError("Retrieval, Answer, and Judge workers must be positive")
    dataset_path, dataset_spec = resolve_dataset(args.dataset, args.data)
    if not args.run_id.strip():
        dataset_slug = "".join(
            character if character.isalnum() else "-"
            for character in str(dataset_spec["dataset_id"]).lower()
        ).strip("-")
        args.run_id = f"reme_{dataset_slug}_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"

    output_root = args.output_dir.resolve() if args.output_dir else default_output_root(dataset_spec, args.memory_adapter)
    run_dir = output_root / args.run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    registered_case_count = dataset_spec.get("case_count")
    selected_case_count = (
        max(0, int(registered_case_count) - args.start)
        if args.cases == 0 and isinstance(registered_case_count, int)
        else min(args.cases, max(0, int(registered_case_count) - args.start))
        if isinstance(registered_case_count, int)
        else args.cases
    )
    prepared_path = run_dir / "prepared.jsonl"
    answers_path = _output_path(args.answer_output, run_dir, "answers.jsonl")
    scores_path = _output_path(args.judge_output, run_dir, "scores.jsonl")

    orchestration_config = {
        "task": "reme_retrieval_answer_judge",
        "run_id": args.run_id,
        "dataset": str(dataset_path),
        "dataset_id": dataset_spec["dataset_id"],
        "dataset_name": dataset_spec["dataset_name"],
        "dataset_version": dataset_spec.get("version"),
        "source_dataset": dataset_spec["source_dataset"],
        "language": dataset_spec["language"],
        "translated": bool(dataset_spec["translated"]),
        "case_count": selected_case_count,
        "dataset_case_count": registered_case_count,
        "output_dir": str(run_dir),
        "baseline_run": str(args.baseline_run.resolve()) if args.baseline_run else None,
        "retrieval": {
            "top_k": args.top_k,
            "cases": args.cases,
            "start": args.start,
            "shuffle": args.shuffle,
            "seed": args.seed,
            "search_multiplier": args.search_multiplier,
            "min_score": args.min_score,
            "base_port": args.base_port,
            "startup_timeout": args.startup_timeout,
            "reme_cmd": args.reme_cmd,
            "reme_config": str(args.reme_config.resolve()) if args.reme_config else None,
            "vector_weight": args.vector_weight,
            "model_label": args.memory_model,
            "keep_workspaces": args.keep_workspaces,
            "workers": args.retrieval_workers,
        },
        "answer": {
            "output": str(answers_path),
            "api_key_env": args.answer_api_key_env,
            "base_url_env": args.answer_base_url_env,
            "model_env": args.answer_model_env,
            "base_url_override": args.answer_base_url,
            "model_override": args.answer_model,
            "max_tokens": args.answer_max_tokens,
            "temperature": args.answer_temperature,
            "timeout": args.answer_timeout,
            "retries": args.answer_retries,
            "workers": args.answer_workers,
            "cache_hit_input_price": args.answer_cache_hit_input_price,
            "cache_miss_input_price": args.answer_cache_miss_input_price,
            "output_price": args.answer_output_price,
            "price_multiplier": args.answer_price_multiplier,
            "prompt_version": ANSWER_PROMPT_VERSION,
            "prompt_template_sha256": ANSWER_PROMPT_SHA256,
        },
        "judge": {
            "output": str(scores_path),
            "api_key_env": args.judge_api_key_env,
            "base_url_env": args.judge_base_url_env,
            "model_env": args.judge_model_env,
            "base_url_override": args.judge_base_url,
            "model_override": args.judge_model,
            "max_tokens": args.judge_max_tokens,
            "temperature": args.judge_temperature,
            "timeout": args.judge_timeout,
            "retries": args.judge_retries,
            "workers": args.judge_workers,
            "cache_hit_input_price": args.judge_cache_hit_input_price,
            "cache_miss_input_price": args.judge_cache_miss_input_price,
            "output_price": args.judge_output_price,
            "price_multiplier": args.judge_price_multiplier,
            "prompt_version": JUDGE_PROMPT_VERSION,
            "prompt_template_sha256": JUDGE_PROMPT_SHA256,
        },
        "start_time_utc": run_started_at.isoformat(),
    }
    (run_dir / "end_to_end_run_config.json").write_text(
        json.dumps(orchestration_config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    retrieval_script = Path(__file__).with_name("run_reme_retrieval_eval.py")
    retrieval_args = [
        "--dataset",
        str(dataset_spec["dataset_id"]),
        "--data",
        str(dataset_path),
        "--cases",
        str(args.cases),
        "--start",
        str(args.start),
        "--top-k",
        str(args.top_k),
        "--search-multiplier",
        str(args.search_multiplier),
        "--min-score",
        str(args.min_score),
        "--seed",
        str(args.seed),
        "--base-port",
        str(args.base_port),
        "--startup-timeout",
        str(args.startup_timeout),
        "--output-dir",
        str(output_root),
        "--run-id",
        args.run_id,
        "--model",
        args.memory_model,
        "--memory-adapter",
        args.memory_adapter,
        "--workers",
        str(args.retrieval_workers),
        "--vector-weight",
        str(args.vector_weight),
    ]
    if args.shuffle:
        retrieval_args.append("--shuffle")
    if args.reme_cmd:
        retrieval_args.extend(["--reme-cmd", args.reme_cmd])
    if args.reme_config:
        retrieval_args.extend(["--reme-config", str(args.reme_config.resolve())])
    if args.keep_workspaces:
        retrieval_args.append("--keep-workspaces")
    retrieval_code = _run_stage("Retrieval", _stage_command(retrieval_script, *retrieval_args))

    stage_codes: dict[str, int | None] = {
        "retrieval": retrieval_code,
        "answer": None,
        "judge": None,
        "trace": None,
        "html": None,
    }
    if retrieval_code == 0:
        answer_script = Path(__file__).with_name("run_answer_eval.py")
        answer_args = [
            "--input",
            str(prepared_path),
            "--output",
            str(answers_path),
            "--api-key-env",
            args.answer_api_key_env,
            "--base-url-env",
            args.answer_base_url_env,
            "--model-env",
            args.answer_model_env,
            "--max-tokens",
            str(args.answer_max_tokens),
            "--temperature",
            str(args.answer_temperature),
            "--timeout",
            str(args.answer_timeout),
            "--retries",
            str(args.answer_retries),
            "--workers",
            str(args.answer_workers),
            "--price-multiplier",
            str(args.answer_price_multiplier),
        ]
        if args.answer_cache_hit_input_price is not None:
            answer_args.extend(["--cache-hit-input-price", str(args.answer_cache_hit_input_price)])
        if args.answer_cache_miss_input_price is not None:
            answer_args.extend(["--cache-miss-input-price", str(args.answer_cache_miss_input_price)])
        if args.answer_output_price is not None:
            answer_args.extend(["--output-price", str(args.answer_output_price)])
        if args.answer_base_url:
            answer_args.extend(["--base-url", args.answer_base_url])
        if args.answer_model:
            answer_args.extend(["--model", args.answer_model])
        answer_code = _run_stage("Answer", _stage_command(answer_script, *answer_args))
        stage_codes["answer"] = answer_code

        if answer_code == 0:
            judge_script = Path(__file__).with_name("run_judge_eval.py")
            judge_args = [
                "--input",
                str(prepared_path),
                "--answers",
                str(answers_path),
                "--output",
                str(scores_path),
                "--api-key-env",
                args.judge_api_key_env,
                "--base-url-env",
                args.judge_base_url_env,
                "--model-env",
                args.judge_model_env,
                "--max-tokens",
                str(args.judge_max_tokens),
                "--temperature",
                str(args.judge_temperature),
                "--timeout",
                str(args.judge_timeout),
                "--retries",
                str(args.judge_retries),
                "--workers",
                str(args.judge_workers),
                "--price-multiplier",
                str(args.judge_price_multiplier),
            ]
            if args.judge_cache_hit_input_price is not None:
                judge_args.extend(["--cache-hit-input-price", str(args.judge_cache_hit_input_price)])
            if args.judge_cache_miss_input_price is not None:
                judge_args.extend(["--cache-miss-input-price", str(args.judge_cache_miss_input_price)])
            if args.judge_output_price is not None:
                judge_args.extend(["--output-price", str(args.judge_output_price)])
            if args.judge_base_url:
                judge_args.extend(["--base-url", args.judge_base_url])
            if args.judge_model:
                judge_args.extend(["--model", args.judge_model])
            judge_code = _run_stage("Judge", _stage_command(judge_script, *judge_args))
            stage_codes["judge"] = judge_code

    model_stages_finished_at = datetime.now(timezone.utc)
    run_metadata = {
        "run_id": args.run_id,
        "start_time_utc": run_started_at.isoformat(),
        "end_time_utc": model_stages_finished_at.isoformat(),
        "stage_exit_codes_before_trace": stage_codes,
        "answer_prompt_version": ANSWER_PROMPT_VERSION,
        "answer_prompt_template_sha256": ANSWER_PROMPT_SHA256,
        "judge_prompt_version": JUDGE_PROMPT_VERSION,
        "judge_prompt_template_sha256": JUDGE_PROMPT_SHA256,
    }
    (run_dir / "run_metadata.json").write_text(
        json.dumps(run_metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    trace_script = Path(__file__).with_name("build_trace_report.py")
    trace_args = ["--run-dir", str(run_dir), "--data", str(dataset_path)]
    if args.baseline_run:
        trace_args.extend(["--baseline-run", str(args.baseline_run.resolve())])
    trace_code = _run_stage("Trace report", _stage_command(trace_script, *trace_args))
    stage_codes["trace"] = trace_code

    layout_script = Path(__file__).with_name("organize_result_layout.py")
    html_code = _run_stage(
        "Result layout + HTML dashboard",
        _stage_command(layout_script, "--run-dir", str(run_dir)),
    )
    stage_codes["html"] = html_code

    detailed_dir = run_dir / DETAILED_DIR_NAME
    summary_dir = run_dir / SUMMARY_DIR_NAME
    dashboard_dir = summary_dir / "Dashboard"

    def relocated(path: Path) -> Path:
        resolved = path.resolve()
        try:
            relative = resolved.relative_to(run_dir.resolve())
        except ValueError:
            return resolved
        return detailed_dir / relative

    final_prepared_path = relocated(prepared_path)
    final_answers_path = relocated(answers_path)
    final_scores_path = relocated(scores_path)

    run_finished_at = datetime.now(timezone.utc)
    final_summary = {
        "task": "reme_retrieval_answer_judge",
        "run_id": args.run_id,
        "run_dir": str(run_dir),
        "detailed_trace_report_dir": str(detailed_dir),
        "trace_summary_dir": str(summary_dir),
        "stage_exit_codes": stage_codes,
        "start_time_utc": run_started_at.isoformat(),
        "end_time_utc": run_finished_at.isoformat(),
        "duration_ms": (run_finished_at - run_started_at).total_seconds() * 1000,
        "retrieval": _read_optional(detailed_dir / "summary.json"),
        "answer": _read_optional(final_answers_path.parent / "answer_summary.json"),
        "judge": _read_optional(final_scores_path.parent / "judge_summary.json"),
        "artifacts": {
            "prepared": str(final_prepared_path),
            "answers": str(final_answers_path),
            "scores": str(final_scores_path),
            "trace_summary": str(detailed_dir / "trace" / "trace_summary.md"),
            "trace_index": str(detailed_dir / "trace" / "trace_index.md"),
            "judge_review": str(detailed_dir / "trace" / "judge_review.md"),
            "html_dashboard": str(summary_dir / "Dashboard.html"),
            "html_report_manifest": str(dashboard_dir / "report_manifest.json"),
            "concise_summary": str(summary_dir / "summary.json"),
        },
    }
    final_summary_dir = detailed_dir if detailed_dir.is_dir() else run_dir
    (final_summary_dir / "end_to_end_summary.json").write_text(
        json.dumps(final_summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print("\n=== End-to-end summary ===")
    print(json.dumps(final_summary, ensure_ascii=False, indent=2))
    return 0 if all(code == 0 for code in stage_codes.values()) else 2


if __name__ == "__main__":
    raise SystemExit(run(parse_args()))
