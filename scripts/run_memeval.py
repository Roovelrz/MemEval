"""Run the frozen eight-dimension MemEval benchmark through a System Adapter."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from dataset.build_pipeline import ReviewedBenchmark
from dataset.build_pipeline.release import DIMENSION_DIRECTORIES
from memory_eval.adapters.memory.reme import (
    ReMeCliMemoryAdapter,
    create_bm25_config,
    resolve_reme_command,
)
from memory_eval.dataset_registry import default_output_root, resolve_dataset
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
    return command


def run(args: argparse.Namespace) -> int:
    source, spec = resolve_dataset(args.dataset, args.data)
    if spec.get("adapter") not in {None, "memeval"} or not source.is_dir():
        raise ValueError("run_memeval requires a formal MemEval release directory")
    benchmark = ReviewedBenchmark(source)
    benchmark.assert_review_complete()
    artifacts = select_artifacts(benchmark, args.dimension, args.case_id, args.limit)

    run_id = args.run_id or datetime.now().strftime("%Y%m%d-%H%M%S")
    output_root = Path(args.output_dir).resolve() if args.output_dir else default_output_root(spec, "reme")
    run_dir = output_root / run_id
    results_path = run_dir / "results.jsonl"
    if results_path.exists():
        raise FileExistsError(f"Run already has results: {results_path}")
    run_dir.mkdir(parents=True, exist_ok=True)

    if args.reme_config:
        config_path = Path(args.reme_config).resolve()
        if not config_path.is_file():
            raise FileNotFoundError(f"ReMe config not found: {config_path}")
    else:
        config_path = create_bm25_config(run_dir / "reme_bm25.yaml", args.vector_weight)
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
    results = MemEvalRunner(system, run_dir / "system_work").run(
        artifacts, run_config, results_path
    )
    summary_path = run_dir / "run_summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    summary.update(
        created_at=datetime.now(timezone.utc).isoformat(),
        selected_dimensions=sorted({row.dimension_id for row in artifacts}),
        selected_case_ids=[row.case["envelope"]["case_id"] for row in artifacts],
        source_root=str(source),
    )
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"Run mode: {summary['run_mode']}")
    print(f"Cases: {len(results)}; Context ingests: {summary['ingest_count']}")
    print(f"Status: {summary['status_counts']}")
    print(f"Results: {results_path}")
    print(f"Summary: {summary_path}")
    return 2 if any(row["status"] == "error" for row in results) else 0


def main() -> int:
    return run(parser().parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
