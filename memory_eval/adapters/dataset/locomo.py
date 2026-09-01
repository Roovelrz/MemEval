"""LoCoMo QA adapter."""

from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from .base import DatasetLoadResult, selected_indices, validate_canonical_case
from .common import load_json_or_jsonl


SESSION_KEY = re.compile(r"^session_(\d+)$")


def _timestamp(value: object, sequence: int) -> str:
    text = str(value or "").strip()
    for pattern in ("%I:%M %p on %d %B, %Y", "%I:%M %p on %d %B %Y"):
        try:
            return datetime.strptime(text, pattern).replace(tzinfo=timezone.utc).isoformat()
        except ValueError:
            pass
    return (datetime(2000, 1, 1, tzinfo=timezone.utc) + timedelta(days=sequence)).isoformat()


def _sessions(conversation: dict[str, Any], evidence_turns: set[str]) -> list[dict[str, Any]]:
    speaker_a = str(conversation.get("speaker_a", "speaker_a"))
    speaker_b = str(conversation.get("speaker_b", "speaker_b"))
    numbered: list[tuple[int, list[dict[str, Any]]]] = []
    for key, value in conversation.items():
        match = SESSION_KEY.match(key)
        if match and isinstance(value, list):
            numbered.append((int(match.group(1)), [turn for turn in value if isinstance(turn, dict)]))
    output: list[dict[str, Any]] = []
    for number, turns in sorted(numbered):
        session_id = f"D{number}"
        messages = []
        for turn in turns:
            speaker = str(turn.get("speaker", "unknown"))
            messages.append(
                {
                    "role": "user" if speaker == speaker_a else ("assistant" if speaker == speaker_b else "unknown"),
                    "speaker": speaker,
                    "content": str(turn.get("text", turn.get("content", ""))),
                    "dia_id": str(turn.get("dia_id", "")),
                    "has_answer": str(turn.get("dia_id", "")) in evidence_turns,
                }
            )
        output.append(
            {
                "session_id": session_id,
                "timestamp": _timestamp(conversation.get(f"session_{number}_date_time"), number),
                "messages": messages,
                "is_evidence_session": session_id in {turn.split(":", 1)[0] for turn in evidence_turns},
            }
        )
    return output


def normalize_locomo_case(sample: dict[str, Any], qa_index: int) -> dict[str, Any]:
    qa_rows = sample.get("qa")
    conversation = sample.get("conversation")
    if not isinstance(qa_rows, list) or not isinstance(conversation, dict):
        raise ValueError("LoCoMo sample must contain qa and conversation")
    qa = qa_rows[qa_index]
    if not isinstance(qa, dict):
        raise ValueError("LoCoMo QA entry must be an object")
    evidence_turns = {
        str(value).strip().strip("()")
        for value in qa.get("evidence", [])
        if str(value).strip().strip("()")
    }
    sessions = _sessions(conversation, evidence_turns)
    evidence_session_ids = sorted(
        {turn.split(":", 1)[0] for turn in evidence_turns},
        key=lambda value: int(value[1:]) if value[1:].isdigit() else value,
    )
    sample_id = str(sample.get("sample_id", "unknown"))
    question_date = sessions[-1]["timestamp"] if sessions else "2000-01-01T00:00:00+00:00"
    return validate_canonical_case(
        {
            "case_id": f"locomo:{sample_id}:{qa_index:04d}",
            "question": str(qa.get("question", "")),
            "gold_answer": str(qa.get("answer", "")),
            "question_type": f"locomo_category_{qa.get('category', 'unknown')}",
            "question_date": question_date,
            "sessions": sessions,
            "evidence_session_ids": evidence_session_ids,
            "speaker_1_name": str(conversation.get("speaker_a", "speaker_a")),
            "speaker_2_name": str(conversation.get("speaker_b", "speaker_b")),
            "dataset_metadata": {
                "sample_id": sample_id,
                "qa_index": qa_index,
                "category": qa.get("category"),
                "evidence_turn_ids": sorted(evidence_turns),
            },
        }
    )


class LoCoMoDatasetAdapter:
    name = "locomo"

    def load(
        self,
        path: Path,
        *,
        start: int = 0,
        limit: int = 0,
        shuffle: bool = False,
        seed: int = 42,
    ) -> DatasetLoadResult:
        samples = load_json_or_jsonl(path)
        references = [
            (sample_index, qa_index)
            for sample_index, sample in enumerate(samples)
            for qa_index in range(len(sample.get("qa", [])) if isinstance(sample.get("qa"), list) else 0)
        ]
        indices = selected_indices(len(references), start=start, limit=limit, shuffle=shuffle, seed=seed)
        cases = [
            normalize_locomo_case(samples[references[index][0]], references[index][1])
            for index in indices
        ]
        return DatasetLoadResult(cases=cases, source_case_count=len(references), adapter_name=self.name)

