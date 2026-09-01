"""One-click configuration wrapper for the ReMe end-to-end memory eval.

Edit ``CONFIG`` below, then run this file from any working directory:

    py -3.12 run_eval.py

The existing end-to-end runner still owns all evaluation logic.  This file
only translates the editable configuration into its command-line arguments.
API credentials are intentionally not stored here; Answer and Judge read
them from the repository ``.env`` file (or the corresponding environment
variables).
"""

from __future__ import annotations

import shlex
import subprocess
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parent
END_TO_END_RUNNER = REPO_ROOT / "scripts" / "run_reme_end_to_end_eval.py"


# ---------------------------------------------------------------------------
# Edit only this section for a new run.
# ---------------------------------------------------------------------------
CONFIG: dict[str, Any] = {
    # Put the dataset file path here.  Absolute paths are recommended because
    # datasets may live outside this repository.  JSON, JSONL and supported
    # benchmark CSV files are accepted.  A registered dataset ID is also accepted for
    # backward compatibility, but a path is the preferred form.
    "dataset": "E:\\LRZ_Workplace\\fork\\LongMemEval\\data\\longmemeval_s_cleaned.json",
    "dataset_adapter": "auto",  # auto / longmemeval / locomo / personamem-v2

    # Case selection.  ``cases=0`` means all cases after ``start``.
    # Keep this at 1 for a smoke test, then change to 20/100/etc.
    "cases": 500, #需要测评的case样本数
    "start": 0, #从第几个case开始测评
    "shuffle": False, #是否随机打乱case顺序
    "seed": 42, #随机种子

    # Retrieval settings.
    "top_k": 5, #检索结果的top-k
    "search_multiplier": 3, #检索结果的top-k的倍数
    "min_score": 0.0, #检索结果的最小分数
    "retrieval_workers": 1,  # 检索线程数
    "base_port": 23330,
    "startup_timeout": 60.0,
    "reme_cmd": None,  # e.g. r"C:\\path\\to\\reme.exe"; None uses PATH
    "reme_config": None,  # optional custom ReMe YAML config path
    "vector_weight": 0.0,  # 0.0 = BM25 baseline
    "memory_adapter": "reme", # reme / off；off 用于无记忆对照实验
    "memory_model": "none", # 当前仅作为检索实验标签记录
    "keep_workspaces": False,

    # Output and reproducibility.  Empty run_id creates a UTC timestamp ID.
    "output_dir": "E:\\LRZ_Workplace\\fork\\memory_eval_pipeline\\results",  #输出目录
    "run_id": "", #run_id
    "baseline_run": None,  # 基线运行目录，用于对比性能

    # Answer API settings.  API key/base URL/model are read from .env by
    # default.  Set the *_model or *_base_url values only when overriding it.
    "answer_api_key_env": "DEEPSEEK_API_KEY",
    "answer_base_url_env": "DEEPSEEK_BASE_URL",
    "answer_model_env": "DEEPSEEK_MODEL",
    "answer_base_url": None,
    "answer_model": None,
    "answer_llm_adapter": "openai-compatible",
    "answer_max_tokens": 8192,
    "answer_temperature": 0.0,
    "answer_timeout": 120.0,
    "answer_retries": 3,
    "answer_workers": 4,
    "answer_cache_hit_input_price": None,
    "answer_cache_miss_input_price": None,
    "answer_output_price": None,
    "answer_price_multiplier": 1.0,

    # Judge API settings.  They default to the same DeepSeek endpoint as
    # Answer, but can be changed independently.
    "judge_api_key_env": "DEEPSEEK_API_KEY",
    "judge_base_url_env": "DEEPSEEK_BASE_URL",
    "judge_model_env": "DEEPSEEK_MODEL",
    "judge_base_url": None,
    "judge_model": None,
    "judge_llm_adapter": "openai-compatible",
    "judge_max_tokens": 8192,
    "judge_temperature": 0.0,
    "judge_timeout": 120.0,
    "judge_retries": 3,
    "judge_workers": 4,
    "judge_cache_hit_input_price": None,
    "judge_cache_miss_input_price": None,
    "judge_output_price": None,
    "judge_price_multiplier": 1.0,
}


def _add_option(command: list[str], flag: str, value: Any) -> None:
    """Append one CLI option, omitting only values intentionally left blank."""

    if value is None:
        return
    if isinstance(value, bool):
        if value:
            command.append(flag)
        return
    if value == "":
        return
    command.extend([flag, str(value)])


def _looks_like_dataset_path(value: Any) -> bool:
    if isinstance(value, Path):
        return True
    if not isinstance(value, str):
        return False
    text = value.strip()
    return (
        text.lower().endswith((".json", ".jsonl"))
        or "\\" in text
        or "/" in text
    )


def build_command(config: dict[str, Any]) -> list[str]:
    """Build the existing end-to-end runner command from ``CONFIG``."""

    command = [sys.executable, str(END_TO_END_RUNNER)]
    dataset_value = config.get("dataset")
    dataset_flag = "--data" if _looks_like_dataset_path(dataset_value) else "--dataset"
    _add_option(command, dataset_flag, dataset_value)

    option_map = (
        ("--cases", "cases"),
        ("--dataset-adapter", "dataset_adapter"),
        ("--start", "start"),
        ("--top-k", "top_k"),
        ("--search-multiplier", "search_multiplier"),
        ("--min-score", "min_score"),
        ("--seed", "seed"),
        ("--base-port", "base_port"),
        ("--startup-timeout", "startup_timeout"),
        ("--reme-cmd", "reme_cmd"),
        ("--reme-config", "reme_config"),
        ("--memory-adapter", "memory_adapter"),
        ("--memory-model", "memory_model"),
        ("--vector-weight", "vector_weight"),
        ("--retrieval-workers", "retrieval_workers"),
        ("--output-dir", "output_dir"),
        ("--run-id", "run_id"),
        ("--baseline-run", "baseline_run"),
        ("--answer-api-key-env", "answer_api_key_env"),
        ("--answer-base-url-env", "answer_base_url_env"),
        ("--answer-model-env", "answer_model_env"),
        ("--answer-base-url", "answer_base_url"),
        ("--answer-model", "answer_model"),
        ("--answer-llm-adapter", "answer_llm_adapter"),
        ("--answer-max-tokens", "answer_max_tokens"),
        ("--answer-temperature", "answer_temperature"),
        ("--answer-timeout", "answer_timeout"),
        ("--answer-retries", "answer_retries"),
        ("--answer-workers", "answer_workers"),
        ("--answer-cache-hit-input-price", "answer_cache_hit_input_price"),
        ("--answer-cache-miss-input-price", "answer_cache_miss_input_price"),
        ("--answer-output-price", "answer_output_price"),
        ("--answer-price-multiplier", "answer_price_multiplier"),
        ("--judge-api-key-env", "judge_api_key_env"),
        ("--judge-base-url-env", "judge_base_url_env"),
        ("--judge-model-env", "judge_model_env"),
        ("--judge-base-url", "judge_base_url"),
        ("--judge-model", "judge_model"),
        ("--judge-llm-adapter", "judge_llm_adapter"),
        ("--judge-max-tokens", "judge_max_tokens"),
        ("--judge-temperature", "judge_temperature"),
        ("--judge-timeout", "judge_timeout"),
        ("--judge-retries", "judge_retries"),
        ("--judge-workers", "judge_workers"),
        ("--judge-cache-hit-input-price", "judge_cache_hit_input_price"),
        ("--judge-cache-miss-input-price", "judge_cache_miss_input_price"),
        ("--judge-output-price", "judge_output_price"),
        ("--judge-price-multiplier", "judge_price_multiplier"),
    )
    for flag, key in option_map:
        _add_option(command, flag, config.get(key))

    if config.get("shuffle"):
        command.append("--shuffle")
    if config.get("keep_workspaces"):
        command.append("--keep-workspaces")
    return command


def _validate_config(config: dict[str, Any]) -> None:
    dataset_value = config.get("dataset")
    if dataset_value is None or str(dataset_value).strip() == "":
        raise ValueError("dataset must be a dataset path or registered dataset ID")
    if _looks_like_dataset_path(dataset_value):
        dataset_path = Path(str(dataset_value))
        if not dataset_path.is_absolute():
            dataset_path = REPO_ROOT / dataset_path
        if not dataset_path.is_file():
            raise FileNotFoundError(f"Dataset file not found: {dataset_path.resolve()}")
    for key in ("cases", "start", "top_k", "search_multiplier", "retrieval_workers", "answer_workers", "judge_workers"):
        value = config.get(key)
        if not isinstance(value, int) or isinstance(value, bool):
            raise ValueError(f"{key} must be an integer")
    if config["cases"] < 0 or config["start"] < 0:
        raise ValueError("cases and start must be non-negative")
    if config["top_k"] < 1 or config["search_multiplier"] < 1:
        raise ValueError("top_k and search_multiplier must be positive")
    for key in ("retrieval_workers", "answer_workers", "judge_workers"):
        if config[key] < 1:
            raise ValueError(f"{key} must be positive")
    if not END_TO_END_RUNNER.is_file():
        raise FileNotFoundError(f"End-to-end runner not found: {END_TO_END_RUNNER}")


def main() -> int:
    _validate_config(CONFIG)
    command = build_command(CONFIG)
    print(f"工作目录: {REPO_ROOT}", flush=True)
    print("即将运行:", flush=True)
    print("  " + shlex.join(command), flush=True)
    print("API key 不在脚本中，Answer/Judge 将从 .env 或环境变量读取。", flush=True)
    completed = subprocess.run(command, cwd=str(REPO_ROOT), check=False)
    print(f"Eval exit code: {completed.returncode}", flush=True)
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
