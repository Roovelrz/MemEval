import json

import pytest

from dataset.build_pipeline import ReviewedBenchmark
from memory_eval.runners import ContextCache, MemEvalRunConfig, MemEvalRunner
from tests.helpers import workspace_directory
from tests.test_memeval_runner import FakeSystem, artifact


def test_context_batch_ingests_once_and_records_cache_hits_separately():
    with workspace_directory("context-batch") as directory:
        event = {"event_id": "e1", "session_id": "s1", "content": "needle", "metadata": {}}
        first = artifact(directory, "D02", "q1", [event], {"gold_evidence_ids": ["s1"]})
        second = artifact(directory, "D02", "q2", [event], {"gold_evidence_ids": ["s1"]})
        second = type(second)(second.dimension_id, second.case_path, first.context_path, second.case)
        for item in (first, second):
            item.case["envelope"]["identity"]["context_id"] = "shared-context"

        batch_system = FakeSystem()
        batch_output = directory / "batch" / "results.jsonl"
        batch = MemEvalRunner(batch_system, directory / "batch-work").run(
            [first, second], MemEvalRunConfig("batch", top_k=3, reuse_context=True), batch_output
        )
        assert batch_system.created == 1
        assert batch_system.ingested == 1
        assert batch_system.searched == 2
        assert batch_system.cleaned == 1
        assert [row["run_mode"] for row in batch] == ["context_batch", "context_batch"]
        assert [row["context_cache"]["hit"] for row in batch] == [False, True]
        assert batch[0]["latency"]["ingest"] == 1.5
        assert batch[1]["latency"]["ingest"] is None
        summary = json.loads((batch_output.parent / "run_summary.json").read_text(encoding="utf-8"))
        assert summary["run_mode"] == "context_batch"
        assert summary["case_count"] == 2
        assert summary["context_count"] == 1
        assert summary["ingest_count"] == 1

        isolated_system = FakeSystem()
        isolated_output = directory / "isolated" / "results.jsonl"
        isolated = MemEvalRunner(isolated_system, directory / "isolated-work").run(
            [first, second], MemEvalRunConfig("isolated", top_k=3), isolated_output
        )
        assert isolated_system.created == 2
        assert isolated_system.ingested == 2
        assert isolated_system.cleaned == 2
        assert all(row["run_mode"] == "case_isolated" for row in isolated)
        isolated_summary = json.loads(
            (isolated_output.parent / "run_summary.json").read_text(encoding="utf-8")
        )
        assert isolated_summary["run_mode"] == "case_isolated"
        assert isolated_summary["ingest_count"] == 2


def test_context_cache_rejects_one_id_with_different_content():
    with workspace_directory("context-mismatch") as directory:
        first = artifact(directory, "D02", "q1", [
            {"event_id": "e1", "session_id": "s1", "content": "one", "metadata": {}}
        ], {"gold_evidence_ids": ["s1"]})
        second = artifact(directory, "D02", "q2", [
            {"event_id": "e2", "session_id": "s2", "content": "two", "metadata": {}}
        ], {"gold_evidence_ids": ["s2"]})
        for item in (first, second):
            item.case["envelope"]["identity"]["context_id"] = "same-id"

        with pytest.raises(ValueError, match="different Context content"):
            ContextCache().group([first, second])


def test_d08_contexts_are_never_reused_after_mutating_actions():
    with workspace_directory("context-d08") as directory:
        event = {"event_id": "e", "session_id": "s", "content": "needle",
                 "metadata": {"memory_id": "m", "user_id": "user", "tenant_id": "tenant"}}
        cases = [artifact(directory, "D08", label, [event], {
            "allowed_memory_ids": ["m"], "forbidden_memory_ids": [],
            "deleted_memory_ids": [], "canary_tokens": [],
        }) for label in ("p1", "p2")]
        for item in cases:
            item.case["envelope"]["identity"].update(
                context_id="shared-private", user_id="user", tenant_id="tenant"
            )
        cases[1] = type(cases[1])(
            cases[1].dimension_id, cases[1].case_path, cases[0].context_path, cases[1].case
        )

        groups = ContextCache().group(cases)
        assert len(groups) == 2
        assert all(len(group.artifacts) == 1 for group in groups)


def test_frozen_release_has_298_cases_in_246_validated_context_groups():
    artifacts = list(ReviewedBenchmark("dataset/MemEval-v0.1").iter_cases())
    groups = ContextCache().group(artifacts)

    assert len(artifacts) == 298
    assert len(groups) == 246
    assert max(len(group.artifacts) for group in groups) == 10
