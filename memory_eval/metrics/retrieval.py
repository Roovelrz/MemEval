"""Session-level LongMemEval retrieval metrics."""

from __future__ import annotations


def retrieval_scores(
    answer_session_ids: list[str],
    retrieved_session_ids: list[str | None],
    is_abstention: bool,
) -> dict[str, float] | None:
    """Return Recall@K and Hit@K, or None for abstention/no-location cases."""
    if is_abstention or not answer_session_ids:
        return None
    gold = set(answer_session_ids)
    retrieved = {ident for ident in retrieved_session_ids if ident is not None}
    overlap = gold & retrieved
    return {
        "recall_at_k": len(overlap) / len(gold),
        "hit_at_k": float(bool(overlap)),
    }
