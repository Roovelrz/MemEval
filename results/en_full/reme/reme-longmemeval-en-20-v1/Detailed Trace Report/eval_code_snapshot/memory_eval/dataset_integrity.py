"""Freeze source integrity evidence and validate the cases selected for one run."""

from __future__ import annotations

import hashlib
import json
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _case_id(case: dict[str, Any]) -> str:
    return str(case.get("case_id") or case.get("question_id") or case.get("id") or "")


def _sessions(case: dict[str, Any]) -> list[dict[str, Any]]:
    value = case.get("sessions", case.get("haystack_sessions", []))
    return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []


def _turns(session: dict[str, Any]) -> list[dict[str, Any]]:
    value = session.get("turns", session.get("messages", []))
    return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []


def _evidence_ids(case: dict[str, Any]) -> list[str]:
    value = case.get("answer_session_ids", case.get("evidence_session_ids", []))
    return [str(item) for item in value] if isinstance(value, list) else []


def _timestamp_valid(value: object) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    cleaned = re.sub(r"\s+\([A-Za-z]{3}\)\s+", " ", value.strip())
    if cleaned.endswith("Z"):
        cleaned = cleaned[:-1] + "+00:00"
    try:
        datetime.fromisoformat(cleaned.replace("/", "-"))
        return True
    except ValueError:
        return False


def build_dataset_validation(
    cases: Iterable[dict[str, Any]], *, source_case_count: int | None = None
) -> dict[str, Any]:
    selected = list(cases)
    case_ids = [_case_id(case) for case in selected]
    session_count = 0
    turn_count = 0
    evidence_count = 0
    missing_evidence_id_count = 0
    duplicate_session_id_count = 0
    timestamp_anomaly_count = 0

    for case in selected:
        sessions = _sessions(case)
        session_ids = [str(session.get("session_id", "")) for session in sessions]
        evidence_ids = _evidence_ids(case)
        session_count += len(sessions)
        turn_count += sum(len(_turns(session)) for session in sessions)
        evidence_count += len(evidence_ids)
        duplicate_session_id_count += len(session_ids) - len(set(session_ids))
        missing_evidence_id_count += len(set(evidence_ids) - set(session_ids))
        timestamp_anomaly_count += sum(not _timestamp_valid(session.get("timestamp")) for session in sessions)

    counts = {
        "actual_loaded_case_count": len(selected),
        "actual_loaded_session_count": session_count,
        "actual_loaded_turn_count": turn_count,
        "evidence_session_count": evidence_count,
        "missing_question_count": sum(not str(case.get("question", "")).strip() for case in selected),
        "missing_gold_answer_count": sum(
            not str(case.get("gold_answer", case.get("answer", ""))).strip() for case in selected
        ),
        "missing_evidence_id_count": missing_evidence_id_count,
        "duplicate_session_id_count": duplicate_session_id_count,
        "duplicate_case_id_count": len(case_ids) - len(set(case_ids)),
        "timestamp_anomaly_count": timestamp_anomaly_count,
        "data_parse_failure_count": 0,
        "data_skipped_count": 0,
        "unselected_case_count": max(0, int(source_case_count or len(selected)) - len(selected)),
    }
    critical = (
        "missing_question_count",
        "missing_gold_answer_count",
        "missing_evidence_id_count",
        "duplicate_case_id_count",
        "timestamp_anomaly_count",
        "data_parse_failure_count",
        "data_skipped_count",
    )
    status = "PASS" if not any(counts[name] for name in critical) else "FAIL"
    if status == "PASS" and counts["duplicate_session_id_count"]:
        status = "PASS_WITH_WARNINGS"
    return {
        "schema_version": "memory_eval_run_dataset_validation_v1",
        "status": status,
        "scope": "selected_cases",
        "selected_case_ids": case_ids,
        "counts": counts,
        "notes": {
            "unselected_cases": "Intentional case selection is not counted as skipped data.",
            "timestamp_validation": "Accepts ISO-like YYYY-MM-DD or YYYY/MM/DD timestamps with an optional weekday and time.",
        },
    }


def freeze_dataset_integrity(
    dataset_path: Path,
    run_dir: Path,
    selected_cases: Iterable[dict[str, Any]],
    *,
    source_case_count: int | None = None,
) -> dict[str, Any]:
    """Write a run-scoped validation and copy the source integrity report."""

    report = build_dataset_validation(selected_cases, source_case_count=source_case_count)
    source_integrity = dataset_path.with_name("integrity_report.json")
    frozen_integrity = run_dir / "integrity_report.json"
    if source_integrity.is_file():
        shutil.copy2(source_integrity, frozen_integrity)
        source_payload = json.loads(source_integrity.read_text(encoding="utf-8"))
        report["source_integrity"] = {
            "status": source_payload.get("status", "NOT_RECORDED"),
            "sha256": _sha256(frozen_integrity),
            "artifact": str(frozen_integrity),
        }
    else:
        report["source_integrity"] = {
            "status": "NOT_RECORDED",
            "sha256": "NOT_RECORDED",
            "artifact": "NOT_RECORDED",
        }
    validation_path = run_dir / "dataset_validation.json"
    validation_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report
