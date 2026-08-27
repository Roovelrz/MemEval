"""Resolve registered benchmark IDs to immutable local dataset files."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = REPO_ROOT / "datasets" / "registry.json"
DEFAULT_DATASET_ID = "LongMemEval-ZH-20-v0.1"


def load_dataset_registry() -> dict[str, dict[str, Any]]:
    payload = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    rows = payload.get("datasets") if isinstance(payload, dict) else None
    if not isinstance(rows, list):
        raise ValueError(f"Dataset registry has no datasets list: {REGISTRY_PATH}")
    registry: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict) or not row.get("dataset_id"):
            raise ValueError(f"Invalid dataset registry row: {row!r}")
        dataset_id = str(row["dataset_id"])
        if dataset_id in registry:
            raise ValueError(f"Duplicate dataset_id in registry: {dataset_id}")
        registry[dataset_id] = dict(row)
    return registry


def _registered_path(spec: dict[str, Any]) -> Path | None:
    value = spec.get("path")
    if not value:
        return None
    path = Path(str(value))
    return path.resolve() if path.is_absolute() else (REPO_ROOT / path).resolve()


def _custom_spec(path: Path) -> dict[str, Any]:
    return {
        "dataset_id": path.stem,
        "dataset_name": path.stem,
        "source_dataset": path.stem,
        "language": "unknown",
        "version": path.parent.name,
        "path": str(path),
        "case_count": None,
        "translated": False,
        "result_group": "custom",
        "status": "custom",
    }


def resolve_dataset(
    dataset: str = DEFAULT_DATASET_ID,
    data_path: str | Path | None = None,
) -> tuple[Path, dict[str, Any]]:
    """Resolve a registry ID, while retaining ``--data`` path compatibility."""

    registry = load_dataset_registry()
    if data_path is not None:
        path = Path(data_path).resolve()
        for spec in registry.values():
            if _registered_path(spec) == path:
                return _validate_resolved(path, spec)
        return _validate_resolved(path, _custom_spec(path))

    if dataset in registry:
        spec = registry[dataset]
        path = _registered_path(spec)
        if spec.get("status") != "available" or path is None:
            raise ValueError(
                f"Dataset {dataset!r} is reserved but not implemented; add its adapter and path first"
            )
        return _validate_resolved(path, spec)

    path = Path(dataset).resolve()
    return _validate_resolved(path, _custom_spec(path))


def _validate_resolved(path: Path, spec: dict[str, Any]) -> tuple[Path, dict[str, Any]]:
    if not path.is_file():
        raise FileNotFoundError(f"Dataset file not found: {path}")
    resolved = dict(spec)
    resolved["path"] = str(path)
    return path, resolved


def default_output_root(spec: dict[str, Any], memory_adapter: str) -> Path:
    group = str(spec.get("result_group") or "custom")
    backend = memory_adapter.strip().lower() or "unknown"
    return REPO_ROOT / "results" / group / backend


def run_dataset_metadata(
    spec: dict[str, Any],
    *,
    selected_case_count: int,
    source_case_count: int,
) -> dict[str, Any]:
    expected = spec.get("case_count")
    if isinstance(expected, int) and expected != source_case_count:
        raise ValueError(
            f"Registered dataset {spec['dataset_id']} expected {expected} cases, found {source_case_count}"
        )
    return {
        "dataset_id": spec["dataset_id"],
        "dataset_name": spec["dataset_name"],
        "dataset_version": spec.get("version"),
        "source_dataset": spec["source_dataset"],
        "language": spec["language"],
        "translated": bool(spec["translated"]),
        "case_count": selected_case_count,
        "dataset_case_count": source_case_count,
    }
