from __future__ import annotations

import unittest

from memory_eval.memory.in_memory import InMemorySessionAdapter


class MemoryAdapterTest(unittest.TestCase):
    def test_search_top_k_reset_and_namespace_isolation(self) -> None:
        adapter = InMemorySessionAdapter()
        adapter.reset("a")
        adapter.reset("b")
        adapter.add_session("a", "a1", "2024/01/01", [{"role": "user", "content": "red apple"}])
        adapter.add_session("a", "a2", "2024/01/02", [{"role": "user", "content": "blue car"}])
        adapter.add_session("b", "b1", "2024/01/03", [{"role": "user", "content": "red apple"}])

        hits = adapter.search("a", "red apple", top_k=1)
        self.assertEqual([hit.metadata["session_id"] for hit in hits], ["a1"])
        self.assertNotIn("b1", {hit.metadata["session_id"] for hit in hits})

        adapter.reset("a")
        self.assertEqual(adapter.search("a", "red", top_k=10), [])


if __name__ == "__main__":
    unittest.main()
