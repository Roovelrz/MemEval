"""Dependency-free parsing helpers shared by dataset adapters."""

from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import Any, Iterable


def load_json_or_jsonl(path: Path) -> list[dict[str, Any]]:
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        raise ValueError(f"Dataset is empty: {path}")
    if path.suffix.lower() == ".jsonl":
        rows = [json.loads(line) for line in text.splitlines() if line.strip()]
        if not all(isinstance(row, dict) for row in rows):
            raise ValueError("Every JSONL line must be an object")
        return rows

    payload = json.loads(text)
    if isinstance(payload, list) and all(isinstance(row, dict) for row in payload):
        return payload
    if isinstance(payload, dict):
        for key in ("cases", "items", "data", "samples"):
            value = payload.get(key)
            if isinstance(value, list) and all(isinstance(row, dict) for row in value):
                return value
    raise ValueError(f"Cannot find a case list in dataset: {path}")


def first_value(obj: dict[str, Any], keys: Iterable[str], default: Any = None) -> Any:
    for key in keys:
        if key in obj and obj[key] is not None:
            return obj[key]
    return default


def normalize_message(message: dict[str, Any]) -> dict[str, Any]:
    role = first_value(message, ("role", "speaker"), "unknown")
    content = first_value(message, ("content", "text", "translated_content", "zh_content"), "")
    normalized = {
        "role": str(role),
        "content": str(content),
        "has_answer": message.get("has_answer"),
    }
    if message.get("speaker") is not None:
        normalized["speaker"] = str(message["speaker"])
    if message.get("dia_id") is not None:
        normalized["dia_id"] = str(message["dia_id"])
    return normalized


def normalize_session(session: dict[str, Any], index: int) -> dict[str, Any]:
    session_id = first_value(session, ("session_id", "id"), f"session_{index:04d}")
    timestamp = first_value(session, ("timestamp", "date", "session_date"), "")
    raw_messages = first_value(session, ("messages", "turns"), [])
    if not isinstance(raw_messages, list):
        raise ValueError(f"Session {session_id!r} messages/turns must be a list")
    return {
        "session_id": str(session_id),
        "timestamp": str(timestamp),
        "messages": [normalize_message(message) for message in raw_messages if isinstance(message, dict)],
        "is_evidence_session": bool(session.get("is_evidence_session", False)),
    }


def parse_json_like(value: Any, default: Any) -> Any:
    if not isinstance(value, str):
        return value if value is not None else default
    text = value.strip()
    if not text:
        return default
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        try:
            return ast.literal_eval(text)
        except (ValueError, SyntaxError):
            return default

