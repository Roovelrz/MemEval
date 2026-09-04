"""Build-side wrapper around the existing LongMemEval parser."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable

from memory_eval.adapters.dataset.longmemeval import normalize_case

from .base import CanonicalSourceRecord, SourceAdapter
from .common import from_eval_case, iter_json_records


class LongMemEvalSourceAdapter(SourceAdapter):
    name = "longmemeval"

    def load_raw(self, path: Path) -> Iterable[dict[str, Any]]:
        return iter_json_records(path)

    def normalize(
        self,
        raw: dict[str, Any],
        raw_index: int,
        source_path: Path,
    ) -> Iterable[CanonicalSourceRecord]:
        case = normalize_case(raw, raw_index)
        yield from_eval_case(
            self.name,
            case,
            source_metadata={
                "source_file": str(source_path),
                "source_question_id": raw.get("question_id", raw.get("id")),
            },
        )
