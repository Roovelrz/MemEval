"""Write traceable Source Adapter output using the stage-20 layout."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .sources.base import CanonicalSourceRecord


@dataclass(frozen=True)
class StagingWriteResult:
    output_dir: Path
    records_path: Path
    record_count: int
    context_count: int


def write_staging_records(
    records: Iterable[CanonicalSourceRecord],
    output_dir: Path,
) -> StagingWriteResult:
    """Write ``records.jsonl`` plus one canonical context per source record."""

    root = Path(output_dir)
    if root.exists() and any(root.iterdir()):
        raise FileExistsError(f"Refusing to mix staging output into a non-empty directory: {root}")
    contexts_dir = root / "contexts"
    contexts_dir.mkdir(parents=True, exist_ok=True)
    records_path = root / "records.jsonl"
    record_count = 0
    context_count = 0
    seen_ids: set[str] = set()
    with records_path.open("w", encoding="utf-8", newline="\n") as records_handle:
        for record in records:
            record_id = record["source_record_id"]
            if record_id in seen_ids:
                raise ValueError(f"Duplicate source_record_id while writing staging data: {record_id}")
            seen_ids.add(record_id)
            context_name = hashlib.sha256(record_id.encode("utf-8")).hexdigest()[:16] + ".json"
            context_ref = f"contexts/{context_name}"
            context_payload = {
                "source_dataset": record["source_dataset"],
                "source_record_id": record_id,
                "events": record["events"],
            }
            (contexts_dir / context_name).write_text(
                json.dumps(context_payload, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            staging_record = {
                "source_dataset": record["source_dataset"],
                "source_record_id": record_id,
                "context_ref": context_ref,
                "source_gold": record["source_gold"],
                "source_metadata": record["source_metadata"],
            }
            records_handle.write(json.dumps(staging_record, ensure_ascii=False) + "\n")
            record_count += 1
            context_count += 1
    return StagingWriteResult(
        output_dir=root,
        records_path=records_path,
        record_count=record_count,
        context_count=context_count,
    )
