from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from dataset.build_pipeline import ReviewedBenchmark, export_benchmark_layout
from dataset.build_pipeline.dimensions.base import DimensionBuilder
from dataset.build_pipeline.dimensions import DIMENSION_BUILDERS, create_dimension_builder
from dataset.build_pipeline.dimensions.d01_write import D01WriteBuilder
from dataset.build_pipeline.dimensions.d02_retrieval import D02RetrievalBuilder
from dataset.build_pipeline.dimensions.d03_temporal import D03TemporalBuilder
from dataset.build_pipeline.dimensions.d04_activation import D04ActivationBuilder
from dataset.build_pipeline.dimensions.d05_profile import D05ProfileBuilder
from dataset.build_pipeline.dimensions.d06_conflict import D06ConflictBuilder
from dataset.build_pipeline.dimensions.d07_scale import D07ScaleBuilder
from dataset.build_pipeline.dimensions.d08_privacy import D08PrivacyBuilder
from dataset.build_pipeline.staging import write_staging_records
from dataset.build_pipeline.sources.agentmembench import AgentMemBenchSourceAdapter
from dataset.build_pipeline.sources.beam import BeamSourceAdapter
from dataset.build_pipeline.sources.locomo import LoCoMoSourceAdapter
from dataset.build_pipeline.sources.longmemeval import LongMemEvalSourceAdapter
from dataset.build_pipeline.sources.memoryagentbench import MemoryAgentBenchSourceAdapter
from dataset.build_pipeline.sources.personamem_v2 import PersonaMemV2SourceAdapter
from dataset.build_pipeline.sources.prefeval import PrefEvalSourceAdapter
from dataset.build_pipeline.sources.registry import SOURCE_ADAPTERS, create_source_adapter
from dataset.build_pipeline.release import DIMENSION_DIRECTORIES, EXPORT_DIRECTORIES
from tests.helpers import workspace_directory


def test_source_registry_exposes_all_stage_17_adapters() -> None:
    assert set(SOURCE_ADAPTERS) == {
        "agentmembench",
        "beam",
        "locomo",
        "longmemeval",
        "memoryagentbench",
        "personamem-v2",
        "prefeval",
    }
    assert create_source_adapter("personamem_v2").name == "personamem-v2"


def test_longmemeval_wrapper_emits_traceable_events() -> None:
    raw = {
        "question_id": "q1",
        "question": "Where does the user live?",
        "answer": "Shanghai",
        "haystack_session_ids": ["s1"],
        "haystack_dates": ["2026-01-01"],
        "haystack_sessions": [[{"role": "user", "content": "I live in Shanghai."}]],
        "answer_session_ids": ["s1"],
    }
    adapter = LongMemEvalSourceAdapter()
    record = adapter.validate(next(adapter.normalize(raw, 0, Path("longmemeval.jsonl"))))
    adapter.load_raw = lambda path: iter([raw])  # type: ignore[method-assign]
    report = adapter.audit(Path("longmemeval.jsonl"))

    assert record["source_record_id"] == "q1"
    assert record["events"][0]["session_id"] == "s1"
    assert record["source_gold"]["evidence_session_ids"] == ["s1"]
    assert report.ok
    assert (report.raw_record_count, report.canonical_record_count, report.event_count) == (1, 1, 1)


def test_locomo_wrapper_preserves_session_timestamp_and_evidence() -> None:
    raw = {
        "sample_id": "sample-1",
        "conversation": {
            "speaker_a": "A",
            "speaker_b": "B",
            "session_1_date_time": "10:00 AM on 01 January, 2025",
            "session_1": [
                {"speaker": "A", "text": "I like tea.", "dia_id": "D1:1"},
                {"speaker": "B", "text": "Noted.", "dia_id": "D1:2"},
            ],
        },
        "qa": [
            {
                "question": "What does A like?",
                "answer": "tea",
                "category": 1,
                "evidence": ["D1:1"],
            }
        ],
    }

    record = next(LoCoMoSourceAdapter().normalize(raw, 0, Path("locomo.json")))

    assert record["events"][0]["timestamp"].startswith("2025-01-01T10:00:00")
    assert record["events"][0]["metadata"]["has_answer"] is True
    assert record["source_gold"]["answer"] == "tea"


def test_personamem_wrapper_reuses_32k_history_index() -> None:
    csv_path = Path("benchmark/text/benchmark.csv")
    history = [
        {"role": "user", "content": "I prefer quiet cafés."},
        {"role": "assistant", "content": "I will remember that."},
    ]
    raw = {
        "persona_id": "0",
        "chat_history_32k_link": "data/chat_history_32k/persona0.json",
        "user_query": '{"content": "Where should I go?"}',
        "correct_answer": "A quiet café",
        "preference": "quiet cafés",
        "related_conversation_snippet": '[{"role": "user", "content": "I prefer quiet cafés."}]',
    }
    with patch("memory_eval.adapters.dataset.personamem_v2._load_history", return_value=history):
        record = next(PersonaMemV2SourceAdapter().normalize(raw, 0, csv_path))

    assert len(record["events"]) == 2
    assert record["source_gold"]["preference"] == "quiet cafés"
    assert record["events"][0]["metadata"]["has_answer"] is True


def test_prefeval_normalizes_without_dimension_policy() -> None:
    raw = {
        "preference_type": "implicit_choice",
        "preference": "prefers trains",
        "question": "How should I travel?",
        "explanation": "Use the stored preference.",
        "aligned_op": "Take a train",
        "options": ["Take a train", "Fly"],
        "conversation_query": "Train or plane?",
        "conversation_assistant_options": "1. Train 2. Plane",
        "conversation_user_selection": "Train",
        "conversation_assistant_acknowledgment": "Understood",
        "topic": "travel",
    }

    record = next(PrefEvalSourceAdapter().normalize(raw, 3, Path("prefeval")))

    assert len(record["events"]) == 4
    assert record["source_gold"]["aligned_option"] == "Take a train"
    assert "should_activate" not in record["source_gold"]


def test_memoryagentbench_keeps_one_context_with_multiple_questions() -> None:
    raw = {
        "context": "0. A is B.",
        "questions": ["Q1?", "Q2?"],
        "answers": [["A1"], ["A2"]],
        "metadata": {"source": "conflict", "qa_pair_ids": ["q1", "q2"]},
    }

    record = next(MemoryAgentBenchSourceAdapter().normalize(raw, 0, Path("source.parquet")))

    assert len(record["events"]) == 1
    assert record["source_gold"]["qa_pair_ids"] == ["q1", "q2"]
    assert len(record["source_gold"]["questions"]) == 2


def test_beam_flattens_nested_chat_and_preserves_scale_gold() -> None:
    raw = {
        "conversation_id": "7",
        "chat": [[{"role": "user", "content": "hello"}, {"role": "assistant", "content": "hi"}]],
        "probing_questions": "{'abstention': [{'question': 'unknown?', 'ideal_response': 'not provided'}]}",
        "user_questions": [],
    }

    record = next(
        BeamSourceAdapter().normalize(raw, 0, Path("100K-00000-of-00001.parquet"))
    )

    assert [event["role"] for event in record["events"]] == ["user", "assistant"]
    assert record["source_metadata"]["scale"] == "100K"
    assert "abstention" in record["source_gold"]["probing_questions"]


def test_agentmembench_preserves_source_event_gold() -> None:
    raw = {
        "record_id": "record-1",
        "session_id": "session-1",
        "memory_events": [
            {
                "turn_idx": 2,
                "event_type": "TASK_REQUEST",
                "raw_text": "The user requests a Persian cat prompt.",
                "query": "What did the user request?",
                "ground_truth": "A Persian cat prompt",
                "evidence_turn_indices": [2],
                "release_verified": True,
            }
        ],
    }

    record = next(AgentMemBenchSourceAdapter().normalize(raw, 0, Path("source.jsonl")))

    assert record["events"][0]["session_id"] == "session-1"
    assert record["source_gold"]["memory_events"][0]["release_verified"] is True


class _ExampleDimensionBuilder(DimensionBuilder):
    dimension_id = "d99_example"

    def derive_gold(self, candidate: dict) -> dict:
        return {
            **candidate,
            "case_id": "case-1",
            "dimension_id": self.dimension_id,
            "query": candidate["source_gold"]["question"],
            "gold_payload": {"answer": candidate["source_gold"]["answer"]},
        }


def test_dimension_builder_runs_the_six_step_contract() -> None:
    record = {
        "source_dataset": "fixture",
        "source_record_id": "source-1",
        "events": [],
        "source_gold": {"question": "Q?", "answer": "A"},
        "source_metadata": {},
    }

    result = _ExampleDimensionBuilder().build([record])

    assert result.loaded_candidate_count == 1
    assert result.filtered_candidate_count == 1
    assert result.cases[0]["gold_payload"] == {"answer": "A"}


def _event(
    record_id: str,
    index: int = 0,
    *,
    content: str = "The user likes tea.",
    has_answer: bool = True,
    source_id: str | int | None = None,
    timestamp: str = "2025-01-01T00:00:00+00:00",
) -> dict:
    return {
        "event_id": f"{record_id}:event:{index:06d}",
        "session_id": "s1",
        "sequence": index,
        "role": "user",
        "content": content,
        "timestamp": timestamp,
        "source_id": str(index if source_id is None else source_id),
        "metadata": {"has_answer": has_answer, "id": source_id},
    }


def _record(
    source_dataset: str,
    record_id: str,
    *,
    source_gold: dict,
    source_metadata: dict | None = None,
    events: list[dict] | None = None,
) -> dict:
    return {
        "source_dataset": source_dataset,
        "source_record_id": record_id,
        "events": events or [_event(record_id)],
        "source_gold": source_gold,
        "source_metadata": source_metadata or {},
    }


def test_stage_21_registry_contains_all_dimensions() -> None:
    assert set(DIMENSION_BUILDERS) == {"d01", "d02", "d03", "d04", "d05", "d06", "d07", "d08"}
    assert create_dimension_builder("D04").dimension_id == "D04"


def test_d01_and_d02_apply_different_gold_to_same_longmemeval_source() -> None:
    record = _record(
        "longmemeval",
        "lme-1",
        source_gold={
            "question": "What does the user like?",
            "answer": "tea",
            "evidence_session_ids": ["s1"],
        },
    )

    write_case = D01WriteBuilder(target_count=0).build([record]).cases[0]
    retrieval_case = D02RetrievalBuilder(target_count=0).build([record]).cases[0]

    assert write_case["payload_type"] == "write"
    assert write_case["metadata"]["annotation_status"] == "semantic_review_required"
    assert retrieval_case["payload_type"] == "retrieval"
    assert retrieval_case["gold_payload"]["gold_evidence_ids"] == ["lme-1:event:000000"]


def test_d03_derives_temporal_payload() -> None:
    record = _record(
        "locomo",
        "locomo:sample:0000",
        source_gold={"question": "When?", "answer": "January", "evidence_session_ids": ["s1"]},
        source_metadata={"question_date": "2025-02-01T00:00:00+00:00"},
    )

    case = D03TemporalBuilder(target_count=0).build([record]).cases[0]

    assert case["gold_payload"]["time_gap_days"] == 31
    assert case["gold_payload"]["lifecycle"]["expected_active"] is True


def test_d04_builds_one_balanced_activation_pair() -> None:
    common_gold = {
        "preference": "prefers trains",
        "question": "How should I travel?",
        "explanation": "Respect the preference.",
    }
    records = [
        _record(
            "prefeval",
            "prefeval:explicit_preference:00007",
            source_gold=common_gold,
            source_metadata={"preference_type": "explicit_preference", "source_row_index": 7},
        ),
        _record(
            "prefeval",
            "prefeval:implicit_choice:00007",
            source_gold={**common_gold, "aligned_option": "Take a train"},
            source_metadata={"preference_type": "implicit_choice", "source_row_index": 7},
        ),
    ]

    cases = D04ActivationBuilder(target_count=2).build(records).cases

    assert len(cases) == 2
    assert {case["gold_payload"]["should_activate"] for case in cases} == {False, True}


def test_d05_emits_reviewable_profile_item() -> None:
    record = _record(
        "personamem-v2",
        "personamem-v2:7:00001",
        source_gold={"question": "Where should I eat?", "answer": "A quiet café", "preference": "quiet cafés"},
    )

    case = D05ProfileBuilder(target_count=0).build([record]).cases[0]

    assert case["gold_payload"]["profile_items"][0]["value"] == "quiet cafés"
    assert case["metadata"]["annotation_status"] == "semantic_review_required"


def test_d06_expands_one_context_into_multiple_questions() -> None:
    record = _record(
        "memoryagentbench",
        "memoryagentbench:conflict:0000",
        source_gold={
            "questions": ["Q1?", "Q2?"],
            "answers": [["A1"], ["A2"]],
            "qa_pair_ids": ["fact_sh_1", "fact_mh_2"],
            "previous_events": None,
        },
        source_metadata={"source": "factconsolidation_mh_6k"},
    )

    result = D06ConflictBuilder(target_count=0).build([record])

    assert len(result.cases) == 2
    assert {case["gold_payload"]["gold_answer"] for case in result.cases} == {"A1", "A2"}
    assert all(case["metadata"]["annotation_status"] == "semantic_review_required" for case in result.cases)


def test_d07_expands_probe_and_resolves_evidence() -> None:
    record = _record(
        "beam",
        "beam:100K:row0",
        source_gold={
            "probing_questions": {
                "contradiction_resolution": [
                    {
                        "question": "Did I revise the design?",
                        "ideal_answer": "Yes.",
                        "source_chat_ids": [7],
                    }
                ]
            }
        },
        source_metadata={"scale": "100K"},
        events=[_event("beam:100K:row0", source_id=7)],
    )

    case = D07ScaleBuilder(target_count=0).build([record]).cases[0]

    assert case["gold_payload"]["target_tokens"] == 100_000
    assert case["gold_payload"]["expected_retrievable"] is True


def test_d08_constructs_all_three_privacy_scenarios() -> None:
    records = [
        _record(
            "agentmembench",
            f"agent-{index}",
            source_gold={
                "memory_events": [
                    {"query": f"What was request {index}?", "ground_truth": f"request {index}"}
                ]
            },
        )
        for index in range(4)
    ]

    cases = D08PrivacyBuilder(scenario_counts=(1, 1, 1), seed="fixture").build(records).cases

    assert {case["gold_payload"]["scenario_type"] for case in cases} == {
        "cross_user_isolation",
        "deletion",
        "forbidden_canary_exposure",
    }
    for case in cases:
        assert case["gold_payload"]["owner_user_id"] != case["gold_payload"]["querying_user_id"]
    canary_case = next(
        case for case in cases if case["gold_payload"]["scenario_type"] == "forbidden_canary_exposure"
    )
    token = canary_case["gold_payload"]["canary_tokens"][0]
    assert sum(token in event["content"] for event in canary_case["events"]) == 1


def test_stage_20_writer_separates_records_and_contexts() -> None:
    record = _record(
        "longmemeval",
        "source-1",
        source_gold={"question": "Q?", "answer": "A"},
    )
    with workspace_directory("stage-20-writer") as directory:
        output = directory / "d02_retrieval"
        result = write_staging_records([record], output)

        lines = result.records_path.read_text(encoding="utf-8").splitlines()
        staging_record = json.loads(lines[0])
        context_path = output / staging_record["context_ref"]
        context = json.loads(context_path.read_text(encoding="utf-8"))

        assert result.record_count == result.context_count == 1
        assert "events" not in staging_record
        assert context["events"][0]["event_id"] == "source-1:event:000000"


def test_frozen_v01_preserves_every_completed_human_review() -> None:
    summary = ReviewedBenchmark("dataset/MemEval-v0.1").assert_review_complete()

    assert summary["D01"]["approved"] == 37
    assert summary["D04"]["approved"] == 38
    assert summary["D05"]["approved_after_repair"] == 37
    assert summary["D06"]["approved"] == 33
    assert summary["D06"]["approved_after_replacement"] == 4
    assert summary["D07"]["approved"] == 37


def test_stage_22_export_uses_reviewed_cases_without_changing_source() -> None:
    manifest_statuses = {
        "D01": "complete",
        "D04": "complete",
        "D05": "complete_after_repair",
        "D06": "complete_after_replacement",
        "D07": "complete_after_repair",
    }
    case_statuses = {
        "D01": "approved",
        "D04": "approved",
        "D05": "approved_after_repair",
        "D06": "approved_after_replacement",
        "D07": "approved",
    }
    with workspace_directory("stage-22-export") as directory:
        source = directory / "source"
        for dimension_id, dimension_name in DIMENSION_DIRECTORIES.items():
            version_dir = source / "dimensions" / dimension_name / "v0.1"
            (version_dir / "cases").mkdir(parents=True)
            (version_dir / "contexts").mkdir()
            metadata = {}
            case = {
                "envelope": {
                    "case_id": f"{dimension_id}:fixture",
                    "context": {"context_ref": "contexts/fixture.json"},
                    "metadata": metadata,
                }
            }
            if dimension_id == "D01":
                case["annotation"] = {"human_review_status": case_statuses[dimension_id]}
            elif dimension_id in case_statuses:
                metadata["human_review"] = {"status": case_statuses[dimension_id]}
            (version_dir / "cases" / "fixture.json").write_text(
                json.dumps(case), encoding="utf-8"
            )
            (version_dir / "contexts" / "fixture.json").write_text("{}", encoding="utf-8")
            human_review = {"required": False}
            if dimension_id in manifest_statuses:
                human_review = {
                    "status": manifest_statuses[dimension_id],
                    "approved_cases": 1,
                }
            (version_dir / "manifest.json").write_text(
                json.dumps({"counts": {"cases": 1}, "human_review": human_review}),
                encoding="utf-8",
            )

        exported = export_benchmark_layout(source, directory / "export")

        assert (exported / "manifest.yaml").is_file()
        for export_name in EXPORT_DIRECTORIES.values():
            assert (exported / export_name / "cases.jsonl").is_file()
            assert (exported / export_name / "contexts" / "fixture.json").is_file()
        assert (source / "dimensions" / DIMENSION_DIRECTORIES["D01"] / "v0.1" / "cases" / "fixture.json").is_file()
