"""D05 user profile and preference builder."""

from __future__ import annotations

from .base import DimensionCandidate, DimensionCase
from .common import SourceDimensionBuilder, ensure_event_ids_exist, evidence_events, stable_id
from .registry import register_dimension_builder


@register_dimension_builder
class D05ProfileBuilder(SourceDimensionBuilder):
    dimension_id = "D05"
    dimension_name = "user_profile_preference"
    payload_type = "profile"
    source_datasets = frozenset({"personamem-v2"})
    default_target_count = 37

    def derive_gold(self, candidate: DimensionCandidate) -> DimensionCandidate:
        record_id = str(candidate["source_record_id"])
        evidence = evidence_events(candidate)
        reviewed = candidate.get("source_metadata", {}).get("reviewed_profile_items")
        if isinstance(reviewed, list) and reviewed:
            profile_items = [dict(item) for item in reviewed if isinstance(item, dict)]
            status = "reviewed"
        else:
            preference = str(candidate["source_gold"].get("preference", "")).strip()
            if not preference:
                raise ValueError(f"D05 source record {record_id!r} has no preference")
            profile_items = [
                {
                    "profile_id": f"d05:{stable_id(record_id)}:profile:00",
                    "slot": "preference",
                    "value": preference,
                    "evidence_event_ids": [event["event_id"] for event in evidence],
                    "status": "active",
                }
            ]
            status = "semantic_review_required"
        return self.make_case(
            candidate,
            case_id=f"d05:{stable_id(record_id)}",
            query=str(candidate["source_gold"].get("question", "")),
            gold_payload={
                "profile_snapshot_time": None,
                "profile_items": profile_items,
                "expected_answer": candidate["source_gold"].get("answer"),
            },
            metadata={"annotation_status": status},
        )

    def validate_cases(self, cases: list[DimensionCase]) -> list[DimensionCase]:
        validated = super().validate_cases(cases)
        for case in validated:
            items = case["gold_payload"].get("profile_items")
            if not isinstance(items, list) or not items:
                raise ValueError(f"Case {case['case_id']!r} must contain profile_items")
            if any(not item.get("evidence_event_ids") for item in items):
                raise ValueError(f"Case {case['case_id']!r} contains an ungrounded profile item")
            ensure_event_ids_exist(
                case,
                [event_id for item in items for event_id in item.get("evidence_event_ids", [])],
                "profile_items",
            )
        return validated
