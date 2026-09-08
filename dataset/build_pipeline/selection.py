"""Deterministic selection snapshots for the frozen MemEval release."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


def collect_selected_sources(version_dir: str | Path) -> list[dict[str, str]]:
    """Return the frozen Case-to-source selection in stable Case ID order."""

    cases_dir = Path(version_dir) / "cases"
    entries = []
    for case_path in cases_dir.glob("*.json"):
        case = json.loads(case_path.read_text(encoding="utf-8"))
        envelope = case.get("envelope", {})
        source = envelope.get("source", {})
        query = envelope.get("query", {})
        entry = {
            "case_id": str(envelope.get("case_id", "")).strip(),
            "source_record_id": str(source.get("source_record_id", "")).strip(),
            "source_question_id": str(
                source.get("source_question_id") or query.get("query_id") or ""
            ).strip(),
        }
        missing = [name for name, value in entry.items() if not value]
        if missing:
            raise ValueError(f"{case_path.name} selection is missing: {', '.join(missing)}")
        entries.append(entry)
    if not entries:
        raise FileNotFoundError(f"No frozen Cases found under: {cases_dir}")
    return sorted(entries, key=lambda entry: entry["case_id"])


def selected_sources_sha256(entries: list[dict[str, str]]) -> str:
    payload = json.dumps(entries, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def build_selected_sources_snapshot(version_dir: str | Path) -> dict[str, Any]:
    entries = collect_selected_sources(version_dir)
    return {
        "case_count": len(entries),
        "sha256": selected_sources_sha256(entries),
        "entries": entries,
    }


def manifest_selection_seed(manifest: dict[str, Any]) -> str:
    selection = manifest.get("selection")
    if isinstance(selection, dict) and selection.get("seed"):
        return str(selection["seed"])
    construction = manifest.get("construction")
    if isinstance(construction, dict) and construction.get("selection_seed"):
        return str(construction["selection_seed"])
    return ""


def validate_selected_sources(version_dir: str | Path, manifest: dict[str, Any]) -> list[str]:
    errors = []
    if not manifest_selection_seed(manifest):
        errors.append("selection seed is missing")
    expected = build_selected_sources_snapshot(version_dir)
    actual = manifest.get("selected_sources")
    if actual != expected:
        errors.append("selected_sources does not match the frozen Cases")
    return errors
