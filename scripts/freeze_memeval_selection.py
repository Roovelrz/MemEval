"""Write or verify Stage-31 source selections in all MemEval manifests."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from dataset.build_pipeline.release import DIMENSION_DIRECTORIES, ReviewedBenchmark
from dataset.build_pipeline.selection import build_selected_sources_snapshot


def parser() -> argparse.ArgumentParser:
    command = argparse.ArgumentParser(description="Freeze or verify MemEval source selections")
    command.add_argument("--root", default="dataset/MemEval-v0.1")
    command.add_argument("--check", action="store_true", help="verify without modifying manifests")
    return command


def run(root: str | Path, *, check: bool) -> int:
    benchmark = ReviewedBenchmark(root)
    changed = []
    for dimension_id in DIMENSION_DIRECTORIES:
        version_dir = benchmark.dimension_dir(dimension_id)
        manifest_path = version_dir / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        expected = build_selected_sources_snapshot(version_dir)
        if manifest.get("selected_sources") == expected:
            continue
        changed.append(dimension_id)
        if not check:
            manifest["selected_sources"] = expected
            manifest_path.write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
    if check and changed:
        print("Selection manifests are stale: " + ", ".join(changed))
        return 1
    print(("Updated" if changed else "Verified") + ": " + (", ".join(changed) or "D01-D08"))
    return 0


def main() -> int:
    args = parser().parse_args()
    return run(args.root, check=args.check)


if __name__ == "__main__":
    raise SystemExit(main())
