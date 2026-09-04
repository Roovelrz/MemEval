"""Shared helpers for the eight dimension-specific builders."""

from __future__ import annotations

import hashlib
import re
from typing import Any

from .base import DimensionBuilder, DimensionCandidate, DimensionCase


def stable_id(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9_.:-]+", "_", value).strip("_")
    return cleaned or hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]


def first_answer(value: Any) -> Any:
    while isinstance(value, list) and value:
        value = value[0]
    return value


def evidence_events(candidate: DimensionCandidate) -> list[dict[str, Any]]:
    evidence_sessions = {
        str(value) for value in candidate.get("source_gold", {}).get("evidence_session_ids", [])
    }
    selected = [
        event
        for event in candidate.get("events", [])
        if event.get("metadata", {}).get("has_answer")
        or str(event.get("session_id", "")) in evidence_sessions
    ]
    return selected


def ensure_event_ids_exist(case: DimensionCase, event_ids: list[str], field_name: str) -> None:
    available = {str(event.get("event_id", "")) for event in case.get("events", [])}
    missing = sorted(set(map(str, event_ids)) - available)
    if missing:
        raise ValueError(f"Case {case['case_id']!r} {field_name} references missing events: {missing}")


class SourceDimensionBuilder(DimensionBuilder):
    """Base for builders that consume one or more named Source Adapters."""

    dimension_name: str
    payload_type: str
    source_datasets: frozenset[str]
    default_target_count = 0

    def __init__(self, *, target_count: int | None = None, seed: str | None = None) -> None:
        target_count = self.default_target_count if target_count is None else target_count
        if target_count < 0:
            raise ValueError("target_count must be non-negative")
        self.target_count = target_count
        self.seed = seed or f"{self.dimension_id.lower()}-builder-v0.1"

    def filter_candidates(
        self,
        candidates: list[DimensionCandidate],
    ) -> list[DimensionCandidate]:
        return [
            candidate
            for candidate in candidates
            if str(candidate.get("source_dataset", "")) in self.source_datasets
        ]

    def sample_cases(self, candidates: list[DimensionCandidate]) -> list[DimensionCase]:
        ordered = sorted(
            candidates,
            key=lambda candidate: hashlib.sha256(
                f"{self.seed}:{candidate.get('case_id', candidate.get('source_record_id', ''))}".encode(
                    "utf-8"
                )
            ).hexdigest(),
        )
        return ordered[: self.target_count] if self.target_count else ordered

    def make_case(
        self,
        candidate: DimensionCandidate,
        *,
        case_id: str,
        query: str,
        gold_payload: dict[str, Any],
        metadata: dict[str, Any] | None = None,
        events: list[dict[str, Any]] | None = None,
    ) -> DimensionCase:
        return {
            "case_id": case_id,
            "dimension_id": self.dimension_id,
            "dimension_name": self.dimension_name,
            "source_dataset": candidate["source_dataset"],
            "source_record_id": candidate["source_record_id"],
            "query": query,
            "events": list(candidate.get("events", []) if events is None else events),
            "payload_type": self.payload_type,
            "gold_payload": gold_payload,
            "metadata": {
                "builder_seed": self.seed,
                **dict(candidate.get("source_metadata", {})),
                **(metadata or {}),
            },
        }

    def validate_cases(self, cases: list[DimensionCase]) -> list[DimensionCase]:
        validated = super().validate_cases(cases)
        for case in validated:
            if case.get("payload_type") != self.payload_type:
                raise ValueError(f"Case {case['case_id']!r} has the wrong payload_type")
            if not isinstance(case.get("events"), list) or not case["events"]:
                raise ValueError(f"Case {case['case_id']!r} must contain source events")
            if not isinstance(case.get("metadata"), dict):
                raise ValueError(f"Case {case['case_id']!r} metadata must be an object")
        return validated
