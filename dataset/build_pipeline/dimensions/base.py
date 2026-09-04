"""Dimension Builder contract for stage-21 benchmark logic."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Iterable

from ..sources.base import CanonicalSourceRecord


DimensionCandidate = dict[str, Any]
DimensionCase = dict[str, Any]


@dataclass(frozen=True)
class DimensionBuildResult:
    dimension_id: str
    cases: list[DimensionCase]
    loaded_candidate_count: int
    filtered_candidate_count: int


class DimensionBuilder(ABC):
    """Template method for benchmark logic, deliberately separate from Source Adapters."""

    dimension_id: str

    def load_candidates(
        self,
        records: Iterable[CanonicalSourceRecord],
    ) -> list[DimensionCandidate]:
        return [dict(record) for record in records]

    def filter_candidates(
        self,
        candidates: list[DimensionCandidate],
    ) -> list[DimensionCandidate]:
        return candidates

    @abstractmethod
    def derive_gold(self, candidate: DimensionCandidate) -> DimensionCandidate:
        """Derive dimension-specific Gold fields without mutating the input."""

    def sample_cases(self, candidates: list[DimensionCandidate]) -> list[DimensionCase]:
        return [dict(candidate) for candidate in candidates]

    def validate_cases(self, cases: list[DimensionCase]) -> list[DimensionCase]:
        seen_case_ids: set[str] = set()
        for case in cases:
            case_id = str(case.get("case_id", "")).strip()
            if not case_id:
                raise ValueError(f"{self.dimension_id} produced a case without case_id")
            if case_id in seen_case_ids:
                raise ValueError(f"{self.dimension_id} produced duplicate case_id {case_id!r}")
            seen_case_ids.add(case_id)
            if str(case.get("dimension_id", "")) != self.dimension_id:
                raise ValueError(f"Case {case_id!r} has the wrong dimension_id")
            if not str(case.get("source_record_id", "")).strip():
                raise ValueError(f"Case {case_id!r} has no source_record_id")
            if not str(case.get("query", "")).strip():
                raise ValueError(f"Case {case_id!r} has an empty query")
            if not isinstance(case.get("gold_payload"), dict):
                raise ValueError(f"Case {case_id!r} gold_payload must be an object")
        return cases

    def build(self, records: Iterable[CanonicalSourceRecord]) -> DimensionBuildResult:
        loaded = self.load_candidates(records)
        filtered = self.filter_candidates(loaded)
        derived = [self.derive_gold(candidate) for candidate in filtered]
        cases = self.validate_cases(self.sample_cases(derived))
        return DimensionBuildResult(
            dimension_id=self.dimension_id,
            cases=cases,
            loaded_candidate_count=len(loaded),
            filtered_candidate_count=len(filtered),
        )
