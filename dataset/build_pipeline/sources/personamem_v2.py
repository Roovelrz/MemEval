"""Build-side wrapper around the existing PersonaMem-v2 text/32K parser."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable

from memory_eval.adapters.dataset.personamem_v2 import normalize_personamem_case

from .base import CanonicalSourceRecord, SourceAdapter
from .common import from_eval_case, iter_csv_records


class PersonaMemV2SourceAdapter(SourceAdapter):
    name = "personamem-v2"

    def load_raw(self, path: Path) -> Iterable[dict[str, Any]]:
        return iter_csv_records(path)

    def normalize(
        self,
        raw: dict[str, Any],
        raw_index: int,
        source_path: Path,
    ) -> Iterable[CanonicalSourceRecord]:
        case = normalize_personamem_case(raw, raw_index, source_path)
        yield from_eval_case(
            self.name,
            case,
            source_gold={
                "preference": raw.get("preference", ""),
                "related_conversation_snippet": raw.get("related_conversation_snippet", ""),
            },
            source_metadata={"source_file": str(source_path), "source_row_index": raw_index},
        )
