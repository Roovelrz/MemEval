"""Build the read-only static HTML dashboard from existing Trace artifacts."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from memory_eval.html_report import build_html_report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the static Memory Eval HTML dashboard")
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Default: <run-dir>/report",
    )
    return parser.parse_args()


def run(args: argparse.Namespace) -> int:
    manifest = build_html_report(args.run_dir, args.output_dir)
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(run(parse_args()))
