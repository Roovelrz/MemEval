from memory_eval.dataset_registry import resolve_dataset
from scripts.run_memeval import parser, select_artifacts
from dataset.build_pipeline import ReviewedBenchmark


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
