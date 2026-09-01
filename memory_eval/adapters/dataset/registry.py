"""Dataset adapter registry and automatic format detection."""

from __future__ import annotations

import csv
from pathlib import Path

from .base import DatasetAdapter, DatasetLoadResult
from .common import load_json_or_jsonl
from .locomo import LoCoMoDatasetAdapter
from .longmemeval import LongMemEvalDatasetAdapter
from .personamem_v2 import PersonaMemV2DatasetAdapter


DATASET_ADAPTERS: dict[str, type[DatasetAdapter]] = {
    "longmemeval": LongMemEvalDatasetAdapter,
    "locomo": LoCoMoDatasetAdapter,
    "personamem-v2": PersonaMemV2DatasetAdapter,
}


def infer_dataset_adapter(path: Path) -> str:
    if path.suffix.lower() == ".csv":
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            headers = set(next(csv.reader(handle), []))
        if {"persona_id", "user_query", "correct_answer"} <= headers:
            return "personamem-v2"
    elif path.suffix.lower() in {".json", ".jsonl"}:
        rows = load_json_or_jsonl(path)
        if rows:
            keys = set(rows[0])
            if {"qa", "conversation"} <= keys:
                return "locomo"
            if keys & {"sessions", "haystack_sessions"} and keys & {"question", "query"}:
                return "longmemeval"
    raise ValueError(f"Cannot infer dataset adapter for {path}; choose --dataset-adapter explicitly")


def create_dataset_adapter(name: str, path: Path) -> DatasetAdapter:
    selected = infer_dataset_adapter(path) if name.strip().lower() == "auto" else name.strip().lower()
    factory = DATASET_ADAPTERS.get(selected)
    if factory is None:
        available = ", ".join(sorted(DATASET_ADAPTERS))
        raise ValueError(f"Unknown dataset adapter {name!r}; available: auto, {available}")
    return factory()


def load_dataset_cases(
    path: Path,
    *,
    adapter_name: str = "auto",
    start: int = 0,
    limit: int = 0,
    shuffle: bool = False,
    seed: int = 42,
) -> DatasetLoadResult:
    adapter = create_dataset_adapter(adapter_name, path)
    return adapter.load(path, start=start, limit=limit, shuffle=shuffle, seed=seed)

