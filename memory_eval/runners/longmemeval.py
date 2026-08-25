"""Prepare isolated LongMemEval cases for the upstream AML pipeline."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Iterable

from memory_eval.datasets.models import EvalCase, EvalSession, MemoryHit
from memory_eval.memory.base import MemoryAdapter
from memory_eval.memory.in_memory import serialize_session


def _write_jsonl(path: Path, rows: Iterable[dict]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def _oracle_hits(case: EvalCase) -> list[MemoryHit]:
    by_id: dict[str, EvalSession] = {session.session_id: session for session in case.sessions}
    missing = [ident for ident in case.answer_session_ids if ident not in by_id]
    if missing:
        raise ValueError(f"case {case.id} references missing answer sessions: {missing}")
    return [
        MemoryHit(
            text=serialize_session(by_id[ident].timestamp, by_id[ident].messages),
            score=None,
            metadata={"session_id": ident, "timestamp": by_id[ident].timestamp},
        )
        for ident in case.answer_session_ids
    ]


class LongMemEvalRunner:
    def __init__(self, memory: MemoryAdapter) -> None:
        self.memory = memory

    def prepare(
        self,
        cases: list[EvalCase],
        run_id: str,
        output_dir: str | Path,
        mode: str,
        top_k: int,
    ) -> tuple[Path, Path]:
        if mode not in {"oracle", "memory"}:
            raise ValueError("mode must be 'oracle' or 'memory'")
        if top_k < 1:
            raise ValueError("top_k must be positive")
        run_dir = Path(output_dir) / run_id
        run_dir.mkdir(parents=True, exist_ok=True)

        prepared_rows: list[dict] = []
        retrieval_rows: list[dict] = []
        for case in cases:
            namespace = f"longmemeval:{run_id}:{case.id}"
            if mode == "oracle":
                started = time.perf_counter()
                hits = _oracle_hits(case)
            else:
                self.memory.reset(namespace)
                for session in case.sessions:
                    self.memory.add_session(
                        namespace=namespace,
                        session_id=session.session_id,
                        timestamp=session.timestamp,
                        messages=session.messages,
                    )
                started = time.perf_counter()
                hits = self.memory.search(namespace=namespace, query=case.question, top_k=top_k)
            latency_ms = (time.perf_counter() - started) * 1000

            prepared_rows.append(
                {
                    "id": case.id,
                    "question": case.question,
                    "gold_answer": case.gold_answer,
                    "retrieved_context": [hit.text for hit in hits],
                    "question_type": case.question_type,
                }
            )
            retrieval_rows.append(
                {
                    "id": case.id,
                    "question_type": case.question_type,
                    "query": case.question,
                    "gold_answer": case.gold_answer,
                    "answer_session_ids": case.answer_session_ids,
                    "is_abstention": case.is_abstention,
                    "namespace": namespace,
                    "mode": mode,
                    "retrieved": [
                        {
                            "rank": rank,
                            "text": hit.text,
                            "score": hit.score,
                            "session_id": hit.metadata.get("session_id"),
                            "timestamp": hit.metadata.get("timestamp"),
                        }
                        for rank, hit in enumerate(hits, start=1)
                    ],
                    "search_latency_ms": latency_ms,
                }
            )

        prepared_path = run_dir / "prepared.jsonl"
        retrieval_path = run_dir / "retrieval.jsonl"
        _write_jsonl(prepared_path, prepared_rows)
        _write_jsonl(retrieval_path, retrieval_rows)
        return prepared_path, retrieval_path
