"""Exercise stage-26 operations against two real local BM25 ReMe services."""

from __future__ import annotations

import json
import socket
import sys
import shutil
import time
from contextlib import contextmanager
from pathlib import Path
from uuid import uuid4

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from memory_eval.adapters.memory.reme import (
    ReMeCliMemoryAdapter, create_bm25_config, resolve_reme_command,
)
from memory_eval.systems import ReMeSystemAdapter


@contextmanager
def smoke_directory():
    directory = REPO_ROOT / ".test-artifacts" / f"real-system-smoke-{uuid4().hex}"
    directory.mkdir(parents=True)
    try:
        yield directory
    finally:
        # Windows CLI children can release inherited log handles just after exit.
        for attempt in range(20):
            try:
                shutil.rmtree(directory)
                break
            except PermissionError:
                if attempt == 19:
                    raise
                time.sleep(0.1)


def free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def main():
    with smoke_directory() as directory:
        config = create_bm25_config(directory / "bm25.yaml", 0.0)
        backend = ReMeCliMemoryAdapter(command=resolve_reme_command(None), config_path=config,
                                      startup_timeout=60, vector_weight=0.0)
        adapter = ReMeSystemAdapter(backend)
        runtimes = []
        try:
            for namespace, words in [("owner", ("quartz", "willow")), ("other", ("citrus", "marigold"))]:
                events = [{"event_id": f"e{i}", "session_id": "shared", "role": "user",
                           "content": f"My favorite word is {word}.", "metadata": {"memory_id": f"m{i}"}}
                          for i, word in enumerate(words)]
                path = directory / f"{namespace}.json"
                path.write_text(json.dumps({"events": events}), encoding="utf-8")
                case = {"envelope": {"case_id": "fixture", "dimension_id": "D08",
                                     "context": {"event_count": 2}, "query": {"text": "quartz"}},
                        "gold": {"payload": {}}}
                runtime = adapter.create_namespace(
                    namespace=namespace, workspace=directory / "namespaces", case=case,
                    context_path=path, dataset_id="smoke", port=free_port(),
                    service_log_path=directory / f"{namespace}.log",
                )
                runtimes.append(runtime)
                assert not adapter.ingest(runtime).failures
            owner, other = runtimes

            def hits(runtime, word):
                return adapter.search(runtime, query=word, top_k=3).memories

            assert hits(owner, "quartz")
            assert hits(other, "citrus")
            assert not hits(other, "quartz")
            assert not hits(owner, "citrus")
            adapter.delete(owner, memory_ids=["m0"])
            assert not hits(owner, "quartz")
            assert hits(owner, "willow")
            assert hits(other, "citrus")
            assert adapter.list_memories(owner).data[0]["source_memory_ids"] == ["m1"]
            adapter.reset(owner)
            adapter.ingest(owner)
            assert hits(owner, "quartz")
            adapter.delete(owner, memory_ids=["shared"])
            assert adapter.list_memories(owner).data == []
            assert not hits(owner, "quartz")
            report = {"status": "ok", "namespaces": 2,
                              "checks": ["positive_retrieval", "isolation", "partial_delete",
                                         "reset", "delete_all", "list_memories"],
                      "capabilities": adapter.run_metadata()["capabilities"]}
        finally:
            for runtime in reversed(runtimes):
                adapter.cleanup(runtime)
    print(json.dumps(report))


if __name__ == "__main__":
    main()
