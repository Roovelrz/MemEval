"""D06 dynamic update and conflict-resolution builder."""

from __future__ import annotations

from typing import Iterable

from ..sources.base import CanonicalSourceRecord
from .base import DimensionCandidate, DimensionCase
from .common import SourceDimensionBuilder, first_answer, stable_id
from .registry import register_dimension_builder


@register_dimension_builder
class D06ConflictBuilder(SourceDimensionBuilder):
    dimension_id = "D06"
    dimension_name = "dynamic_update_conflict"
    payload_type = "conflict"
    source_datasets = frozenset({"memoryagentbench"})
    default_target_count = 37

    def load_candidates(
        self,
        records: Iterable[CanonicalSourceRecord],
    ) -> list[DimensionCandidate]:
        output: list[DimensionCandidate] = []
        for record in records:
            questions = record.get("source_gold", {}).get("questions", [])
            answers = record.get("source_gold", {}).get("answers", [])
            qa_pair_ids = record.get("source_gold", {}).get("qa_pair_ids", [])
            if not isinstance(questions, list) or not isinstance(answers, list):
                continue
            for index, (question, answer) in enumerate(zip(questions, answers, strict=False)):
                qa_pair_id = (
                    str(qa_pair_ids[index])
                    if isinstance(qa_pair_ids, list) and index < len(qa_pair_ids)
                    else f"{record['source_record_id']}:q{index:04d}"
                )
                output.append(
                    {
                        **record,
                        "source_record_id": qa_pair_id,
                        "source_gold": {
                            **record["source_gold"],
                            "question": question,
                            "answer": answer,
                        },
                        "source_metadata": {
                            **record["source_metadata"],
                            "parent_source_record_id": record["source_record_id"],
                            "source_question_index": index,
                        },
                    }
                )
        return output

    def derive_gold(self, candidate: DimensionCandidate) -> DimensionCandidate:
        record_id = str(candidate["source_record_id"])
        reviewed_versions = candidate.get("source_metadata", {}).get("reviewed_fact_versions")
        if isinstance(reviewed_versions, list) and reviewed_versions:
            fact_versions = [dict(item) for item in reviewed_versions if isinstance(item, dict)]
            status = "reviewed"
        else:
            previous_events = candidate["source_gold"].get("previous_events")
            fact_versions = previous_events if isinstance(previous_events, list) else []
            status = "semantic_review_required"
        winning_ids = [
            str(item.get("fact_id"))
            for item in fact_versions
            if isinstance(item, dict) and item.get("status") == "winning" and item.get("fact_id")
        ]
        stale_ids = [
            str(item.get("fact_id"))
            for item in fact_versions
            if isinstance(item, dict) and item.get("status") == "stale" and item.get("fact_id")
        ]
        source_name = str(candidate.get("source_metadata", {}).get("source", ""))
        conflict_type = "multi-hop" if "_mh_" in source_name or "_mh_" in record_id else "single-hop"
        return self.make_case(
            candidate,
            case_id=f"d06:{stable_id(record_id)}",
            query=str(candidate["source_gold"].get("question", "")),
            gold_payload={
                "gold_answer": first_answer(candidate["source_gold"].get("answer")),
                "conflict_type": conflict_type,
                "fact_versions": fact_versions,
                "winning_fact_ids": winning_ids,
                "stale_fact_ids": stale_ids,
            },
            metadata={"annotation_status": status},
        )

    def validate_cases(self, cases: list[DimensionCase]) -> list[DimensionCase]:
        validated = super().validate_cases(cases)
        for case in validated:
            payload = case["gold_payload"]
            if payload.get("gold_answer") in (None, ""):
                raise ValueError(f"Case {case['case_id']!r} has no conflict-resolution answer")
            if case["metadata"].get("annotation_status") == "reviewed":
                versions = payload.get("fact_versions", [])
                if not versions or not payload.get("winning_fact_ids"):
                    raise ValueError(f"Reviewed Case {case['case_id']!r} has incomplete fact versions")
        return validated
