"""LongMemEval-S cleaned JSON adapter."""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from .models import EvalCase, EvalSession


REQUIRED_FIELDS = {
    "question_id",
    "question_type",
    "question",
    "answer",
    "question_date",
    "haystack_session_ids",
    "haystack_dates",
    "haystack_sessions",
    "answer_session_ids",
}


def _timestamp_key(value: str) -> tuple[int, datetime | str]:
    normalized = re.sub(r"\s+\([A-Za-z]+\)", "", value).strip()
    try:
        return (0, datetime.strptime(normalized, "%Y/%m/%d %H:%M"))
    except ValueError:
        return (1, value)


def _require_record(record: Any, index: int) -> dict[str, Any]:
    if not isinstance(record, dict):
        raise ValueError(f"record {index} must be a JSON object")
    missing = sorted(REQUIRED_FIELDS - record.keys())
    if missing:
        raise ValueError(f"record {index} is missing fields: {', '.join(missing)}")
    return record


def _load_case(record: dict[str, Any], index: int) -> EvalCase:
    session_ids = record["haystack_session_ids"]
    dates = record["haystack_dates"]
    histories = record["haystack_sessions"]
    if not all(isinstance(value, list) for value in (session_ids, dates, histories)):
        raise ValueError(f"record {index} haystack fields must be arrays")
    if not (len(session_ids) == len(dates) == len(histories)):
        raise ValueError(
            f"record {index} haystack lengths differ: "
            f"ids={len(session_ids)}, dates={len(dates)}, sessions={len(histories)}"
        )

    sessions: list[EvalSession] = []
    for session_id, timestamp, messages in zip(session_ids, dates, histories, strict=True):
        if not isinstance(messages, list):
            raise ValueError(f"record {index} session {session_id!r} messages must be an array")
        sessions.append(
            EvalSession(
                session_id=str(session_id),
                timestamp=str(timestamp),
                messages=messages,
            )
        )
    sessions.sort(key=lambda session: _timestamp_key(session.timestamp))

    case_id = str(record["question_id"])
    answer_session_ids = record["answer_session_ids"]
    if not isinstance(answer_session_ids, list):
        raise ValueError(f"record {index} answer_session_ids must be an array")
    return EvalCase(
        id=case_id,
        question_type=str(record["question_type"]),
        question=str(record["question"]),
        gold_answer=str(record["answer"]),
        question_date=str(record["question_date"]),
        sessions=sessions,
        answer_session_ids=[str(value) for value in answer_session_ids],
        is_abstention=case_id.endswith("_abs"),
    )


def load_longmemeval(path: str | Path, limit: int | None = None) -> list[EvalCase]:
    """Load LongMemEval-S cleaned data into the canonical EvalCase boundary."""
    if limit is not None and limit < 1:
        raise ValueError("limit must be positive")
    source = Path(path)
    payload = json.loads(source.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("LongMemEval-S cleaned input must be a JSON array")
    selected = payload if limit is None else payload[:limit]
    return [_load_case(_require_record(record, index), index) for index, record in enumerate(selected)]
