"""Organize an eval Run into detailed provenance and concise review folders."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from memory_eval.result_layout import organize_result_layout


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Apply the fixed two-folder Eval result layout")
    parser.add_argument("--run-dir", type=Path, required=True)
    return parser.parse_args()


def run(args: argparse.Namespace) -> int:
    manifest = organize_result_layout(args.run_dir)
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(run(parse_args()))
