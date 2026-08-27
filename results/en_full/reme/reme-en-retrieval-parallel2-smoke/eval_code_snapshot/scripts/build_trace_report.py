"""Build human-readable trace reports from an existing eval run directory."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from memory_eval.trace_report import build_trace_report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build trace_summary and per-case trace reports")
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument(
        "--data",
        "--dataset",
        dest="dataset",
        type=Path,
        default=None,
        help="Override the dataset path recorded in run_config.json",
    )
    parser.add_argument(
        "--baseline-run",
        type=Path,
        default=None,
        help="Optional prior run directory used to calculate version deltas",
    )
    return parser.parse_args()


def run(args: argparse.Namespace) -> int:
    summary = build_trace_report(args.run_dir, args.dataset, args.baseline_run)
    result = {
        "trace_summary": str((args.run_dir.resolve() / "trace" / "trace_summary.md")),
        "total_cases": summary["total_cases"],
        "root_cause_distribution": summary["root_cause_distribution"],
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(run(parse_args()))
