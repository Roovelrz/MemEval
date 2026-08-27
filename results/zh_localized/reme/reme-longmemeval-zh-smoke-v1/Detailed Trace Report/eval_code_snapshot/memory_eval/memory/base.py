"""Memory system boundary used by benchmark runners."""

from __future__ import annotations

from typing import Protocol

from memory_eval.datasets.models import MemoryHit


class MemoryAdapter(Protocol):
    def reset(self, namespace: str) -> None:
        ...

    def add_session(
        self,
        namespace: str,
        session_id: str,
        timestamp: str,
        messages: list[dict],
    ) -> None:
        ...

    def search(self, namespace: str, query: str, top_k: int) -> list[MemoryHit]:
        ...
