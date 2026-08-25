"""Canonical data exchanged by dataset, memory, and runner adapters."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class EvalSession:
    session_id: str
    timestamp: str
    messages: list[dict[str, Any]]


@dataclass
class EvalCase:
    id: str
    question_type: str
    question: str
    gold_answer: str
    question_date: str
    sessions: list[EvalSession]
    answer_session_ids: list[str]
    is_abstention: bool


@dataclass
class MemoryHit:
    text: str
    score: float | None
    metadata: dict[str, Any]
