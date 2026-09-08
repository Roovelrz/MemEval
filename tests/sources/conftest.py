from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator

import pyarrow as pa
import pyarrow.parquet as parquet
import pytest

from dataset.build_pipeline.sources import create_source_adapter
from tests.helpers import workspace_directory


@dataclass(frozen=True)
class SourceFixture:
    name: str
    adapter: Any
    path: Path
    raw_count: int
    record_count: int


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")


def _write_parquet(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    parquet.write_table(pa.Table.from_pylist(rows), path)


def _longmemeval_rows() -> list[dict[str, Any]]:
    return [
        {
            "question_id": f"long-{index}",
            "question": f"Where is item {index}?",
            "answer": f"place {index}",
            "question_type": "single-session-user",
            "haystack_session_ids": [f"session-{index}"],
            "haystack_dates": [f"2026-01-0{index + 1}"],
            "haystack_sessions": [[{"role": "user", "content": f"Item {index} is in place {index}."}]],
            "answer_session_ids": [f"session-{index}"],
        }
        for index in range(2)
    ]


def _locomo_rows() -> list[dict[str, Any]]:
    return [
        {
            "sample_id": "sample-1",
            "conversation": {
                "speaker_a": "A",
                "speaker_b": "B",
                "session_1_date_time": "10:00 AM on 01 January, 2025",
                "session_1": [
                    {"speaker": "A", "text": "I like tea and hiking.", "dia_id": "D1:1"},
                    {"speaker": "B", "text": "Noted.", "dia_id": "D1:2"},
                ],
            },
            "qa": [
                {"question": "What does A drink?", "answer": "tea", "category": 1, "evidence": ["D1:1"]},
                {"question": "What activity does A like?", "answer": "hiking", "category": 1, "evidence": ["D1:1"]},
            ],
        }
    ]


def _build_fixture(name: str, root: Path) -> SourceFixture:
    adapter = create_source_adapter(name)
    if name == "longmemeval":
        path = root / "longmemeval.json"
        _write_json(path, _longmemeval_rows())
        return SourceFixture(name, adapter, path, 2, 2)
    if name == "locomo":
        path = root / "locomo.json"
        _write_json(path, _locomo_rows())
        return SourceFixture(name, adapter, path, 1, 2)
    if name == "personamem-v2":
        path = root / "benchmark" / "text" / "benchmark.csv"
        histories = root / "data" / "chat_history_32k"
        histories.mkdir(parents=True)
        rows = []
        for index in range(2):
            content = f"I prefer quiet place {index}."
            _write_json(histories / f"persona{index}.json", {"chat_history": [{"role": "user", "content": content}]})
            rows.append(
                {
                    "persona_id": str(index),
                    "chat_history_32k_link": f"data/chat_history_32k/persona{index}.json",
                    "user_query": json.dumps({"content": "Where should I go?"}),
                    "correct_answer": f"quiet place {index}",
                    "preference": f"quiet place {index}",
                    "related_conversation_snippet": json.dumps([{"role": "user", "content": content}]),
                    "pref_type": "location",
                }
            )
        path.parent.mkdir(parents=True)
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
        return SourceFixture(name, adapter, path, 2, 2)
    if name == "prefeval":
        path = root / "prefeval.parquet"
        _write_parquet(
            path,
            [
                {
                    "preference_type": "explicit_preference",
                    "preference": f"prefers train {index}",
                    "question": f"How should trip {index} be made?",
                    "explanation": "Use the preference.",
                    "aligned_op": "Take a train",
                    "options": ["Take a train", "Fly"],
                    "topic": "travel",
                }
                for index in range(2)
            ],
        )
        return SourceFixture(name, adapter, path, 2, 2)
    if name == "memoryagentbench":
        path = root / "Conflict_Resolution-fixture.parquet"
        _write_parquet(
            path,
            [
                {
                    "context": f"0. Fact {index} is current.",
                    "questions": [f"What is fact {index}?"],
                    "answers": [[f"Fact {index}"]],
                    "metadata": {"source": "fixture", "qa_pair_ids": [f"qa-{index}"]},
                }
                for index in range(2)
            ],
        )
        return SourceFixture(name, adapter, path, 2, 2)
    if name == "beam":
        path = root / "100K-fixture.parquet"
        _write_parquet(
            path,
            [
                {
                    "conversation_id": str(index),
                    "chat": [[{"role": "user", "content": f"Remember beam fact {index}."}]],
                    "probing_questions": str(
                        {"information_extraction": [{"question": f"Which fact {index}?", "ideal_response": f"fact {index}"}]}
                    ),
                    "user_questions": [],
                }
                for index in range(2)
            ],
        )
        return SourceFixture(name, adapter, path, 2, 2)
    if name == "agentmembench":
        path = root / "agentmembench.jsonl"
        rows = [
            {
                "record_id": f"record-{index}",
                "session_id": f"session-{index}",
                "memory_events": [
                    {
                        "turn_idx": index,
                        "event_type": "TASK_REQUEST",
                        "raw_text": f"The user requests task {index}.",
                        "query": f"What task was requested {index}?",
                        "ground_truth": f"task {index}",
                        "evidence_turn_indices": [index],
                        "release_verified": True,
                    }
                ],
            }
            for index in range(2)
        ]
        path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
        return SourceFixture(name, adapter, path, 2, 2)
    raise AssertionError(f"Unhandled Source Adapter fixture: {name}")


SOURCE_NAMES = (
    "longmemeval",
    "locomo",
    "prefeval",
    "personamem-v2",
    "memoryagentbench",
    "beam",
    "agentmembench",
)


@pytest.fixture(scope="module", params=SOURCE_NAMES)
def source_fixture(request: pytest.FixtureRequest) -> Iterator[SourceFixture]:
    name = str(request.param)
    with workspace_directory(f"source-contract-{name}") as root:
        yield _build_fixture(name, root)


@pytest.fixture(scope="module", params=("longmemeval", "locomo", "personamem-v2"))
def legacy_source_fixture(request: pytest.FixtureRequest) -> Iterator[SourceFixture]:
    name = str(request.param)
    with workspace_directory(f"source-legacy-{name}") as root:
        yield _build_fixture(name, root)
