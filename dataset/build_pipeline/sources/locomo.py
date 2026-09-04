"""Build-side wrapper around the existing LoCoMo parser."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable

from memory_eval.adapters.dataset.locomo import normalize_locomo_case

from .base import CanonicalSourceRecord, SourceAdapter
from .common import from_eval_case, iter_json_records


class LoCoMoSourceAdapter(SourceAdapter):
    name = "locomo"

    def load_raw(self, path: Path) -> Iterable[dict[str, Any]]:
        return iter_json_records(path)

    def normalize(
        self,
        raw: dict[str, Any],
        raw_index: int,
        source_path: Path,
    ) -> Iterable[CanonicalSourceRecord]:
        qa_rows = raw.get("qa")
        if not isinstance(qa_rows, list):
            raise ValueError(f"LoCoMo raw record {raw_index} has no qa list")
        for qa_index in range(len(qa_rows)):
            case = normalize_locomo_case(raw, qa_index)
            yield from_eval_case(
                self.name,
                case,
                source_metadata={"source_file": str(source_path), "source_sample_index": raw_index},
            )
