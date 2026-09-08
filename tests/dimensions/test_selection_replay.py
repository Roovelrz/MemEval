from __future__ import annotations

from copy import deepcopy

import pytest

from dataset.build_pipeline import ReviewedBenchmark
from dataset.build_pipeline.release import DIMENSION_DIRECTORIES
from dataset.build_pipeline.selection import (
    build_selected_sources_snapshot,
    manifest_selection_seed,
    validate_selected_sources,
)


@pytest.mark.parametrize("dimension_id", DIMENSION_DIRECTORIES)
def test_manifest_replays_the_frozen_selection(dimension_id: str) -> None:
    benchmark = ReviewedBenchmark("dataset/MemEval-v0.1")
    version_dir = benchmark.dimension_dir(dimension_id)
    manifest = benchmark.load_manifest(dimension_id)
    first = build_selected_sources_snapshot(version_dir)
    second = build_selected_sources_snapshot(version_dir)

    assert manifest_selection_seed(manifest)
    assert first == second == manifest["selected_sources"]
    assert first["case_count"] == manifest["counts"]["cases"]
    assert all(
        set(entry) == {"case_id", "source_record_id", "source_question_id"}
        for entry in first["entries"]
    )
    assert validate_selected_sources(version_dir, manifest) == []


def test_selection_replay_rejects_a_stale_manifest() -> None:
    benchmark = ReviewedBenchmark("dataset/MemEval-v0.1")
    version_dir = benchmark.dimension_dir("D01")
    manifest = deepcopy(benchmark.load_manifest("D01"))
    manifest["selected_sources"]["entries"].pop()

    assert validate_selected_sources(version_dir, manifest) == [
        "selected_sources does not match the frozen Cases"
    ]
