"""AgentMemBench MemDialogue-v2 Source Adapter."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable

from .base import CanonicalSourceRecord, SourceAdapter
from .common import iter_json_records, make_events


class AgentMemBenchSourceAdapter(SourceAdapter):
    name = "agentmembench"

    def load_raw(self, path: Path) -> Iterable[dict[str, Any]]:
        return iter_json_records(path)

    def normalize(
        self,
        raw: dict[str, Any],
        raw_index: int,
        source_path: Path,
    ) -> Iterable[CanonicalSourceRecord]:
        record_id = str(raw.get("record_id") or f"agentmembench:{raw_index:06d}")
        memory_events = raw.get("memory_events")
        if not isinstance(memory_events, list):
            raise ValueError(f"AgentMemBench record {record_id!r} has no memory_events list")
        messages = [
            {
                "role": "user",
                "content": event.get("raw_text", ""),
                "source_id": event.get("turn_idx", index),
                "turn_idx": event.get("turn_idx"),
                "event_type": event.get("event_type"),
            }
            for index, event in enumerate(memory_events)
            if isinstance(event, dict)
        ]
        gold_events = [
            {
                "turn_idx": event.get("turn_idx"),
                "event_type": event.get("event_type"),
                "query": event.get("query"),
                "ground_truth": event.get("ground_truth"),
                "evidence_turn_indices": event.get("evidence_turn_indices"),
                "release_verified": event.get("release_verified"),
            }
            for event in memory_events
            if isinstance(event, dict)
        ]
        yield {
            "source_dataset": self.name,
            "source_record_id": record_id,
            "events": make_events(record_id, messages, default_session_id=str(raw.get("session_id", "s0"))),
            "source_gold": {"memory_events": gold_events},
            "source_metadata": {
                "session_id": raw.get("session_id"),
                "language": raw.get("language"),
                "source_dataset": raw.get("source_dataset"),
                "source_id": raw.get("source_id"),
                "source_license": raw.get("source_license"),
                "annotator_model": raw.get("annotator_model"),
                "prompt_version": raw.get("prompt_version"),
                "verifier_version": raw.get("verifier_version"),
                "source_file": str(source_path),
            },
        }
