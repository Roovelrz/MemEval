from __future__ import annotations

import unittest
from types import SimpleNamespace

from memory_eval.memory.reme import ReMeAdapter
from tests.helpers import workspace_directory


class FakeApplication:
    instances: list["FakeApplication"] = []

    def __init__(self, **config) -> None:
        self.config = config
        self.calls: list[tuple] = []
        self.__class__.instances.append(self)

    async def start(self) -> None:
        self.calls.append(("start",))

    async def close(self) -> None:
        self.calls.append(("close",))

    async def run_job(self, name: str, **kwargs):
        self.calls.append((name, kwargs))
        if name == "reindex":
            return SimpleNamespace(success=True, answer="", metadata={})
        return SimpleNamespace(
            success=True,
            answer="",
            metadata={
                "results": [
                    {
                        "id": "chunk-1",
                        "path": "daily/case-1/session-1.md",
                        "text": "## User\n\n中文内容",
                        "scores": {"keyword": 3.0, "score": 3.0},
                        "start_line": 7,
                        "end_line": 10,
                    }
                ]
            },
        )


class ReMeAdapterTest(unittest.TestCase):
    def setUp(self) -> None:
        FakeApplication.instances.clear()

    def test_writes_verbatim_markdown_and_maps_search_result(self) -> None:
        with workspace_directory("reme-adapter") as directory:
            adapter = ReMeAdapter(directory, application_factory=FakeApplication)
            namespace = "longmemeval:run:case-1"
            adapter.reset(namespace)
            adapter.add_session(
                namespace,
                "session-1",
                "2024/01/01 (Mon) 10:00",
                [
                    {"role": "user", "content": "中文内容"},
                    {"role": "assistant", "content": "Original answer"},
                ],
            )
            markdown = (adapter.workspace / "daily" / "case-1" / "session-1.md").read_text(
                encoding="utf-8"
            )
            hits = adapter.search(namespace, "中文", 10)

        self.assertIn('session_id: "session-1"', markdown)
        self.assertIn('timestamp: "2024/01/01 (Mon) 10:00"', markdown)
        self.assertIn("dataset: longmemeval", markdown)
        self.assertIn('case_id: "case-1"', markdown)
        self.assertIn("## User\n\n中文内容", markdown)
        self.assertIn("## Assistant\n\nOriginal answer", markdown)
        self.assertEqual(hits[0].metadata["session_id"], "session-1")
        self.assertEqual(hits[0].metadata["timestamp"], "2024/01/01 (Mon) 10:00")
        self.assertEqual(hits[0].score, 3.0)
        calls = FakeApplication.instances[0].calls
        self.assertEqual([call[0] for call in calls], ["start", "reindex", "search", "close"])
        self.assertEqual(calls[2][1]["vector_weight"], 0.0)
        self.assertEqual(
            FakeApplication.instances[0].config["components"]["file_store"]["default"]["embedding_store"],
            "",
        )
        self.assertFalse(adapter.workspace.exists())

    def test_reset_removes_previous_case_workspace(self) -> None:
        with workspace_directory("reme-reset") as directory:
            adapter = ReMeAdapter(directory, application_factory=FakeApplication)
            first = "longmemeval:run:first"
            adapter.reset(first)
            adapter.add_session(first, "old", "2024/01/01", [{"role": "user", "content": "old"}])
            old_path = adapter.workspace / "daily" / "first" / "old.md"
            self.assertTrue(old_path.exists())
            adapter.reset("longmemeval:run:second")
            self.assertFalse(old_path.exists())

    def test_duplicate_session_ids_get_distinct_files(self) -> None:
        with workspace_directory("reme-duplicate") as directory:
            adapter = ReMeAdapter(directory, application_factory=FakeApplication)
            namespace = "longmemeval:run:case"
            adapter.reset(namespace)
            adapter.add_session(namespace, "same", "2024/01/01", [{"role": "user", "content": "one"}])
            adapter.add_session(namespace, "same", "2024/01/02", [{"role": "user", "content": "two"}])
            files = sorted((adapter.workspace / "daily" / "case").glob("*.md"))

        self.assertEqual([path.name for path in files], ["same.md", "same__2.md"])


if __name__ == "__main__":
    unittest.main()
