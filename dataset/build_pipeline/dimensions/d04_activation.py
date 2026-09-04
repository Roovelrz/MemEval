"""D04 proactive memory activation builder."""

from __future__ import annotations

import hashlib

from .base import DimensionCandidate, DimensionCase
from .common import SourceDimensionBuilder, ensure_event_ids_exist, stable_id
from .registry import register_dimension_builder


@register_dimension_builder
class D04ActivationBuilder(SourceDimensionBuilder):
    dimension_id = "D04"
    dimension_name = "proactive_memory_activation"
    payload_type = "activation"
    source_datasets = frozenset({"prefeval"})
    default_target_count = 38

    def derive_gold(self, candidate: DimensionCandidate) -> DimensionCandidate:
        record_id = str(candidate["source_record_id"])
        preference_type = str(candidate.get("source_metadata", {}).get("preference_type", ""))
        should_activate = preference_type in {"implicit_choice", "implicit_persona"}
        required_memory_ids = (
            [event["event_id"] for event in candidate["events"]] if should_activate else []
        )
        return self.make_case(
            candidate,
            case_id=f"d04:{stable_id(record_id)}",
            query=str(candidate["source_gold"].get("question", "")),
            gold_payload={
                "should_activate": should_activate,
                "required_memory_ids": required_memory_ids,
                "preference": candidate["source_gold"].get("preference", ""),
                "answer_criteria": {
                    "explanation": candidate["source_gold"].get("explanation", ""),
                    "must_respect_preference": True,
                    "aligned_option": candidate["source_gold"].get("aligned_option"),
                },
            },
            metadata={"activation_form": preference_type},
        )

    def sample_cases(self, candidates: list[DimensionCandidate]) -> list[DimensionCase]:
        if not self.target_count:
            return super().sample_cases(candidates)
        groups: dict[int, dict[str, DimensionCase]] = {}
        for candidate in candidates:
            row_index = candidate.get("metadata", {}).get("source_row_index")
            form = str(candidate.get("metadata", {}).get("activation_form", ""))
            if isinstance(row_index, int):
                groups.setdefault(row_index, {})[form] = candidate
        eligible = [
            (row_index, forms)
            for row_index, forms in groups.items()
            if "explicit_preference" in forms
            and ("implicit_choice" in forms or "implicit_persona" in forms)
        ]
        eligible.sort(
            key=lambda item: hashlib.sha256(f"{self.seed}:{item[0]}".encode("utf-8")).hexdigest()
        )
        pair_target = self.target_count // 2
        output: list[DimensionCase] = []
        choice_target = (pair_target + 1) // 2
        choice_used = 0
        for _, forms in eligible[:pair_target]:
            preferred = "implicit_choice" if choice_used < choice_target else "implicit_persona"
            positive = forms.get(preferred) or forms.get("implicit_persona") or forms["implicit_choice"]
            if positive.get("metadata", {}).get("activation_form") == "implicit_choice":
                choice_used += 1
            output.extend([forms["explicit_preference"], positive])
        return output

    def validate_cases(self, cases: list[DimensionCase]) -> list[DimensionCase]:
        validated = super().validate_cases(cases)
        positives = 0
        for case in validated:
            payload = case["gold_payload"]
            required = payload.get("required_memory_ids", [])
            if payload.get("should_activate"):
                positives += 1
                if not required:
                    raise ValueError(f"Positive activation Case {case['case_id']!r} has no required memory")
                ensure_event_ids_exist(case, required, "required_memory_ids")
            elif required:
                raise ValueError(f"Negative activation Case {case['case_id']!r} has required memories")
        if len(validated) == self.target_count and positives * 2 != len(validated):
            raise ValueError("D04 target output must contain equal positive and negative cases")
        return validated
