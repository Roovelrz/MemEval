"""Dependency-free lexical adapter for harness smoke tests only."""

from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass

from memory_eval.datasets.models import MemoryHit


TOKEN_PATTERN = re.compile(r"[A-Za-z0-9_]+|[\u4e00-\u9fff]")


@dataclass
class _StoredSession:
    session_id: str
    timestamp: str
    text: str


def serialize_session(timestamp: str, messages: list[dict]) -> str:
    lines = [f"[Date: {timestamp}]", ""]
    for message in messages:
        role = str(message.get("role", "unknown"))
        content = str(message.get("content", ""))
        lines.append(f"{role}: {content}")
    return "\n".join(lines)


def _tokens(text: str) -> set[str]:
    return {token.lower() for token in TOKEN_PATTERN.findall(text)}


class InMemorySessionAdapter:
    """Store whole sessions and rank them by query-token overlap.

    This validates Add/Search wiring. It is not a production memory baseline.
    """

    def __init__(self) -> None:
        self._namespaces: dict[str, list[_StoredSession]] = defaultdict(list)

    def reset(self, namespace: str) -> None:
        self._namespaces[namespace] = []

    def add_session(
        self,
        namespace: str,
        session_id: str,
        timestamp: str,
        messages: list[dict],
    ) -> None:
        self._namespaces[namespace].append(
            _StoredSession(
                session_id=session_id,
                timestamp=timestamp,
                text=serialize_session(timestamp, messages),
            )
        )

    def search(self, namespace: str, query: str, top_k: int) -> list[MemoryHit]:
        if top_k < 1:
            raise ValueError("top_k must be positive")
        query_tokens = _tokens(query)
        ranked: list[tuple[float, int, _StoredSession]] = []
        for index, session in enumerate(self._namespaces.get(namespace, [])):
            overlap = len(query_tokens & _tokens(session.text))
            score = overlap / len(query_tokens) if query_tokens else 0.0
            ranked.append((score, index, session))
        ranked.sort(key=lambda item: (-item[0], item[1]))
        return [
            MemoryHit(
                text=session.text,
                score=score,
                metadata={"session_id": session.session_id, "timestamp": session.timestamp},
            )
            for score, _, session in ranked[:top_k]
        ]
