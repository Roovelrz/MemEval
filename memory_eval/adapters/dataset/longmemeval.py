"""LongMemEval and canonical JSON/JSONL dataset adapter."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .base import DatasetLoadResult, selected_indices, validate_canonical_case
from .common import first_value, load_json_or_jsonl, normalize_session


def normalize_case(raw: dict[str, Any], index: int) -> dict[str, Any]:
    """Map Clean LongMemEval or a compatible record to the eval schema."""

    case_id = first_value(raw, ("case_id", "question_id", "id"), f"case_{index:04d}")
    question = first_value(raw, ("question", "query"), "")
    gold_answer = first_value(raw, ("gold_answer", "answer"), "")
    raw_sessions = raw.get("sessions")

    if raw_sessions is None and "haystack_sessions" in raw:
        ids = raw.get("haystack_session_ids", [])
        dates = raw.get("haystack_dates", [])
        histories = raw.get("haystack_sessions", [])
        if not (isinstance(ids, list) and isinstance(dates, list) and isinstance(histories, list)):
            raise ValueError(f"Case {case_id!r} has invalid LongMemEval haystack fields")
        if not (len(ids) == len(dates) == len(histories)):
            raise ValueError(f"Case {case_id!r} has mismatched LongMemEval haystack lengths")
        raw_sessions = [
            {
                "session_id": session_id,
                "timestamp": timestamp,
                "messages": messages,
                "is_evidence_session": session_id in raw.get("answer_session_ids", []),
            }
            for session_id, timestamp, messages in zip(ids, dates, histories, strict=True)
        ]
    if not isinstance(raw_sessions, list):
        raise ValueError(f"Case {case_id!r} has no sessions list")

    sessions = [normalize_session(session, i) for i, session in enumerate(raw_sessions) if isinstance(session, dict)]
    explicit_evidence = first_value(raw, ("evidence_session_ids", "answer_session_ids"), None)
    if explicit_evidence is None:
        evidence_ids = [session["session_id"] for session in sessions if session["is_evidence_session"]]
    elif isinstance(explicit_evidence, list):
        evidence_ids = [str(value) for value in explicit_evidence]
    else:
        raise ValueError(f"Case {case_id!r} evidence session IDs must be a list")

    case = {
        "case_id": str(case_id),
        "question": str(question),
        "gold_answer": str(gold_answer),
        "question_type": str(raw.get("question_type", "")),
        "question_date": str(raw.get("question_date", "")),
        "sessions": sessions,
        "evidence_session_ids": evidence_ids,
        "dataset_metadata": dict(raw.get("dataset_metadata", {})) if isinstance(raw.get("dataset_metadata"), dict) else {},
    }
    for name in ("speaker_1_name", "speaker_2_name"):
        if raw.get(name) is not None:
            case[name] = str(raw[name])
    return validate_canonical_case(case)


class LongMemEvalDatasetAdapter:
    name = "longmemeval"

    def load(
        self,
        path: Path,
        *,
        start: int = 0,
        limit: int = 0,
        shuffle: bool = False,
        seed: int = 42,
    ) -> DatasetLoadResult:
        rows = load_json_or_jsonl(path)
        indices = selected_indices(len(rows), start=start, limit=limit, shuffle=shuffle, seed=seed)
        cases = [normalize_case(rows[index], index) for index in indices]
        return DatasetLoadResult(cases=cases, source_case_count=len(rows), adapter_name=self.name)

