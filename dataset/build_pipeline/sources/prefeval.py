"""PrefEval explicit, implicit-choice, and implicit-persona Source Adapter."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable

from .base import CanonicalSourceRecord, SourceAdapter
from .common import iter_parquet_records, make_events


PREFEVAL_PARTS = ("explicit", "implicit_choice", "implicit_persona")


class PrefEvalSourceAdapter(SourceAdapter):
    name = "prefeval"

    def load_raw(self, path: Path) -> Iterable[dict[str, Any]]:
        if path.is_file():
            yield from iter_parquet_records(path)
            return
        files = [
            path / part / "data" / "train-00000-of-00001.parquet"
            for part in PREFEVAL_PARTS
            if (path / part / "data" / "train-00000-of-00001.parquet").is_file()
        ]
        if not files:
            raise FileNotFoundError(f"No allow-listed PrefEval files found under: {path}")
        for file in files:
            yield from iter_parquet_records(file)

    def normalize(
        self,
        raw: dict[str, Any],
        raw_index: int,
        source_path: Path,
    ) -> Iterable[CanonicalSourceRecord]:
        preference_type = str(raw.get("preference_type", "unknown"))
        if preference_type not in {"explicit_preference", "implicit_choice", "implicit_persona"}:
            raise ValueError(f"Unsupported PrefEval preference_type: {preference_type!r}")
        if not str(raw.get("preference", "")).strip():
            raise ValueError(f"PrefEval raw record {raw_index} has an empty preference")
        if not str(raw.get("question", "")).strip():
            raise ValueError(f"PrefEval raw record {raw_index} has an empty question")
        source_row_index = int(raw.get("__source_row_index__", raw_index))
        record_id = f"prefeval:{preference_type}:{source_row_index:05d}"
        messages: list[dict[str, Any]] = []
        conversation = raw.get("conversation")
        if isinstance(conversation, dict):
            for key in sorted(conversation, key=lambda value: int(value) if str(value).isdigit() else str(value)):
                turn = conversation[key]
                if isinstance(turn, dict):
                    messages.extend(
                        [
                            {"role": "user", "content": turn.get("user", ""), "source_id": f"{key}:user"},
                            {
                                "role": "assistant",
                                "content": turn.get("assistant", ""),
                                "source_id": f"{key}:assistant",
                            },
                        ]
                    )
        elif preference_type == "implicit_choice":
            messages = [
                {"role": "user", "content": raw.get("conversation_query", ""), "source_id": "query"},
                {
                    "role": "assistant",
                    "content": raw.get("conversation_assistant_options", ""),
                    "source_id": "options",
                },
                {
                    "role": "user",
                    "content": raw.get("conversation_user_selection", ""),
                    "source_id": "selection",
                },
                {
                    "role": "assistant",
                    "content": raw.get("conversation_assistant_acknowledgment", ""),
                    "source_id": "acknowledgment",
                },
            ]
        else:
            messages = [
                {
                    "role": "user",
                    "content": raw.get("preference", ""),
                    "source_id": "explicit_preference",
                }
            ]

        yield {
            "source_dataset": self.name,
            "source_record_id": record_id,
            "events": make_events(record_id, messages),
            "source_gold": {
                "preference": raw.get("preference", ""),
                "question": raw.get("question", ""),
                "explanation": raw.get("explanation", ""),
                "aligned_option": raw.get("aligned_op"),
                "options": raw.get("options"),
            },
            "source_metadata": {
                "topic": raw.get("topic"),
                "preference_type": preference_type,
                "persona": raw.get("persona"),
                "source_row_index": source_row_index,
                "source_file": raw.get("__source_file__", str(source_path)),
            },
        }
