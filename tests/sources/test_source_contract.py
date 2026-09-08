from __future__ import annotations

from copy import deepcopy

import pytest


REQUIRED_RECORD_FIELDS = {
    "source_dataset",
    "source_record_id",
    "events",
    "source_gold",
    "source_metadata",
}
REQUIRED_EVENT_FIELDS = {
    "event_id",
    "session_id",
    "order",
    "role",
    "content",
    "timestamp",
    "source_id",
    "metadata",
}


def _records(source_fixture):
    return list(source_fixture.adapter.iter_records(source_fixture.path))


def test_load_raw(source_fixture) -> None:
    rows = list(source_fixture.adapter.load_raw(source_fixture.path))
    assert len(rows) == source_fixture.raw_count
    assert all(isinstance(row, dict) for row in rows)


def test_record_count(source_fixture) -> None:
    report = source_fixture.adapter.audit(source_fixture.path)
    assert report.ok, report.errors
    assert report.raw_record_count == source_fixture.raw_count
    assert report.canonical_record_count == source_fixture.record_count


def test_required_fields(source_fixture) -> None:
    record = _records(source_fixture)[0]
    assert REQUIRED_RECORD_FIELDS <= record.keys()
    assert all(REQUIRED_EVENT_FIELDS <= event.keys() for event in record["events"])

    invalid = deepcopy(record)
    invalid.pop("source_record_id")
    with pytest.raises(ValueError, match="source_record_id"):
        source_fixture.adapter.validate(invalid)


def test_unique_ids(source_fixture) -> None:
    records = _records(source_fixture)
    record_ids = [record["source_record_id"] for record in records]
    event_ids = [event["event_id"] for record in records for event in record["events"]]
    assert len(record_ids) == len(set(record_ids))
    assert len(event_ids) == len(set(event_ids))


def test_normalize(source_fixture) -> None:
    raw = next(iter(source_fixture.adapter.load_raw(source_fixture.path)))
    normalized = list(source_fixture.adapter.normalize(raw, 0, source_fixture.path))
    assert normalized
    assert all(source_fixture.adapter.validate(record) is record for record in normalized)


def test_source_traceability(source_fixture) -> None:
    for record in _records(source_fixture):
        assert record["source_dataset"] == source_fixture.name
        assert record["source_metadata"]["source_file"]
        assert all(str(event["source_id"]) for event in record["events"])


def test_context_reference(source_fixture) -> None:
    for record in _records(source_fixture):
        assert [event["order"] for event in record["events"]] == list(range(len(record["events"])))
        assert all(str(event["session_id"]) for event in record["events"])


def test_gold_reference(source_fixture) -> None:
    for record in _records(source_fixture):
        gold = record["source_gold"]
        session_ids = {event["session_id"] for event in record["events"]}
        if "evidence_session_ids" in gold:
            assert set(gold["evidence_session_ids"]) <= session_ids
        elif source_fixture.name == "prefeval":
            assert gold["preference"] and gold["question"]
        elif source_fixture.name == "memoryagentbench":
            assert len(gold["questions"]) == len(gold["answers"]) == len(gold["qa_pair_ids"])
        elif source_fixture.name == "beam":
            assert gold["probing_questions"]
        else:
            turns = {event["metadata"].get("turn_idx") for event in record["events"]}
            expected = {
                value
                for event in gold["memory_events"]
                for value in event["evidence_turn_indices"]
            }
            assert expected <= turns


def test_deterministic_output(source_fixture) -> None:
    first = _records(source_fixture)
    second = _records(source_fixture)
    assert second == first
