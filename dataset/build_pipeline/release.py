"""Reviewed benchmark access and stage-22 export helpers."""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator


DIMENSION_DIRECTORIES = {
    "D01": "d01_memory_write",
    "D02": "d02_long_term_memory",
    "D03": "d03_long_time_span_dialogue",
    "D04": "d04_proactive_memory_activation",
    "D05": "d05_user_profile_preference",
    "D06": "d06_dynamic_update_conflict",
    "D07": "d07_ultra_long_context",
    "D08": "d08_privacy_user_isolation",
}

EXPORT_DIRECTORIES = {
    "D01": "d01_write",
    "D02": "d02_retrieval",
    "D03": "d03_temporal",
    "D04": "d04_activation",
    "D05": "d05_profile",
    "D06": "d06_conflict",
    "D07": "d07_scale",
    "D08": "d08_privacy",
}

REVIEWED_DIMENSIONS = {"D01", "D04", "D05", "D06", "D07"}

_APPROVED_CASE_STATUSES = {
    "D01": {"approved"},
    "D04": {"approved"},
    "D05": {"approved_after_repair"},
    "D06": {"approved", "approved_after_replacement"},
    "D07": {"approved"},
}

_APPROVED_MANIFEST_STATUSES = {
    "D01": {"complete"},
    "D04": {"complete"},
    "D05": {"complete_after_repair"},
    "D06": {"complete_after_replacement"},
    "D07": {"complete_after_repair"},
}


@dataclass(frozen=True)
class ReviewedCaseArtifact:
    """One formal Case and the Context file it references."""

    dimension_id: str
    case_path: Path
    context_path: Path
    case: dict[str, Any]


class ReviewedBenchmark:
    """Read the frozen benchmark while preserving its human-review evidence."""

    def __init__(self, root: str | Path, *, version: str = "v0.1") -> None:
        self.root = Path(root).resolve()
        self.version = version

    def dimension_dir(self, dimension_id: str) -> Path:
        try:
            directory = DIMENSION_DIRECTORIES[dimension_id.upper()]
        except KeyError as exc:
            raise KeyError(f"Unknown dimension {dimension_id!r}") from exc
        return self.root / "dimensions" / directory / self.version

    def load_manifest(self, dimension_id: str) -> dict[str, Any]:
        path = self.dimension_dir(dimension_id) / "manifest.json"
        if not path.is_file():
            raise FileNotFoundError(f"Missing dimension manifest: {path}")
        return json.loads(path.read_text(encoding="utf-8"))

    def iter_cases(self, dimension_id: str | None = None) -> Iterator[ReviewedCaseArtifact]:
        dimensions = [dimension_id.upper()] if dimension_id else list(DIMENSION_DIRECTORIES)
        for current_dimension in dimensions:
            version_dir = self.dimension_dir(current_dimension)
            cases_dir = version_dir / "cases"
            if not cases_dir.is_dir():
                raise FileNotFoundError(f"Missing cases directory: {cases_dir}")
            for case_path in sorted(cases_dir.glob("*.json")):
                case = json.loads(case_path.read_text(encoding="utf-8"))
                context_ref = str(case.get("envelope", {}).get("context", {}).get("context_ref", ""))
                if not context_ref:
                    context_path = version_dir / "__missing_context_ref__"
                else:
                    context_path = (version_dir / context_ref).resolve()
                    try:
                        context_path.relative_to(version_dir.resolve())
                    except ValueError as exc:
                        raise ValueError(
                            f"Case {case_path.name} references a Context outside its dimension directory"
                        ) from exc
                yield ReviewedCaseArtifact(
                    dimension_id=current_dimension,
                    case_path=case_path,
                    context_path=context_path,
                    case=case,
                )

    @staticmethod
    def case_review_status(dimension_id: str, case: dict[str, Any]) -> str | None:
        if dimension_id == "D01":
            value = case.get("annotation", {}).get("human_review_status")
        else:
            value = (
                case.get("envelope", {})
                .get("metadata", {})
                .get("human_review", {})
                .get("status")
            )
        return str(value).strip() if value is not None else None

    def assert_review_complete(self) -> dict[str, dict[str, int]]:
        """Verify manifests and every review-required formal Case."""

        summary: dict[str, dict[str, int]] = {}
        for dimension_id in DIMENSION_DIRECTORIES:
            artifacts = list(self.iter_cases(dimension_id))
            manifest = self.load_manifest(dimension_id)
            manifest_count = int(manifest.get("counts", {}).get("cases", -1))
            if manifest_count != len(artifacts):
                raise ValueError(
                    f"{dimension_id} manifest declares {manifest_count} cases, found {len(artifacts)}"
                )

            if dimension_id not in REVIEWED_DIMENSIONS:
                summary[dimension_id] = {"cases": len(artifacts), "reviewed": 0}
                continue

            manifest_status = str(manifest.get("human_review", {}).get("status", ""))
            if manifest_status not in _APPROVED_MANIFEST_STATUSES[dimension_id]:
                raise ValueError(
                    f"{dimension_id} human-review manifest status is not final: {manifest_status!r}"
                )

            bad_cases = []
            status_counts: dict[str, int] = {}
            for artifact in artifacts:
                status = self.case_review_status(dimension_id, artifact.case)
                status_counts[status or "<missing>"] = status_counts.get(status or "<missing>", 0) + 1
                if status not in _APPROVED_CASE_STATUSES[dimension_id]:
                    bad_cases.append(f"{artifact.case_path.name}={status!r}")
            if bad_cases:
                preview = ", ".join(bad_cases[:5])
                raise ValueError(f"{dimension_id} contains non-final review states: {preview}")

            human_review = manifest.get("human_review", {})
            approved = int(
                human_review.get(
                    "approved_cases",
                    human_review.get("covered_cases", -1),
                )
            )
            if approved != len(artifacts):
                raise ValueError(
                    f"{dimension_id} manifest covers {approved} approved cases, found {len(artifacts)}"
                )
            summary[dimension_id] = {"cases": len(artifacts), "reviewed": len(artifacts), **status_counts}
        return summary


def export_benchmark_layout(
    source_root: str | Path,
    destination: str | Path,
    *,
    version: str = "v0.1",
) -> Path:
    """Export the reviewed release to the stage-22 ``cases.jsonl`` layout.

    The destination must be absent or empty. The source release is never modified.
    """

    benchmark = ReviewedBenchmark(source_root, version=version)
    review_summary = benchmark.assert_review_complete()
    destination_path = Path(destination).resolve()
    if destination_path.exists() and any(destination_path.iterdir()):
        raise FileExistsError(f"Refusing to mix a Benchmark export into non-empty {destination_path}")
    destination_path.mkdir(parents=True, exist_ok=True)
    version_root = destination_path / version.replace(".", "_")
    version_root.mkdir()

    counts: dict[str, int] = {}
    for dimension_id, export_name in EXPORT_DIRECTORIES.items():
        target_dimension = version_root / export_name
        target_contexts = target_dimension / "contexts"
        target_contexts.mkdir(parents=True)
        artifacts = list(benchmark.iter_cases(dimension_id))
        counts[dimension_id] = len(artifacts)
        with (target_dimension / "cases.jsonl").open("w", encoding="utf-8", newline="\n") as handle:
            copied_contexts: set[str] = set()
            for artifact in artifacts:
                handle.write(json.dumps(artifact.case, ensure_ascii=False, separators=(",", ":")) + "\n")
                context_name = artifact.context_path.name
                if context_name not in copied_contexts:
                    shutil.copy2(artifact.context_path, target_contexts / context_name)
                    copied_contexts.add(context_name)

    manifest_lines = [
        'schema_version: "0.1"',
        f'version: "{version}"',
        f"case_count: {sum(counts.values())}",
        "human_review: complete",
        "dimensions:",
    ]
    for dimension_id in DIMENSION_DIRECTORIES:
        manifest_lines.extend(
            [
                f"  {dimension_id}:",
                f"    path: {EXPORT_DIRECTORIES[dimension_id]}",
                f"    cases: {counts[dimension_id]}",
                f"    reviewed_cases: {review_summary[dimension_id]['reviewed']}",
            ]
        )
    (version_root / "manifest.yaml").write_text("\n".join(manifest_lines) + "\n", encoding="utf-8")
    return version_root
