"""PersonaMem-v2 text benchmark adapter."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from .base import DatasetLoadResult, selected_indices, validate_canonical_case
from .common import parse_json_like


def _query_text(value: Any) -> str:
    parsed = parse_json_like(value, {})
    if isinstance(parsed, dict):
        return str(parsed.get("content", ""))
    return str(value or "")


def _load_history(csv_path: Path, link: str) -> list[dict[str, Any]]:
    benchmark_root = csv_path.parent.parent.parent
    history_path = (benchmark_root / link).resolve()
    if not history_path.is_file():
        raise FileNotFoundError(f"PersonaMem chat history not found: {history_path}")
    payload = json.loads(history_path.read_text(encoding="utf-8"))
    history = payload.get("chat_history") if isinstance(payload, dict) else payload
    if not isinstance(history, list):
        raise ValueError(f"PersonaMem chat history is not a list: {history_path}")
    return [message for message in history if isinstance(message, dict)]


def normalize_personamem_case(row: dict[str, str], row_index: int, csv_path: Path) -> dict[str, Any]:
    history_link = row.get("chat_history_32k_link") or row.get("chat_history_128k_link") or ""
    history = _load_history(csv_path, history_link)
    related = parse_json_like(row.get("related_conversation_snippet", ""), [])
    related_pairs = {
        (str(message.get("role", "")), str(message.get("content", "")).strip())
        for message in related
        if isinstance(message, dict)
    }
    base_time = datetime(2000, 1, 1, tzinfo=timezone.utc)
    sessions: list[dict[str, Any]] = []
    evidence_session_ids: list[str] = []
    for message_index, message in enumerate(history):
        session_id = f"m{message_index:04d}"
        role = str(message.get("role", "unknown"))
        content = str(message.get("content", ""))
        is_evidence = (role, content.strip()) in related_pairs
        sessions.append(
            {
                "session_id": session_id,
                "timestamp": (base_time + timedelta(minutes=message_index)).isoformat(),
                "messages": [{"role": role, "content": content, "has_answer": is_evidence}],
                "is_evidence_session": is_evidence,
            }
        )
        if is_evidence:
            evidence_session_ids.append(session_id)
    if related_pairs and not evidence_session_ids:
        raise ValueError(f"PersonaMem row {row_index} related snippet was not found in its chat history")

    question_date = (base_time + timedelta(minutes=len(history))).isoformat()
    persona_id = str(row.get("persona_id", "unknown"))
    return validate_canonical_case(
        {
            "case_id": f"personamem-v2:{persona_id}:{row_index:05d}",
            "question": _query_text(row.get("user_query")),
            "gold_answer": str(row.get("correct_answer", "")),
            "question_type": str(row.get("pref_type") or "persona_preference"),
            "question_date": question_date,
            "sessions": sessions,
            "evidence_session_ids": evidence_session_ids,
            "dataset_metadata": {
                "persona_id": persona_id,
                "preference": row.get("preference", ""),
                "topic": row.get("topic_query", ""),
                "updated": row.get("updated", ""),
                "sensitive_info": row.get("sensitive_info", ""),
                "history_link": history_link,
            },
        }
    )


class PersonaMemV2DatasetAdapter:
    name = "personamem-v2"

    def load(
        self,
        path: Path,
        *,
        start: int = 0,
        limit: int = 0,
        shuffle: bool = False,
        seed: int = 42,
    ) -> DatasetLoadResult:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            rows = list(csv.DictReader(handle))
        indices = selected_indices(len(rows), start=start, limit=limit, shuffle=shuffle, seed=seed)
        cases = [normalize_personamem_case(rows[index], index, path) for index in indices]
        return DatasetLoadResult(cases=cases, source_case_count=len(rows), adapter_name=self.name)

