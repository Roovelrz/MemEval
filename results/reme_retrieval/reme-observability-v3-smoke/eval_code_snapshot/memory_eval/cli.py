"""CLI for the first LongMemEval-S end-to-end evaluation path."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from memory_eval.datasets.longmemeval import load_longmemeval
from memory_eval.memory.in_memory import InMemorySessionAdapter
from memory_eval.metrics.report import build_summary
from memory_eval.metrics.retrieval_report import build_retrieval_summary
from memory_eval.runners.longmemeval import LongMemEvalRunner


AML_ENV_NAMES = (
    "ANSWER_API_BASE",
    "ANSWER_API_KEY",
    "ANSWER_MODEL",
    "JUDGE_API_BASE",
    "JUDGE_API_KEY",
    "JUDGE_MODEL",
)


def _dataset_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _require_aml_environment() -> None:
    missing = [name for name in AML_ENV_NAMES if not os.environ.get(name)]
    if missing:
        raise SystemExit(
            "Prepared artifacts were created, but AML Answer/Judge cannot run. "
            f"Missing environment variables: {', '.join(missing)}"
        )


def _run_aml(pipeline: Path, prepared: Path, run_dir: Path) -> tuple[Path, Path]:
    answers = run_dir / "answers.jsonl"
    scores = run_dir / "scores.jsonl"
    subprocess.run(
        [sys.executable, str(pipeline), "answer", "--input", str(prepared), "--output", str(answers)],
        check=True,
        cwd=pipeline.parents[2],
    )
    subprocess.run(
        [
            sys.executable,
            str(pipeline),
            "evaluate",
            "--input",
            str(prepared),
            "--answers",
            str(answers),
            "--output",
            str(scores),
        ],
        check=True,
        cwd=pipeline.parents[2],
    )
    return answers, scores


def run_longmemeval(args: argparse.Namespace) -> int:
    source = Path(args.data).resolve()
    cases = load_longmemeval(source, limit=args.limit)
    run_id = args.run_id or datetime.now().strftime("%Y%m%d-%H%M%S")
    output_root = Path(args.output_dir).resolve()
    run_dir = output_root / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    if args.memory_adapter == "reme":
        from memory_eval.memory.reme import ReMeAdapter

        reme_work_dir = Path(args.reme_work_dir or output_root / "_reme_workspace").resolve()
        adapter = ReMeAdapter(reme_work_dir)
    else:
        reme_work_dir = None
        adapter = InMemorySessionAdapter()
    runner = LongMemEvalRunner(adapter)
    prepared, retrieval = runner.prepare(
        cases=cases,
        run_id=run_id,
        output_dir=output_root,
        mode=args.mode,
        top_k=args.top_k,
    )

    config = {
        "dataset_path": str(source),
        "dataset_version": "LongMemEval-S v1 cleaned",
        "dataset_sha256": _dataset_sha256(source),
        "mode": args.mode,
        "memory_adapter": args.memory_adapter,
        "top_k": args.top_k,
        "limit": args.limit,
        "answer_model": os.environ.get("ANSWER_MODEL", ""),
        "judge_model": os.environ.get("JUDGE_MODEL", ""),
        "run_timestamp": datetime.now(timezone.utc).isoformat(),
    }
    if args.memory_adapter == "reme":
        import reme

        config.update(
            {
                "retrieval_backend": "bm25",
                "embedding_enabled": False,
                "llm_enabled": False,
                "reme_version": reme.__version__,
                "reme_workspace": str(reme_work_dir),
            }
        )
    (run_dir / "run_config.json").write_text(
        json.dumps(config, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(f"Prepared {len(cases)} cases: {prepared}")
    print(f"Retrieval trace: {retrieval}")
    retrieval_summary = run_dir / "summary.json"
    build_retrieval_summary(
        retrieval_path=retrieval,
        output_path=retrieval_summary,
        memory_adapter=args.memory_adapter,
        top_k=args.top_k,
    )
    print(f"Retrieval summary: {retrieval_summary}")
    if args.prepare_only:
        print("AML Answer/Judge skipped because --prepare-only was set.")
        return 0

    _require_aml_environment()
    aml_root = Path(args.aml_root).resolve()
    pipeline = aml_root / "data" / "longmemeval-s" / "pipeline.py"
    if not pipeline.is_file():
        raise SystemExit(f"AML LongMemEval pipeline not found: {pipeline}")
    _, scores = _run_aml(pipeline, prepared, run_dir)
    summary_path = run_dir / "summary.json"
    build_summary(prepared, retrieval, scores, summary_path, args.mode, args.top_k)
    print(f"Summary: {summary_path}")
    return 0


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description="Agent Memory eval harness")
    commands = root.add_subparsers(dest="command", required=True)
    command = commands.add_parser("longmemeval", help="run LongMemEval-S cleaned")
    command.add_argument("--data", required=True)
    command.add_argument("--mode", choices=("oracle", "memory"), required=True)
    command.add_argument("--limit", type=int)
    command.add_argument("--top-k", type=int, default=10)
    command.add_argument("--output-dir", default="results")
    command.add_argument("--run-id")
    command.add_argument(
        "--aml-root",
        default=str(Path(__file__).resolve().parents[2] / "AML" / "agent-memory-leaderboard"),
        help="path to the read-only upstream AML repository",
    )
    command.add_argument("--memory-adapter", choices=("in-memory", "reme"), default="in-memory")
    command.add_argument(
        "--reme-work-dir",
        help="adapter-owned sequential ReMe workspace root (defaults under output-dir)",
    )
    command.add_argument(
        "--prepare-only",
        action="store_true",
        help="write prepared/retrieval artifacts without calling AML models",
    )
    command.set_defaults(run=run_longmemeval)
    return root


def main() -> int:
    args = parser().parse_args()
    return args.run(args)


if __name__ == "__main__":
    raise SystemExit(main())
