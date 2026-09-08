from __future__ import annotations

import pytest

from dataset.build_pipeline import ReviewedBenchmark


DIMENSIONS = (
    ("D01", 37, "write"),
    ("D02", 37, "retrieval"),
    ("D03", 38, "temporal"),
    ("D04", 38, "activation"),
    ("D05", 37, "profile"),
    ("D06", 37, "conflict"),
    ("D07", 37, "scale"),
    ("D08", 37, "privacy"),
)


@pytest.mark.parametrize(("dimension_id", "case_count", "payload_type"), DIMENSIONS)
def test_frozen_dimension_contract(dimension_id: str, case_count: int, payload_type: str) -> None:
    artifacts = list(ReviewedBenchmark("dataset/MemEval-v0.1").iter_cases(dimension_id))
    assert len(artifacts) == case_count
    assert all(artifact.case["gold"]["payload_type"] == payload_type for artifact in artifacts)
    assert all(artifact.context_path.is_file() for artifact in artifacts)
