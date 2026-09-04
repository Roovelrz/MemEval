"""BEAM regular-scale and 10M Source Adapter."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable

from .base import CanonicalSourceRecord, SourceAdapter
from .common import flatten_message_objects, iter_parquet_records, make_events, parse_literal_mapping


class BeamSourceAdapter(SourceAdapter):
    name = "beam"

    def load_raw(self, path: Path) -> Iterable[dict[str, Any]]:
        yield from iter_parquet_records(
            path,
            patterns=("100K-*.parquet", "500K-*.parquet", "1M-*.parquet", "10M-*.parquet"),
        )

    def normalize(
        self,
        raw: dict[str, Any],
        raw_index: int,
        source_path: Path,
    ) -> Iterable[CanonicalSourceRecord]:
        source_file = Path(str(raw.get("__source_file__", source_path)))
        scale = source_file.name.split("-", 1)[0]
        conversation_id = str(raw.get("conversation_id", raw_index))
        source_row_index = int(raw.get("__source_row_index__", raw_index))
        record_id = f"beam:{scale}:{source_file.stem}:{source_row_index:04d}"
        messages = flatten_message_objects(raw.get("chat"))
        if not messages:
            messages = flatten_message_objects(raw.get("plans"))
        probing_questions = parse_literal_mapping(raw.get("probing_questions"))
        if "raw" in probing_questions:
            raise ValueError(f"BEAM record {record_id!r} has unparseable probing_questions")
        yield {
            "source_dataset": self.name,
            "source_record_id": record_id,
            "events": make_events(record_id, messages),
            "source_gold": {
                "probing_questions": probing_questions,
                "user_questions": raw.get("user_questions", []),
            },
            "source_metadata": {
                "scale": scale,
                "conversation_id": conversation_id,
                "conversation_seed": raw.get("conversation_seed"),
                "user_profile": raw.get("user_profile"),
                "source_file": str(source_file),
            },
        }
