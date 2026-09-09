"""One-click configuration wrapper for the current MemEval-v0.1 pipeline.

Edit ``CONFIG`` below, then run this file from any working directory:

    py -3.12 run_eval.py

The dimension-aware runner owns Retrieval, Answer, Judge, Trace, Dashboard,
progress, and resume behavior. API credentials remain in the repository
``.env`` file or process environment; they are never stored here.
"""

from __future__ import annotations

import shlex
import subprocess
import sys
from pathlib import Path
from typing import Any

from dataset.build_pipeline.release import DIMENSION_DIRECTORIES
from memory_eval.dataset_registry import resolve_dataset


REPO_ROOT = Path(__file__).resolve().parent
MEMEVAL_RUNNER = REPO_ROOT / "scripts" / "run_memeval.py"


# ---------------------------------------------------------------------------
# 新运行只需修改此区域。
# ---------------------------------------------------------------------------
CONFIG: dict[str, Any] = {
    # 正式八维度数据集。data 可填写另一个正式 MemEval release 目录，并覆盖 dataset。
    "dataset": "MemEval-v0.1",
    "data": None,

    # 筛选。空列表表示全部维度/Case；limit=None 表示运行全部 298 条。
    "dimensions": [],  # 例如 ["D01", "D08"]
    "case_ids": [],  # 例如 ["d08:agentmembench:deletion_01"]
    "limit": None,  # smoke test 可设为 5

    # Retrieval。
    "top_k": 10,
    "search_multiplier": 1,
    "min_score": 0.0,
    "context_batch": False,
    "reme_cmd": None,
    "reme_config": None,
    "reme_port": 25000,
    "reme_startup_timeout": 60.0,
    "vector_weight": 0.0,

    # 输出与断点续跑。run_id 为空时自动生成时间戳。
    "output_dir": None,  # None 使用仓库的 results 根目录
    "run_id": "",
    "resume": True,

    # Answer：仅 D02/D03/D05/D06/D07 执行。
    "answer_api_key_env": "DEEPSEEK_API_KEY",
    "answer_base_url_env": "DEEPSEEK_BASE_URL",
    "answer_model_env": "DEEPSEEK_MODEL",
    "answer_workers": 4,
    "answer_max_tokens": 65536,

    # Judge：复用同一组环境变量，也可独立改成其他变量名。
    "judge_api_key_env": "DEEPSEEK_API_KEY",
    "judge_base_url_env": "DEEPSEEK_BASE_URL",
    "judge_model_env": "DEEPSEEK_MODEL",
    "judge_workers": 4,
    "judge_max_tokens": 65536,
}


def _add_option(command: list[str], flag: str, value: Any) -> None:
    """Append one CLI option, omitting values intentionally left blank."""

    if value is None or value == "":
        return
    command.extend([flag, str(value)])


def _add_repeated(command: list[str], flag: str, values: Any) -> None:
    for value in values or []:
        _add_option(command, flag, value)


def build_command(config: dict[str, Any]) -> list[str]:
    """Translate ``CONFIG`` into arguments accepted by ``run_memeval.py``."""

    command = [sys.executable, str(MEMEVAL_RUNNER)]
    _add_option(command, "--dataset", config.get("dataset"))
    _add_option(command, "--data", config.get("data"))
    _add_repeated(command, "--dimension", config.get("dimensions"))
    _add_repeated(command, "--case-id", config.get("case_ids"))

    option_map = (
        ("--limit", "limit"),
        ("--top-k", "top_k"),
        ("--search-multiplier", "search_multiplier"),
        ("--min-score", "min_score"),
        ("--run-id", "run_id"),
        ("--output-dir", "output_dir"),
        ("--reme-cmd", "reme_cmd"),
        ("--reme-config", "reme_config"),
        ("--reme-port", "reme_port"),
        ("--reme-startup-timeout", "reme_startup_timeout"),
        ("--vector-weight", "vector_weight"),
        ("--answer-api-key-env", "answer_api_key_env"),
        ("--answer-base-url-env", "answer_base_url_env"),
        ("--answer-model-env", "answer_model_env"),
        ("--answer-workers", "answer_workers"),
        ("--answer-max-tokens", "answer_max_tokens"),
        ("--judge-api-key-env", "judge_api_key_env"),
        ("--judge-base-url-env", "judge_base_url_env"),
        ("--judge-model-env", "judge_model_env"),
        ("--judge-workers", "judge_workers"),
        ("--judge-max-tokens", "judge_max_tokens"),
    )
    for flag, key in option_map:
        _add_option(command, flag, config.get(key))

    if config.get("context_batch"):
        command.append("--context-batch")
    command.append("--resume" if config.get("resume") else "--no-resume")
    return command


def _repo_relative_path(value: Any) -> Path:
    path = Path(str(value))
    return path if path.is_absolute() else REPO_ROOT / path


def _validate_string_list(config: dict[str, Any], key: str) -> list[str]:
    values = config.get(key)
    if not isinstance(values, list) or any(
        not isinstance(value, str) or not value.strip() for value in values
    ):
        raise ValueError(f"{key} must be a list of non-empty strings")
    return values


def _validate_config(config: dict[str, Any]) -> None:
    dataset = config.get("dataset")
    if not isinstance(dataset, str) or not dataset.strip():
        raise ValueError("dataset must be a registered dataset ID or release directory")

    data = config.get("data")
    data_path = _repo_relative_path(data).resolve() if data not in {None, ""} else None
    dataset_value = dataset
    if "\\" in dataset or "/" in dataset:
        dataset_value = str(_repo_relative_path(dataset).resolve())
    source, spec = resolve_dataset(dataset_value, data_path)
    if spec.get("adapter") not in {None, "memeval"} or not source.is_dir():
        raise ValueError("run_eval.py requires a formal MemEval release directory")

    dimensions = _validate_string_list(config, "dimensions")
    unknown_dimensions = sorted(set(dimensions) - set(DIMENSION_DIRECTORIES))
    if unknown_dimensions:
        raise ValueError(f"Unknown dimensions: {unknown_dimensions}")
    _validate_string_list(config, "case_ids")

    limit = config.get("limit")
    if limit is not None and (
        not isinstance(limit, int) or isinstance(limit, bool) or limit < 1
    ):
        raise ValueError("limit must be None or a positive integer")

    positive_integers = (
        "top_k", "search_multiplier", "reme_port", "answer_workers",
        "answer_max_tokens", "judge_workers", "judge_max_tokens",
    )
    for key in positive_integers:
        value = config.get(key)
        if not isinstance(value, int) or isinstance(value, bool) or value < 1:
            raise ValueError(f"{key} must be a positive integer")

    for key in ("context_batch", "resume"):
        if not isinstance(config.get(key), bool):
            raise ValueError(f"{key} must be a boolean")

    reme_config = config.get("reme_config")
    if reme_config not in {None, ""} and not _repo_relative_path(reme_config).is_file():
        raise FileNotFoundError(f"ReMe config not found: {_repo_relative_path(reme_config).resolve()}")
    if not MEMEVAL_RUNNER.is_file():
        raise FileNotFoundError(f"MemEval runner not found: {MEMEVAL_RUNNER}")


def main() -> int:
    _validate_config(CONFIG)
    command = build_command(CONFIG)
    print(f"工作目录: {REPO_ROOT}", flush=True)
    print("即将运行 MemEval-v0.1:", flush=True)
    print("  " + shlex.join(command), flush=True)
    print("API Key 不写入脚本；Answer/Judge 从 .env 或环境变量读取。", flush=True)
    completed = subprocess.run(command, cwd=REPO_ROOT, check=False)
    print(f"Eval exit code: {completed.returncode}", flush=True)
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
