from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace

from dataset.build_pipeline.release import ReviewedCaseArtifact
from memory_eval.runners import MemEvalRunConfig, MemEvalRunner
from memory_eval.systems import SystemCapabilities, SystemIngestResult, SystemOperationResult, SystemSearchResult
from tests.helpers import workspace_directory


def artifact(directory: Path, dimension: str, label: str, events: list[dict], payload: dict):
    path = directory / f"{label}.json"
    path.write_text(json.dumps({"events": events}), encoding="utf-8")
    case = {
        "envelope": {
            "case_id": label, "dimension_id": dimension,
            "identity": {"context_id": f"context:{label}", "user_id": None, "tenant_id": None},
            "context": {"event_count": len(events)}, "query": {"text": "needle"},
        },
        "gold": {"payload": payload},
    }
    return ReviewedCaseArtifact(dimension, directory / f"{label}-case.json", path, case)


@dataclass
class FakeRuntime:
    canonical_case: dict
    events: list[dict]
    deleted: list[str]


class FakeSystem:
    name = "fake"
    capabilities = SystemCapabilities(write_trace=True, retrieval=True, delete=True,
                                      user_isolation=True, latency_stats=True)

    def __init__(self):
        self.opened_events = []
        self.cleaned = 0

    def run_metadata(self):
        return {"memory_version": "test"}

    def create_namespace(self, **kwargs):
        events = json.loads(Path(kwargs["context_path"]).read_text(encoding="utf-8"))["events"]
        self.opened_events.append(events)
        sessions = [
            {"session_id": event["session_id"], "messages": [event]}
            for event in events if event.get("metadata", {}).get("operation") != "delete"
        ]
        evidence = kwargs["case"]["gold"]["payload"].get("gold_evidence_ids", [])
        return FakeRuntime({"sessions": sessions, "evidence_session_ids": evidence}, events, [])

    def ingest(self, runtime):
        return SystemIngestResult({}, [], [], 1.5)

    def list_memories(self, runtime):
        return SystemOperationResult("ok", data=[
            {"event_ids": [message["event_id"] for message in session["messages"]]}
            for session in runtime.canonical_case["sessions"]
        ])

    def search(self, runtime, **kwargs):
        hits = []
        for session in runtime.canonical_case["sessions"]:
            message = session["messages"][0]
            memory_id = message.get("metadata", {}).get("memory_id")
            if memory_id not in runtime.deleted and kwargs["query"] in message.get("content", ""):
                hits.append({"session_id": session["session_id"], "score": 1.0})
        return SystemSearchResult({}, hits[:kwargs["top_k"]], 2.5)

    def delete(self, runtime, *, memory_ids):
        runtime.deleted.extend(memory_ids)
        return SystemOperationResult("ok", data={"deleted_ids": memory_ids})

    def query(self, runtime, *, query):
        return SystemOperationResult("unsupported", reason="fixture has no answer model")

    def get_profile(self, runtime):
        return SystemOperationResult("unsupported", reason="fixture has no profile")

    def get_trace(self, runtime):
        return SystemOperationResult("ok", data={"events": []})

    def get_stats(self, runtime):
        return SystemOperationResult("ok", data={"cost": None})

    def cleanup(self, runtime):
        self.cleaned += 1


def test_runner_emits_dimension_results_and_preserves_unsupported_status():
    with workspace_directory("memeval-runner") as directory:
        event = {"event_id": "e1", "session_id": "s1", "content": "needle", "metadata": {}}
        cases = [
            artifact(directory, "D01", "write", [event], {"scored_event_ids": ["e1"]}),
            artifact(directory, "D02", "retrieve", [event], {"gold_evidence_ids": ["s1"]}),
            artifact(directory, "D03", "temporal", [event], {"evidence_event_ids": ["e1"]}),
            artifact(directory, "D04", "activation", [event], {"should_activate": True}),
            artifact(directory, "D05", "profile", [event], {"profile_items": []}),
            artifact(directory, "D06", "conflict", [event], {"winning_fact_ids": []}),
            artifact(directory, "D07", "scale", [event], {"gold_evidence_ids": ["s1"]}),
        ]
        system = FakeSystem()
        results = MemEvalRunner(system, directory / "work").run(
            cases, MemEvalRunConfig("run", top_k=3), directory / "results.jsonl"
        )

        assert [row["status"] for row in results] == [
            "partial", "ok", "partial", "unsupported", "unsupported", "partial", "partial"
        ]
        assert results[0]["metrics"]["write_event_recall"] == 1.0
        assert results[1]["metrics"] == {
            "retrieval_evaluated": True, "hit_at_k": 1.0, "recall_at_k": 1.0, "mrr": 1.0
        }
        assert results[3]["prediction"]["status"] == "unsupported"
        assert results[3]["metrics"] == {}
        assert results[3]["error"] is None
        assert all(set(("run_id", "case_id", "dimension_id", "system", "system_version",
                        "prediction", "retrieved_memories", "trace", "latency", "cost",
                        "metrics", "status", "error")) <= row.keys() for row in results)
        assert len((directory / "results.jsonl").read_text(encoding="utf-8").splitlines()) == 7
        assert system.cleaned == 7


def test_d08_identity_partition_and_lifecycle_delete_do_not_use_gold_for_access():
    with workspace_directory("memeval-d08") as directory:
        visible_id = "allowed"
        events = [
            {"event_id": "forbidden", "session_id": "owner", "content": "needle private",
             "metadata": {"memory_id": "forbidden", "user_id": "owner", "tenant_id": "tenant"}},
            {"event_id": "allowed", "session_id": "querying", "content": "needle public",
             "metadata": {"memory_id": visible_id, "user_id": "querying", "tenant_id": "tenant"}},
            {"event_id": "delete", "session_id": "lifecycle", "content": "delete",
             "metadata": {"operation": "delete", "target_memory_id": visible_id,
                          "user_id": "querying", "tenant_id": "tenant"}},
        ]
        case = artifact(
            directory, "D08", "privacy", events,
            {"allowed_memory_ids": [], "forbidden_memory_ids": ["forbidden"],
             "deleted_memory_ids": [visible_id], "canary_tokens": []},
        )
        case.case["envelope"]["identity"].update(user_id="querying", tenant_id="tenant")
        system = FakeSystem()
        result = MemEvalRunner(system, directory / "work").run_case(case, MemEvalRunConfig("run"))

        assert [event["event_id"] for event in system.opened_events[0]] == ["allowed", "delete"]
        assert result["status"] == "ok"
        assert result["retrieved_memories"] == []
        assert result["metrics"]["deleted_exposure_count"] == 0
        assert result["metrics"]["forbidden_exposure_count"] == 0
        assert result["metrics"]["privacy_pass"] == 1.0
        assert not (directory / "work" / "_runner_inputs").exists()


def test_runner_writes_error_result_and_still_cleans_up():
    class BrokenSystem(FakeSystem):
        def ingest(self, runtime):
            raise RuntimeError("index unavailable")

    with workspace_directory("memeval-error") as directory:
        case = artifact(directory, "D02", "broken", [
            {"event_id": "e", "session_id": "s", "content": "needle", "metadata": {}}
        ], {"gold_evidence_ids": ["s"]})
        system = BrokenSystem()
        result = MemEvalRunner(system, directory / "work").run_case(case, MemEvalRunConfig("run"))

        assert result["status"] == "error"
        assert result["error"] == {"type": "RuntimeError", "message": "index unavailable"}
        assert result["latency"]["total"] is not None
        assert system.cleaned == 1
