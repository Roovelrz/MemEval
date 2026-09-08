from __future__ import annotations

from memory_eval.adapters.dataset.locomo import LoCoMoDatasetAdapter
from memory_eval.adapters.dataset.longmemeval import LongMemEvalDatasetAdapter
from memory_eval.adapters.dataset.personamem_v2 import PersonaMemV2DatasetAdapter


LEGACY_ADAPTERS = {
    "longmemeval": LongMemEvalDatasetAdapter,
    "locomo": LoCoMoDatasetAdapter,
    "personamem-v2": PersonaMemV2DatasetAdapter,
}


def _event_contents(record):
    return [event["content"] for event in record["events"]]


def _case_contents(case):
    return [message["content"] for session in case["sessions"] for message in session["messages"]]


def test_legacy_equivalence(legacy_source_fixture) -> None:
    legacy = LEGACY_ADAPTERS[legacy_source_fixture.name]().load(legacy_source_fixture.path).cases
    source = list(legacy_source_fixture.adapter.iter_records(legacy_source_fixture.path))

    assert len(source) == len(legacy)
    for record, case in zip(source, legacy, strict=True):
        assert record["source_record_id"] == case["case_id"]
        assert record["source_gold"]["question"] == case["question"]
        assert record["source_gold"]["answer"] == case["gold_answer"]
        assert record["source_gold"]["evidence_session_ids"] == case["evidence_session_ids"]
        assert _event_contents(record) == _case_contents(case)
