"""Shared, dimension-neutral Source Adapter helpers."""

from __future__ import annotations

import ast
import csv
import json
from pathlib import Path
from typing import Any, Iterable, Iterator

from .base import CanonicalEvent, CanonicalSourceRecord


def iter_json_records(path: Path) -> Iterator[dict[str, Any]]:
    if not path.is_file():
        raise FileNotFoundError(f"Source file not found: {path}")
    if path.suffix.lower() == ".jsonl":
        with path.open("r", encoding="utf-8-sig") as handle:
            for line_number, line in enumerate(handle, start=1):
                if not line.strip():
                    continue
                value = json.loads(line)
                if not isinstance(value, dict):
                    raise ValueError(f"{path}:{line_number} is not a JSON object")
                yield value
        return
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    rows = payload if isinstance(payload, list) else [payload]
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise ValueError(f"{path} record {index} is not a JSON object")
        yield row


def iter_csv_records(path: Path) -> Iterator[dict[str, Any]]:
    if not path.is_file():
        raise FileNotFoundError(f"Source file not found: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        yield from csv.DictReader(handle)


def iter_parquet_records(path: Path, *, patterns: tuple[str, ...] = ("*.parquet",)) -> Iterator[dict[str, Any]]:
    try:
        import pyarrow.parquet as parquet
    except ImportError as exc:
        raise RuntimeError(
            "Parquet Source Adapter requires pyarrow; install dataset/build_pipeline/requirements.txt"
        ) from exc

    if path.is_file():
        files = [path]
    elif path.is_dir():
        files = sorted({file for pattern in patterns for file in path.rglob(pattern)})
    else:
        raise FileNotFoundError(f"Source path not found: {path}")
    if not files:
        raise FileNotFoundError(f"No allowed Parquet files found under: {path}")
    for file in files:
        parquet_file = parquet.ParquetFile(file)
        row_index = 0
        for batch in parquet_file.iter_batches(batch_size=32):
            for row in batch.to_pylist():
                row["__source_file__"] = str(file)
                row["__source_row_index__"] = row_index
                row_index += 1
                yield row


def parse_literal_mapping(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if not isinstance(value, str) or not value.strip():
        return {}
    try:
        parsed = ast.literal_eval(value)
    except (SyntaxError, ValueError):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return {"raw": value}
    return parsed if isinstance(parsed, dict) else {"value": parsed}


def make_events(
    source_record_id: str,
    messages: Iterable[dict[str, Any]],
    *,
    default_session_id: str = "s0",
) -> list[CanonicalEvent]:
    events: list[CanonicalEvent] = []
    for message in messages:
        content = str(message.get("content", message.get("text", ""))).strip()
        if not content:
            continue
        sequence = len(events)
        source_id = str(
            message.get("source_id", message.get("dia_id", message.get("id", sequence)))
        )
        metadata = {
            str(key): value
            for key, value in message.items()
            if key
            not in {
                "content",
                "text",
                "role",
                "timestamp",
                "session_id",
                "source_id",
            }
        }
        events.append(
            {
                "event_id": f"{source_record_id}:event:{sequence:06d}",
                "session_id": str(message.get("session_id", default_session_id)),
                "sequence": sequence,
                "role": str(message.get("role", "unknown")),
                "content": content,
                "timestamp": str(message.get("timestamp", "")),
                "source_id": source_id,
                "metadata": metadata,
            }
        )
    return events


def from_eval_case(
    source_dataset: str,
    case: dict[str, Any],
    *,
    source_gold: dict[str, Any] | None = None,
    source_metadata: dict[str, Any] | None = None,
) -> CanonicalSourceRecord:
    record_id = str(case["case_id"])
    messages: list[dict[str, Any]] = []
    for session in case.get("sessions", []):
        if not isinstance(session, dict):
            continue
        session_id = str(session.get("session_id", "s0"))
        timestamp = str(session.get("timestamp", ""))
        for message in session.get("messages", []):
            if isinstance(message, dict):
                messages.append({**message, "session_id": session_id, "timestamp": timestamp})
    gold = {
        "question": case.get("question", ""),
        "answer": case.get("gold_answer", ""),
        "evidence_session_ids": case.get("evidence_session_ids", []),
    }
    if source_gold:
        gold.update(source_gold)
    metadata = dict(case.get("dataset_metadata", {}))
    metadata.setdefault("question_type", case.get("question_type", ""))
    metadata.setdefault("question_date", case.get("question_date", ""))
    metadata.update(source_metadata or {})
    return {
        "source_dataset": source_dataset,
        "source_record_id": record_id,
        "events": make_events(record_id, messages),
        "source_gold": gold,
        "source_metadata": metadata,
    }


def flatten_message_objects(value: Any) -> list[dict[str, Any]]:
    """Collect message-shaped objects from nested lists/dicts in source order."""

    output: list[dict[str, Any]] = []
    if isinstance(value, list):
        for item in value:
            output.extend(flatten_message_objects(item))
    elif isinstance(value, dict):
        if "role" in value and ("content" in value or "text" in value):
            output.append(value)
        else:
            for item in value.values():
                output.extend(flatten_message_objects(item))
    return output
