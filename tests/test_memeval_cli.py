from memory_eval.dataset_registry import resolve_dataset
from scripts.run_memeval import (
    _artifact_directory,
    _default_run_id,
    parser,
    select_artifacts,
)
from dataset.build_pipeline import ReviewedBenchmark
from tests.helpers import workspace_directory


def test_cli_selects_shared_context_for_batch_mode():
    args = parser().parse_args(["--dimension", "D03", "--limit", "2", "--context-batch"])
    source, spec = resolve_dataset(args.dataset, args.data)
    artifacts = select_artifacts(
        ReviewedBenchmark(source), args.dimension, args.case_id, args.limit
    )

    assert spec["adapter"] == "memeval"
    assert args.context_batch is True
    assert len(artifacts) == 2
    assert artifacts[0].case["envelope"]["identity"]["context_id"] == (
        artifacts[1].case["envelope"]["identity"]["context_id"]
    )
    assert artifacts[0].context_path.read_bytes() == artifacts[1].context_path.read_bytes()


def test_cli_resumes_by_default_and_can_disable_resume():
    args = parser().parse_args([])
    assert args.resume is True
    assert args.answer_max_tokens == 65536
    assert args.judge_max_tokens == 65536
    assert parser().parse_args(["--no-resume"]).resume is False


def test_default_run_id_matches_legacy_result_naming():
    run_id = _default_run_id("MemEval-v0.1")

    assert run_id.startswith("reme_memeval-v0-1_")
    assert run_id.endswith("Z")


def test_resume_reads_artifacts_from_organized_detailed_folder():
    with workspace_directory("memeval-organized-resume") as directory:
        detailed = directory / "Detailed Trace Report"
        assert _artifact_directory(directory) == detailed

        (directory / "results.jsonl").write_text("", encoding="utf-8")
        assert _artifact_directory(directory) == directory
        (directory / "results.jsonl").unlink()

        detailed.mkdir()

        assert _artifact_directory(directory) == detailed
