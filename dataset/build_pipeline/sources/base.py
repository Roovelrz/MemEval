"""Source Adapter contract and canonical source-record validation."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Iterator, TypedDict


class CanonicalEvent(TypedDict):
    """One source event before any benchmark-dimension logic is applied."""

    event_id: str
    session_id: str
    sequence: int
    role: str
    content: str
    timestamp: str
    source_id: str
    metadata: dict[str, Any]


class CanonicalSourceRecord(TypedDict):
    """Traceable source material consumed by a Dimension Builder."""

    source_dataset: str
    source_record_id: str
    events: list[CanonicalEvent]
    source_gold: dict[str, Any]
    source_metadata: dict[str, Any]


@dataclass
class SourceAudit:
    """Result of a full or limited Source Adapter audit."""

    adapter_name: str
    raw_record_count: int = 0
    canonical_record_count: int = 0
    event_count: int = 0
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


class SourceAdapter(ABC):
    """Read one upstream dataset and emit dimension-neutral records."""

    name: str

    @abstractmethod
    def load_raw(self, path: Path) -> Iterable[dict[str, Any]]:
        """Yield raw records from a source file or directory."""

    @abstractmethod
    def normalize(
        self,
        raw: dict[str, Any],
        raw_index: int,
        source_path: Path,
    ) -> Iterable[CanonicalSourceRecord]:
        """Map one raw record to one or more canonical source records."""

    def validate(self, record: CanonicalSourceRecord) -> CanonicalSourceRecord:
        """Validate only source-level invariants, never dimension policy."""

        source_dataset = str(record.get("source_dataset", "")).strip()
        source_record_id = str(record.get("source_record_id", "")).strip()
        if not source_dataset:
            raise ValueError("source_dataset must not be empty")
        if not source_record_id:
            raise ValueError("source_record_id must not be empty")
        if source_dataset != self.name:
            raise ValueError(
                f"Record {source_record_id!r} belongs to {source_dataset!r}, expected {self.name!r}"
            )

        events = record.get("events")
        if not isinstance(events, list):
            raise ValueError(f"Record {source_record_id!r} events must be a list")
        if not events:
            raise ValueError(f"Record {source_record_id!r} must contain at least one event")
        seen_event_ids: set[str] = set()
        for expected_sequence, event in enumerate(events):
            event_id = str(event.get("event_id", "")).strip()
            if not event_id:
                raise ValueError(f"Record {source_record_id!r} contains an event without event_id")
            if event_id in seen_event_ids:
                raise ValueError(f"Record {source_record_id!r} repeats event_id {event_id!r}")
            seen_event_ids.add(event_id)
            if event.get("sequence") != expected_sequence:
                raise ValueError(
                    f"Record {source_record_id!r} event {event_id!r} has a non-contiguous sequence"
                )
            if not str(event.get("role", "")).strip():
                raise ValueError(f"Record {source_record_id!r} event {event_id!r} has no role")
            if not str(event.get("content", "")).strip():
                raise ValueError(f"Record {source_record_id!r} event {event_id!r} has empty content")
            if not isinstance(event.get("metadata"), dict):
                raise ValueError(f"Record {source_record_id!r} event {event_id!r} metadata must be an object")

        if not isinstance(record.get("source_gold"), dict):
            raise ValueError(f"Record {source_record_id!r} source_gold must be an object")
        if not isinstance(record.get("source_metadata"), dict):
            raise ValueError(f"Record {source_record_id!r} source_metadata must be an object")
        return record

    def iter_records(self, path: Path) -> Iterator[CanonicalSourceRecord]:
        """Stream validated canonical records in deterministic source order."""

        source_path = Path(path)
        for raw_index, raw in enumerate(self.load_raw(source_path)):
            if not isinstance(raw, dict):
                raise ValueError(f"Raw record {raw_index} from {source_path} is not an object")
            for record in self.normalize(raw, raw_index, source_path):
                yield self.validate(record)

    def audit(self, path: Path, *, limit: int = 0) -> SourceAudit:
        """Normalize and validate records, optionally stopping after ``limit`` outputs."""

        if limit < 0:
            raise ValueError("limit must be non-negative")
        result = SourceAudit(adapter_name=self.name)
        seen_record_ids: set[str] = set()
        try:
            for raw_index, raw in enumerate(self.load_raw(Path(path))):
                result.raw_record_count += 1
                if not isinstance(raw, dict):
                    raise ValueError(f"Raw record {raw_index} from {path} is not an object")
                for unvalidated in self.normalize(raw, raw_index, Path(path)):
                    record = self.validate(unvalidated)
                    result.canonical_record_count += 1
                    result.event_count += len(record["events"])
                    record_id = record["source_record_id"]
                    if record_id in seen_record_ids:
                        result.errors.append(f"duplicate source_record_id: {record_id}")
                    seen_record_ids.add(record_id)
                    if limit and result.canonical_record_count >= limit:
                        return result
        except (OSError, RuntimeError, ValueError, TypeError, KeyError) as exc:
            result.errors.append(str(exc))
        return result
