import json
import pytest

from memory_eval.adapters.memory.reme import ReMeCliMemoryAdapter
from memory_eval.systems import ReMeSystemAdapter
from tests.helpers import workspace_directory


def make_case(directory, label, events):
    path = directory / f"{label}.json"
    path.write_text(json.dumps({"events": events}), encoding="utf-8")
    return {
        "envelope": {"case_id": label, "dimension_id": "D08",
                     "context": {"event_count": len(events)}, "query": {"text": "memory"}},
        "gold": {"payload": {}},
    }, path


def event(event_id, memory_id, content, session_id="shared"):
    return {"event_id": event_id, "session_id": session_id, "role": "user",
            "content": content, "metadata": {"memory_id": memory_id}}


class FileIndexService:
    """HTTP double that keeps a stale index until the real adapter requests reindex."""

    def __init__(self):
        self.workspaces = {}
        self.indices = {}
        self.fail_reindex = False
        self.fail_search = False

    def start(self, command, workspace, port, config, log_path):
        self.workspaces[port] = workspace
        return object(), object()

    def http(self, port, endpoint, payload, timeout):
        if endpoint == "reindex":
            if self.fail_reindex:
                return {"success": False, "answer": "fixture failure"}
            self.indices[port] = [
                {"path": str(p), "content": p.read_text(encoding="utf-8"), "score": 1.0}
                for p in self.workspaces[port].glob("daily/**/*.md")
            ]
            return {"results": [{"path": item["path"], "success": True} for item in self.indices[port]]}
        if endpoint == "health_check":
            return {"n_chunks": len(self.indices.get(port, [])), "n_nodes": 0}
        if self.fail_search:
            return {"success": False, "answer": "fixture failure"}
        return {"results": [item for item in self.indices[port] if payload["query"] in item["content"]]}


def test_namespace_delete_reset_and_observation_use_existing_backend():
    with workspace_directory("system-operations") as directory:
        service = FileIndexService()
        backend = ReMeCliMemoryAdapter(
            command=["reme"], config_path=directory / "config.yaml", startup_timeout=5,
            vector_weight=0, start_fn=service.start, stop_fn=lambda *args: None,
            wait_fn=lambda *args: None, http_fn=service.http,
        )
        adapter = ReMeSystemAdapter(backend)
        events = [event("e1", "m1", "secret_alpha"), event("e2", "m2", "public_beta"),
                  event("e3", "m1", "secret_alpha", "another"),
                  {"event_id": "delete_command", "session_id": "lifecycle", "role": "system",
                   "content": "Delete m1", "metadata": {"operation": "delete", "target_memory_id": "m1"}}]
        case, path = make_case(directory, "case", events)

        def open_namespace(name, port):
            return adapter.create_namespace(
                namespace=name, workspace=directory / "namespaces", case=case, context_path=path,
                dataset_id="fixture", port=port, service_log_path=directory / f"{port}.log",
            )

        left = open_namespace("user/a", 25001)
        right = open_namespace("user:a", 25002)
        assert left.backend_runtime.workspace != right.backend_runtime.workspace
        assert len(left.backend_runtime.workspace.name) == 16
        with pytest.raises(ValueError, match="overlaps"):
            open_namespace("user/a", 25003)
        with pytest.raises(ValueError, match="port"):
            open_namespace("third", 25002)
        with pytest.raises(ValueError, match="ingest"):
            adapter.search(left, query="secret_alpha", top_k=3)
        for runtime in (left, right):
            adapter.ingest(runtime)
            assert adapter.search(runtime, query="secret_alpha", top_k=3).memories
        assert len(adapter.list_memories(left).data) == 2
        assert "Delete m1" not in str(adapter.list_memories(left).data)
        before = adapter.list_memories(left).data
        with pytest.raises(ValueError, match="Unknown"):
            adapter.delete(left, memory_ids=["m1", "unknown"])
        assert adapter.list_memories(left).data == before
        adapter.delete(left, memory_ids=["m1"])
        assert "m1" not in left.memory_to_session_id
        assert "e1" not in left.event_to_session_id
        assert not adapter.search(left, query="secret_alpha", top_k=3).memories
        assert adapter.search(left, query="public_beta", top_k=3).memories
        assert adapter.search(right, query="secret_alpha", top_k=3).memories
        memories = adapter.list_memories(left).data
        assert len(memories) == 1
        assert memories[0]["source_memory_ids"] == ["m2"]
        trace = adapter.get_trace(left).data
        assert trace["kind"] == "adapter_operations"
        trace["events"].clear()
        assert adapter.get_trace(left).data["events"]
        stats = adapter.get_stats(left).data
        assert stats["operations"]["delete"]["calls"] == 1
        assert stats["cost"] is None
        assert adapter.query(left, query="question").status == "unsupported"
        assert adapter.get_profile(left).status == "unsupported"
        service.fail_search = True
        with pytest.raises(RuntimeError, match="search failed"):
            adapter.search(left, query="public_beta", top_k=3)
        assert adapter.get_trace(left).data["events"][-1]["status"] == "error"
        service.fail_search = False
        service.fail_reindex = True
        with pytest.raises(RuntimeError, match="reindex failed"):
            adapter.delete(left, memory_ids=["m2"])
        assert adapter.get_trace(left).data["events"][-1]["status"] == "error"
        with pytest.raises(ValueError, match="ingest"):
            adapter.search(left, query="public_beta", top_k=3)
        service.fail_reindex = False
        adapter.reset(left)
        assert "m1" in left.memory_to_session_id
        assert adapter.get_trace(left).data["events"] == []
        adapter.ingest(left)
        assert adapter.search(left, query="secret_alpha", top_k=3).memories
        adapter.delete(left, memory_ids=["shared", "another"])
        assert adapter.list_memories(left).data == []
        assert adapter.search(left, query="secret_alpha", top_k=3).memories == []
        for runtime in (left, right):
            adapter.cleanup(runtime)
            adapter.cleanup(runtime)
        with pytest.raises(ValueError, match="closed"):
            adapter.ingest(left)
