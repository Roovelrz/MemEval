from dataclasses import asdict

from memory_eval.systems import OptionalSystemOperations, SystemOperationResult


def test_optional_operations_never_manufacture_scores_or_capabilities():
    adapter = OptionalSystemOperations()
    assert not any(asdict(adapter.capabilities).values())
    results = [
        adapter.query(None, query="question"),
        adapter.get_profile(None), adapter.get_trace(None), adapter.get_stats(None),
        adapter.list_memories(None), adapter.delete(None, memory_ids=["memory"]),
    ]
    for result in results:
        assert result.status == "unsupported"
        assert result.reason
        assert result.data is None
        assert "score" not in asdict(result)
    assert SystemOperationResult("ok", data=[]).status != results[0].status
