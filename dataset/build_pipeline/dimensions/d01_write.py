"""D01 memory extraction and write builder."""

from __future__ import annotations

from typing import Any

from .base import DimensionCandidate, DimensionCase
from .common import SourceDimensionBuilder, ensure_event_ids_exist, evidence_events, stable_id
from .registry import register_dimension_builder


def _memory_type(content: str) -> str:
    lowered = content.lower()
    if any(token in lowered for token in ("prefer", "favorite", "enjoy", "like ")):
        return "preference"
    if any(token in lowered for token in ("plan", "goal", "want to", "trying to")):
        return "goal"
    return "personal_fact"


@register_dimension_builder
class D01WriteBuilder(SourceDimensionBuilder):
    dimension_id = "D01"
    dimension_name = "memory_extraction_and_write"
    payload_type = "write"
    source_datasets = frozenset({"longmemeval"})
    default_target_count = 37

    def derive_gold(self, candidate: DimensionCandidate) -> DimensionCandidate:
        record_id = str(candidate["source_record_id"])
        reviewed = candidate.get("source_metadata", {}).get("reviewed_gold_memories")
        selected = evidence_events(candidate)
        if isinstance(reviewed, list) and reviewed:
            gold_memories = [dict(item) for item in reviewed if isinstance(item, dict)]
            review_status = "reviewed"
        else:
            gold_memories: list[dict[str, Any]] = []
            for index, event in enumerate(selected):
                gold_memories.append(
                    {
                        "memory_id": f"d01:{stable_id(record_id)}:m{index:02d}",
                        "canonical_content": event["content"],
                        "memory_type": _memory_type(str(event["content"])),
                        "evidence_event_ids": [event["event_id"]],
                    }
                )
            review_status = "semantic_review_required"
        if not gold_memories:
            raise ValueError(f"D01 source record {record_id!r} has no memory evidence")
        return self.make_case(
            candidate,
            case_id=f"d01:{stable_id(record_id)}",
            query=str(candidate["source_gold"].get("question", "Extract memories from this context.")),
            gold_payload={
                "scored_event_ids": [event["event_id"] for event in candidate["events"]],
                "gold_memories": gold_memories,
            },
            metadata={"annotation_status": review_status},
        )

    def validate_cases(self, cases: list[DimensionCase]) -> list[DimensionCase]:
        validated = super().validate_cases(cases)
        for case in validated:
            memories = case["gold_payload"].get("gold_memories")
            if not isinstance(memories, list) or not memories:
                raise ValueError(f"Case {case['case_id']!r} must contain gold_memories")
            ensure_event_ids_exist(
                case,
                [event_id for item in memories for event_id in item.get("evidence_event_ids", [])],
                "gold_memories",
            )
        return validated
