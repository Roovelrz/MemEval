"""D02 long-term retrieval builder."""

from __future__ import annotations

from .base import DimensionCandidate, DimensionCase
from .common import SourceDimensionBuilder, ensure_event_ids_exist, evidence_events, first_answer, stable_id
from .registry import register_dimension_builder


@register_dimension_builder
class D02RetrievalBuilder(SourceDimensionBuilder):
    dimension_id = "D02"
    dimension_name = "long_term_memory_retrieval"
    payload_type = "retrieval"
    source_datasets = frozenset({"longmemeval"})
    default_target_count = 37

    def derive_gold(self, candidate: DimensionCandidate) -> DimensionCandidate:
        record_id = str(candidate["source_record_id"])
        selected = evidence_events(candidate)
        if not selected:
            raise ValueError(f"D02 source record {record_id!r} has no retrieval evidence")
        return self.make_case(
            candidate,
            case_id=f"d02:{stable_id(record_id)}",
            query=str(candidate["source_gold"].get("question", "")),
            gold_payload={
                "gold_evidence_ids": [event["event_id"] for event in selected],
                "gold_answer": first_answer(candidate["source_gold"].get("answer")),
                "retrieval_k": [1, 3, 5, 10],
            },
        )

    def validate_cases(self, cases: list[DimensionCase]) -> list[DimensionCase]:
        validated = super().validate_cases(cases)
        for case in validated:
            evidence_ids = case["gold_payload"].get("gold_evidence_ids", [])
            if not evidence_ids:
                raise ValueError(f"Case {case['case_id']!r} must contain retrieval evidence")
            ensure_event_ids_exist(case, evidence_ids, "gold_evidence_ids")
        return validated
