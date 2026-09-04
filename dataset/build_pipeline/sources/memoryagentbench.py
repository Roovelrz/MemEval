"""MemoryAgentBench context/query Source Adapter."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable

from .base import CanonicalSourceRecord, SourceAdapter
from .common import flatten_message_objects, iter_parquet_records, make_events


class MemoryAgentBenchSourceAdapter(SourceAdapter):
    name = "memoryagentbench"

    def load_raw(self, path: Path) -> Iterable[dict[str, Any]]:
        yield from iter_parquet_records(path, patterns=("Conflict_Resolution-*.parquet",))

    def normalize(
        self,
        raw: dict[str, Any],
        raw_index: int,
        source_path: Path,
    ) -> Iterable[CanonicalSourceRecord]:
        metadata = raw.get("metadata") if isinstance(raw.get("metadata"), dict) else {}
        qa_pair_ids = metadata.get("qa_pair_ids") if isinstance(metadata.get("qa_pair_ids"), list) else []
        questions = raw.get("questions")
        answers = raw.get("answers")
        if not isinstance(questions, list) or not isinstance(answers, list):
            raise ValueError(f"MemoryAgentBench raw record {raw_index} has invalid questions or answers")
        if len(questions) != len(answers):
            raise ValueError(f"MemoryAgentBench raw record {raw_index} has mismatched questions and answers")
        if qa_pair_ids and len(qa_pair_ids) != len(questions):
            raise ValueError(f"MemoryAgentBench raw record {raw_index} has mismatched qa_pair_ids")
        source_key = str(metadata.get("source") or "conflict_resolution")
        source_row_index = int(raw.get("__source_row_index__", raw_index))
        record_id = f"memoryagentbench:{source_key}:{source_row_index:04d}"
        messages = flatten_message_objects(metadata.get("haystack_sessions"))
        if not messages:
            messages = [{"role": "system", "content": raw.get("context", ""), "source_id": "context"}]
        yield {
            "source_dataset": self.name,
            "source_record_id": record_id,
            "events": make_events(record_id, messages),
            "source_gold": {
                "questions": questions,
                "answers": answers,
                "qa_pair_ids": qa_pair_ids,
                "question_dates": metadata.get("question_dates"),
                "question_types": metadata.get("question_types"),
                "keypoints": metadata.get("keypoints"),
                "previous_events": metadata.get("previous_events"),
            },
            "source_metadata": {
                "source": metadata.get("source"),
                "demo": metadata.get("demo"),
                "source_file": raw.get("__source_file__", str(source_path)),
            },
        }
