from copy import deepcopy
from pathlib import Path

import pytest

import run_eval
from scripts.run_memeval import parser as memeval_parser


def test_default_config_targets_current_memeval_pipeline():
    run_eval._validate_config(run_eval.CONFIG)
    command = run_eval.build_command(run_eval.CONFIG)
    args = memeval_parser().parse_args(command[2:])

    assert Path(command[1]) == run_eval.MEMEVAL_RUNNER
    assert args.dataset == "MemEval-v0.1"
    assert args.limit is None
    assert args.dimension is None
    assert args.case_id is None
    assert args.resume is True
    assert args.answer_max_tokens == 65536
    assert args.judge_max_tokens == 65536


def test_config_maps_repeated_case_selection_and_resume_switch():
    config = deepcopy(run_eval.CONFIG)
    config.update(
        dimensions=["D01", "D08"],
        case_ids=["case-a", "case-b"],
        limit=5,
        context_batch=True,
        resume=False,
    )
    args = memeval_parser().parse_args(run_eval.build_command(config)[2:])

    assert args.dimension == ["D01", "D08"]
    assert args.case_id == ["case-a", "case-b"]
    assert args.limit == 5
    assert args.context_batch is True
    assert args.resume is False


@pytest.mark.parametrize("key", ["top_k", "answer_workers", "judge_max_tokens"])
def test_config_rejects_non_positive_worker_and_budget_values(key):
    config = deepcopy(run_eval.CONFIG)
    config[key] = 0

    with pytest.raises(ValueError, match=key):
        run_eval._validate_config(config)
