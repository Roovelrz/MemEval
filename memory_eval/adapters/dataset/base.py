"""Common contract for benchmark dataset adapters."""

from __future__ import annotations

import random
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol


CanonicalCase = dict[str, Any]


@dataclass(frozen=True)
class DatasetLoadResult:
    """Selected canonical cases plus the source benchmark cardinality."""

    cases: list[CanonicalCase]
    source_case_count: int
    adapter_name: str


class DatasetAdapter(Protocol):
    """Convert one benchmark format into canonical eval cases."""

    name: str

    def load(
        self,
        path: Path,
        *,
        start: int = 0,
        limit: int = 0,
        shuffle: bool = False,
        seed: int = 42,
    ) -> DatasetLoadResult:
        ...


def selected_indices(
    count: int,
    *,
    start: int,
    limit: int,
    shuffle: bool,
    seed: int,
) -> list[int]:
    if start < 0 or limit < 0:
        raise ValueError("start and limit must be non-negative")
    indices = list(range(count))
    if shuffle:
        random.Random(seed).shuffle(indices)
    selected = indices[start:]
    return selected[:limit] if limit else selected


def validate_canonical_case(case: CanonicalCase) -> CanonicalCase:
    required = ("case_id", "question", "gold_answer", "sessions", "evidence_session_ids")
    missing = [name for name in required if name not in case]
    if missing:
        raise ValueError(f"Canonical case is missing fields: {', '.join(missing)}")
    if not str(case["case_id"]).strip():
        raise ValueError("Canonical case_id must not be empty")
    if not str(case["question"]).strip():
        raise ValueError(f"Case {case['case_id']} has an empty question")
    if not str(case["gold_answer"]).strip():
        raise ValueError(f"Case {case['case_id']} has an empty gold answer")
    if not isinstance(case["sessions"], list):
        raise ValueError(f"Case {case['case_id']} sessions must be a list")
    if not isinstance(case["evidence_session_ids"], list):
        raise ValueError(f"Case {case['case_id']} evidence_session_ids must be a list")
    session_ids = {str(session.get("session_id", "")) for session in case["sessions"]}
    missing_evidence = sorted(set(map(str, case["evidence_session_ids"])) - session_ids)
    if missing_evidence:
        raise ValueError(f"Case {case['case_id']} references missing evidence sessions: {missing_evidence}")
    return case

