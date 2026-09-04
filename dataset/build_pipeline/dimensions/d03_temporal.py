"""D03 long-time-span dialogue builder."""

from __future__ import annotations

from datetime import datetime

from .base import DimensionCandidate, DimensionCase
from .common import SourceDimensionBuilder, ensure_event_ids_exist, evidence_events, first_answer, stable_id
from .registry import register_dimension_builder


def _parse_time(value: object) -> datetime | None:
    text = str(value or "").strip().replace("Z", "+00:00")
    if not text:
        return None
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None


@register_dimension_builder
class D03TemporalBuilder(SourceDimensionBuilder):
    dimension_id = "D03"
    dimension_name = "long_time_span_dialogue"
    payload_type = "temporal"
    source_datasets = frozenset({"locomo"})
    default_target_count = 38

    def derive_gold(self, candidate: DimensionCandidate) -> DimensionCandidate:
        record_id = str(candidate["source_record_id"])
        selected = evidence_events(candidate)
        if not selected:
            raise ValueError(f"D03 source record {record_id!r} has no temporal evidence")
        query_time_text = str(candidate.get("source_metadata", {}).get("question_date", ""))
        query_time = _parse_time(query_time_text)
        evidence_times = {
            event["event_id"]: event.get("timestamp", "") for event in selected if event.get("timestamp")
        }
        gaps = [
            (query_time - parsed).days
            for parsed in (_parse_time(value) for value in evidence_times.values())
            if query_time is not None and parsed is not None
        ]
        return self.make_case(
            candidate,
            case_id=f"d03:{stable_id(record_id)}",
            query=str(candidate["source_gold"].get("question", "")),
            gold_payload={
                "gold_answer": first_answer(candidate["source_gold"].get("answer")),
                "evidence_event_ids": [event["event_id"] for event in selected],
                "evidence_time": evidence_times,
                "query_time": query_time_text or None,
                "time_gap_days": max(gaps) if gaps else None,
                "lifecycle": {
                    "valid_from": min(evidence_times.values()) if evidence_times else None,
                    "valid_until": None,
                    "deleted_at": None,
                    "expected_active": True,
                },
            },
        )

    def validate_cases(self, cases: list[DimensionCase]) -> list[DimensionCase]:
        validated = super().validate_cases(cases)
        for case in validated:
            evidence_ids = case["gold_payload"].get("evidence_event_ids", [])
            if not evidence_ids:
                raise ValueError(f"Case {case['case_id']!r} must contain temporal evidence")
            ensure_event_ids_exist(case, evidence_ids, "evidence_event_ids")
        return validated
