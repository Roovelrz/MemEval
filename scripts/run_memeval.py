"""Run the frozen eight-dimension MemEval benchmark through a System Adapter."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from dataset.build_pipeline import ReviewedBenchmark
from dataset.build_pipeline.release import DIMENSION_DIRECTORIES
from memory_eval.adapters.Trace import MemEvalTraceAdapter
from memory_eval.adapters.memory.reme import (
    ReMeCliMemoryAdapter,
    create_bm25_config,
    resolve_reme_command,
)
from memory_eval.dataset_registry import resolve_dataset
from memory_eval.result_layout import (
    DETAILED_DIR_NAME,
    SUMMARY_DIR_NAME,
    organize_result_layout,
    refresh_result_layout,
)
from memory_eval.runners import MemEvalRunConfig, MemEvalRunner
from memory_eval.systems import ReMeSystemAdapter


def select_artifacts(benchmark: ReviewedBenchmark, dimensions, case_ids, limit):
    selected_dimensions = dimensions or list(DIMENSION_DIRECTORIES)
    selected_ids = set(case_ids or [])
    rows = [
        artifact
        for dimension in selected_dimensions
        for artifact in benchmark.iter_cases(dimension)
        if not selected_ids or artifact.case["envelope"]["case_id"] in selected_ids
    ]
    if selected_ids:
        found = {row.case["envelope"]["case_id"] for row in rows}
        if missing := selected_ids - found:
            raise ValueError(f"Unknown case IDs: {sorted(missing)}")
    if limit is not None:
        if limit < 1:
            raise ValueError("--limit must be positive")
        rows = rows[:limit]
    if not rows:
        raise ValueError("No MemEval Cases matched the selection")
    return rows


def parser() -> argparse.ArgumentParser:
    command = argparse.ArgumentParser(description="Run MemEval-v0.1 with the ReMe System Adapter")
    command.add_argument("--dataset", default="MemEval-v0.1")
    command.add_argument("--data", help="formal MemEval release directory; overrides --dataset")
    command.add_argument("--dimension", action="append", choices=tuple(DIMENSION_DIRECTORIES))
    command.add_argument("--case-id", action="append")
    command.add_argument("--limit", type=int)
    command.add_argument("--top-k", type=int, default=10)
    command.add_argument("--search-multiplier", type=int, default=1)
    command.add_argument("--min-score", type=float, default=0.0)
    command.add_argument("--run-id")
    command.add_argument("--output-dir")
    command.add_argument("--context-batch", action="store_true",
                         help="performance mode: ingest an identical Context once for multiple Queries")
    command.add_argument("--reme-cmd")
    command.add_argument("--reme-config")
    command.add_argument("--reme-port", type=int, default=25000)
    command.add_argument("--reme-startup-timeout", type=float, default=60.0)
    command.add_argument("--vector-weight", type=float, default=0.0)
    command.add_argument("--answer-api-key-env", default="DEEPSEEK_API_KEY")
    command.add_argument("--answer-base-url-env", default="DEEPSEEK_BASE_URL")
    command.add_argument("--answer-model-env", default="DEEPSEEK_MODEL")
    command.add_argument("--answer-workers", type=int, default=4)
    command.add_argument("--answer-max-tokens", type=int, default=65536)
    command.add_argument("--judge-api-key-env", default="DEEPSEEK_API_KEY")
    command.add_argument("--judge-base-url-env", default="DEEPSEEK_BASE_URL")
    command.add_argument("--judge-model-env", default="DEEPSEEK_MODEL")
    command.add_argument("--judge-workers", type=int, default=4)
    command.add_argument("--judge-max-tokens", type=int, default=65536)
    command.add_argument(
        "--resume",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="resume an existing run-id by skipping completed cases (default: enabled)",
    )
    return command


def _run_llm_stage(name: str, script_name: str, arguments: list[str]) -> int:
    print(f"\n=== {name} ===", flush=True)
    completed = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / script_name), *arguments],
        cwd=REPO_ROOT,
        check=False,
    )
    return completed.returncode


def _default_run_id(dataset_id: str) -> str:
    dataset_slug = "".join(
        character if character.isalnum() else "-"
        for character in dataset_id.lower()
    ).strip("-")
    return f"reme_{dataset_slug}_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"


def _artifact_directory(run_dir: Path) -> Path:
    detailed_dir = run_dir / DETAILED_DIR_NAME
    if detailed_dir.is_dir():
        return detailed_dir
    if (run_dir / "results.jsonl").is_file() or (run_dir / "retrieval_run_config.json").is_file():
        return run_dir
    return detailed_dir


def run(args: argparse.Namespace) -> int:
    if args.answer_workers < 1 or args.judge_workers < 1:
        raise ValueError("Answer and Judge workers must be positive")
    if args.answer_max_tokens < 1 or args.judge_max_tokens < 1:
        raise ValueError("Answer and Judge max tokens must be positive")
    source, spec = resolve_dataset(args.dataset, args.data)
    if spec.get("adapter") not in {None, "memeval"} or not source.is_dir():
        raise ValueError("run_memeval requires a formal MemEval release directory")
    benchmark = ReviewedBenchmark(source)
    benchmark.assert_review_complete()
    artifacts = select_artifacts(benchmark, args.dimension, args.case_id, args.limit)

    run_id = args.run_id or _default_run_id(str(spec["dataset_id"]))
    output_root = Path(args.output_dir).resolve() if args.output_dir else REPO_ROOT / "results"
    run_dir = output_root / run_id
    organized_run = (
        (run_dir / DETAILED_DIR_NAME).is_dir()
        and (run_dir / SUMMARY_DIR_NAME).is_dir()
    )
    artifact_dir = _artifact_directory(run_dir)
    results_path = artifact_dir / "results.jsonl"
    if results_path.exists() and not args.resume:
        raise FileExistsError(
            f"Run already has results and --no-resume was requested: {results_path}"
        )
    if results_path.exists():
        print(f"Resuming existing run: {run_dir}", flush=True)
    artifact_dir.mkdir(parents=True, exist_ok=True)

    if args.reme_config:
        config_path = Path(args.reme_config).resolve()
        if not config_path.is_file():
            raise FileNotFoundError(f"ReMe config not found: {config_path}")
    else:
        config_path = artifact_dir / "reme_bm25.yaml"

    retrieval_config = {
        "run_id": run_id,
        "dataset_id": str(spec["dataset_id"]),
        "source_root": str(source),
        "selected_case_ids": [row.case["envelope"]["case_id"] for row in artifacts],
        "top_k": args.top_k,
        "search_multiplier": args.search_multiplier,
        "min_score": args.min_score,
        "context_batch": args.context_batch,
        "vector_weight": args.vector_weight,
        "reme_config": str(Path(args.reme_config).resolve()) if args.reme_config else None,
    }
    retrieval_config_path = artifact_dir / "retrieval_run_config.json"
    if retrieval_config_path.is_file():
        existing_config = json.loads(retrieval_config_path.read_text(encoding="utf-8"))
        if existing_config != retrieval_config:
            raise ValueError(
                "Resume configuration differs from retrieval_run_config.json; "
                "use the original settings or a new --run-id"
            )
    else:
        retrieval_config_path.write_text(
            json.dumps(retrieval_config, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    if not args.reme_config:
        config_path = create_bm25_config(config_path, args.vector_weight)
    backend = ReMeCliMemoryAdapter(
        command=resolve_reme_command(args.reme_cmd),
        config_path=config_path,
        startup_timeout=args.reme_startup_timeout,
        vector_weight=args.vector_weight,
    )
    system = ReMeSystemAdapter(backend)
    run_config = MemEvalRunConfig(
        run_id=run_id,
        dataset_id=str(spec["dataset_id"]),
        top_k=args.top_k,
        search_multiplier=args.search_multiplier,
        min_score=args.min_score,
        port=args.reme_port,
        reuse_context=args.context_batch,
    )
    print("\n=== Retrieval ===", flush=True)
    results = MemEvalRunner(system, artifact_dir / "system_work").run(
        artifacts, run_config, results_path, resume=args.resume
    )
    summary_path = artifact_dir / "run_summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    summary.update(
        created_at=datetime.now(timezone.utc).isoformat(),
        selected_dimensions=sorted({row.dimension_id for row in artifacts}),
        selected_case_ids=[row.case["envelope"]["case_id"] for row in artifacts],
        source_root=str(source),
    )
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    trace_adapter = MemEvalTraceAdapter(
        source,
        artifacts,
        artifact_dir,
        top_k=args.top_k,
        answer_api_key_env=args.answer_api_key_env,
        answer_base_url_env=args.answer_base_url_env,
        answer_model_env=args.answer_model_env,
        judge_api_key_env=args.judge_api_key_env,
        judge_base_url_env=args.judge_base_url_env,
        judge_model_env=args.judge_model_env,
    )
    llm_case_count = trace_adapter.write_inputs(results)
    stage_codes = {
        "retrieval": 0, "answer": None, "judge": None,
        "trace": None, "dashboard": None,
    }
    if llm_case_count:
        llm_input = artifact_dir / "llm_input.jsonl"
        answers_path = artifact_dir / "answers.jsonl"
        scores_path = artifact_dir / "scores.jsonl"
        stage_codes["answer"] = _run_llm_stage(
            "Answer",
            "run_answer_eval.py",
            [
                "--input", str(llm_input),
                "--output", str(answers_path),
                "--api-key-env", args.answer_api_key_env,
                "--base-url-env", args.answer_base_url_env,
                "--model-env", args.answer_model_env,
                "--workers", str(args.answer_workers),
                "--max-tokens", str(args.answer_max_tokens),
            ],
        )
        if stage_codes["answer"] == 0:
            stage_codes["judge"] = _run_llm_stage(
                "Judge",
                "run_judge_eval.py",
                [
                    "--input", str(llm_input),
                    "--answers", str(answers_path),
                    "--output", str(scores_path),
                    "--api-key-env", args.judge_api_key_env,
                    "--base-url-env", args.judge_base_url_env,
                    "--model-env", args.judge_model_env,
                    "--workers", str(args.judge_workers),
                    "--max-tokens", str(args.judge_max_tokens),
                ],
            )

    results = trace_adapter.apply_llm_outputs(results_path)

    print("\n=== Trace ===", flush=True)
    trace_adapter.build_trace(results_path)
    stage_codes["trace"] = 0
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    summary["stage_exit_codes"] = stage_codes
    summary["llm_case_count"] = llm_case_count
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print("\n=== Dashboard ===", flush=True)
    layout = (
        refresh_result_layout(run_dir)
        if organized_run
        else organize_result_layout(run_dir)
    )
    stage_codes["dashboard"] = 0
    detailed_dir = Path(layout["detailed_trace_report_dir"])
    summary_dir = Path(layout["trace_summary_dir"])
    results_path = detailed_dir / "results.jsonl"
    summary_path = detailed_dir / "run_summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    summary["stage_exit_codes"] = stage_codes
    summary["llm_case_count"] = llm_case_count
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"Run mode: {summary['run_mode']}")
    print(f"Cases: {len(results)}; Answer/Judge cases: {llm_case_count}; Context ingests: {summary['ingest_count']}")
    print(f"Status: {summary['status_counts']}")
    print(f"Results: {results_path}")
    print(f"Summary: {summary_path}")
    print(f"Trace: {detailed_dir / 'trace' / 'trace_summary.json'}")
    print(f"Dashboard: {summary_dir / 'Dashboard.html'}")
    failed_stage = any(code not in {None, 0} for code in stage_codes.values())
    return 2 if failed_stage or any(row["status"] == "error" for row in results) else 0


def main() -> int:
    return run(parser().parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
