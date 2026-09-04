"""D07 ultra-long-context and scale-degradation builder."""

from __future__ import annotations

import hashlib
from typing import Any, Iterable

from ..sources.base import CanonicalSourceRecord
from .base import DimensionCandidate, DimensionCase
from .common import SourceDimensionBuilder, ensure_event_ids_exist, stable_id
from .registry import register_dimension_builder


TARGET_TOKENS = {"100K": 100_000, "500K": 500_000, "1M": 1_000_000, "10M": 10_000_000}


def _collect_source_ids(value: Any) -> set[str]:
    output: set[str] = set()
    if isinstance(value, (str, int)):
        output.add(str(value))
    elif isinstance(value, list):
        for item in value:
            output.update(_collect_source_ids(item))
    elif isinstance(value, dict):
        for item in value.values():
            output.update(_collect_source_ids(item))
    return output


@register_dimension_builder
class D07ScaleBuilder(SourceDimensionBuilder):
    dimension_id = "D07"
    dimension_name = "ultra_long_context"
    payload_type = "scale"
    source_datasets = frozenset({"beam"})
    default_target_count = 37

    def load_candidates(
        self,
        records: Iterable[CanonicalSourceRecord],
    ) -> list[DimensionCandidate]:
        output: list[DimensionCandidate] = []
        for record in records:
            probing = record.get("source_gold", {}).get("probing_questions", {})
            if not isinstance(probing, dict):
                continue
            for category, probes in probing.items():
                if not isinstance(probes, list):
                    continue
                for probe_index, probe in enumerate(probes):
                    if not isinstance(probe, dict) or not str(probe.get("question", "")).strip():
                        continue
                    output.append(
                        {
                            **record,
                            "source_record_id": f"{record['source_record_id']}:{category}:{probe_index}",
                            "source_gold": {**record["source_gold"], "probe": probe},
                            "source_metadata": {
                                **record["source_metadata"],
                                "parent_source_record_id": record["source_record_id"],
                                "ability_category": str(category),
                                "source_probe_index": probe_index,
                            },
                        }
                    )
        return output

    def derive_gold(self, candidate: DimensionCandidate) -> DimensionCandidate:
        record_id = str(candidate["source_record_id"])
        probe = candidate["source_gold"].get("probe", {})
        scale = str(candidate.get("source_metadata", {}).get("scale", "")).upper()
        answer = next(
            (
                probe[field]
                for field in (
                    "ideal_answer",
                    "ideal_response",
                    "answer",
                    "ideal_summary",
                    "expected_compliance",
                )
                if probe.get(field) not in (None, "")
            ),
            "",
        )
        referenced = _collect_source_ids(
            probe.get("source_chat_ids", probe.get("evidence_chat_ids", probe.get("chat_ids", [])))
        )
        evidence_ids = [
            event["event_id"]
            for event in candidate["events"]
            if str(event.get("source_id", "")) in referenced
            or str(event.get("metadata", {}).get("id", "")) in referenced
        ]
        question = str(probe.get("question", ""))
        scale_group = hashlib.sha256(question.encode("utf-8")).hexdigest()[:12]
        return self.make_case(
            candidate,
            case_id=f"d07:{stable_id(record_id)}",
            query=question,
            gold_payload={
                "scale_group_id": f"d07:scale_group:{scale_group}",
                "scale_level": scale,
                "target_tokens": TARGET_TOKENS.get(scale),
                "gold_answer": answer,
                "gold_evidence_ids": evidence_ids,
                "expected_retrievable": bool(evidence_ids),
            },
            metadata={
                "annotation_status": "reviewed" if evidence_ids else "evidence_review_required",
                "difficulty": probe.get("difficulty"),
                "source_rubric": probe.get("rubric"),
            },
        )

    def validate_cases(self, cases: list[DimensionCase]) -> list[DimensionCase]:
        validated = super().validate_cases(cases)
        for case in validated:
            payload = case["gold_payload"]
            if payload.get("scale_level") not in TARGET_TOKENS:
                raise ValueError(f"Case {case['case_id']!r} has an unsupported scale")
            if not str(payload.get("gold_answer", "")).strip():
                raise ValueError(f"Case {case['case_id']!r} has no scale gold answer")
            evidence_ids = payload.get("gold_evidence_ids", [])
            ensure_event_ids_exist(case, evidence_ids, "gold_evidence_ids")
            if payload.get("expected_retrievable") and not evidence_ids:
                raise ValueError(f"Case {case['case_id']!r} is retrievable but has no evidence")
        return validated
