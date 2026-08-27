"""Judge generated answers against gold answers with an LLM endpoint.

The judge is intentionally a separate process from answer generation.  It
consumes the same prepared cases plus an answers JSONL, writes one score row
per case, and can resume an interrupted run.
"""

from __future__ import annotations

import argparse
import json
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:  # works both as ``python scripts/run_judge_eval.py`` and as a package import
    from scripts.llm_eval_common import (
        JUDGE_PROMPT_SHA256,
        JUDGE_PROMPT_VERSION,
        LLMRequestError,
        calculate_usage_cost,
        complete,
        parse_judge_label,
        percentile,
        read_jsonl,
        render_accuracy_prompt,
        resolve_model_pricing,
        resolve_endpoint,
        row_id,
        summarize_token_usage,
        text_sha256,
        write_jsonl,
    )
except ModuleNotFoundError:  # pragma: no cover - direct script execution path
    from llm_eval_common import (
        JUDGE_PROMPT_SHA256,
        JUDGE_PROMPT_VERSION,
        LLMRequestError,
        calculate_usage_cost,
        complete,
        parse_judge_label,
        percentile,
        read_jsonl,
        render_accuracy_prompt,
        resolve_model_pricing,
        resolve_endpoint,
        row_id,
        summarize_token_usage,
        text_sha256,
        write_jsonl,
    )


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = REPO_ROOT / "results" / "reme_retrieval" / "reme-baseline-20" / "prepared.jsonl"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Judge generated memory-eval answers")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT, help="prepared.jsonl with questions and gold answers")
    parser.add_argument("--answers", type=Path, required=True, help="answers JSONL from run_answer_eval.py")
    parser.add_argument("--output", type=Path, required=True, help="scores JSONL output")
    parser.add_argument("--failures", type=Path, default=None, help="failure JSONL (default: judge_failures.jsonl beside output)")
    parser.add_argument("--api-key-env", default="DEEPSEEK_API_KEY")
    parser.add_argument("--base-url-env", default="DEEPSEEK_BASE_URL")
    parser.add_argument("--model-env", default="DEEPSEEK_MODEL")
    parser.add_argument("--api-key", default=None, help="optional direct key; prefer --api-key-env")
    parser.add_argument("--base-url", default=None)
    parser.add_argument("--model", default=None)
    parser.add_argument("--max-tokens", type=int, default=4096)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--timeout", type=float, default=120.0)
    parser.add_argument("--retries", type=int, default=3)
    parser.add_argument("--retry-backoff", type=float, default=1.0)
    parser.add_argument("--cache-hit-input-price", type=float, default=None, help="USD per 1M tokens")
    parser.add_argument("--cache-miss-input-price", type=float, default=None, help="USD per 1M tokens")
    parser.add_argument("--output-price", type=float, default=None, help="USD per 1M tokens")
    parser.add_argument("--price-multiplier", type=float, default=1.0, help="Multiplier for peak pricing or account-specific rates")
    parser.add_argument("--start", type=int, default=0)
    parser.add_argument("--limit", type=int, default=0, help="0 means all selected rows")
    parser.add_argument("--workers", type=int, default=1, help="Concurrent API requests; 1 preserves sequential behavior")
    parser.add_argument("--overwrite", action="store_true", help="replace existing output instead of resuming")
    return parser.parse_args()


def _existing_rows(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return read_jsonl(path)


def _answer_map(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for row in read_jsonl(path):
        ident = row_id(row)
        if "generated_answer" not in row:
            raise ValueError(f"Answer row {ident} has no generated_answer")
        if ident in values:
            raise ValueError(f"Duplicate answer ID: {ident}")
        values[ident] = str(row["generated_answer"])
    return values


def _safe_name(value: str) -> str:
    cleaned = "".join(char if char.isalnum() or char in "._-" else "_" for char in value)
    return cleaned.strip("._") or "unnamed"


def run(args: argparse.Namespace) -> int:
    run_started_at = datetime.now(timezone.utc)
    if args.start < 0 or args.limit < 0:
        raise ValueError("--start and --limit must be non-negative")
    if args.max_tokens < 1 or args.timeout <= 0 or args.retries < 0 or args.retry_backoff < 0:
        raise ValueError("max tokens, timeout, and retry settings are invalid")
    workers = int(getattr(args, "workers", 1))
    if workers < 1:
        raise ValueError("--workers must be positive")

    input_path = args.input.resolve()
    answer_path = args.answers.resolve()
    items = read_jsonl(input_path)
    answers = _answer_map(answer_path)
    selected = items[args.start:]
    if args.limit:
        selected = selected[: args.limit]
    if not selected:
        raise ValueError("No input rows selected")
    selected_ids = {row_id(item) for item in selected}
    missing_answers = sorted(selected_ids - set(answers))
    if missing_answers:
        raise ValueError(f"Missing generated answers for {len(missing_answers)} selected IDs: {missing_answers[:5]}")

    api_key, base_url, model, key_configured = resolve_endpoint(
        api_key=args.api_key,
        api_key_env=args.api_key_env,
        base_url=args.base_url,
        base_url_env=args.base_url_env,
        model=args.model,
        model_env=args.model_env,
    )
    pricing = resolve_model_pricing(
        model,
        cache_hit_input=getattr(args, "cache_hit_input_price", None),
        cache_miss_input=getattr(args, "cache_miss_input_price", None),
        output=getattr(args, "output_price", None),
        multiplier=getattr(args, "price_multiplier", 1.0),
    )
    output_path = args.output.resolve()
    failure_path = (args.failures or output_path.with_name("judge_failures.jsonl")).resolve()
    api_error_path = output_path.with_name("api_errors.jsonl")
    prompt_dir = output_path.parent / "judge_prompts"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    prompt_dir.mkdir(parents=True, exist_ok=True)
    if args.overwrite:
        for path in (output_path, failure_path):
            if path.exists():
                path.unlink()
    failure_path.touch(exist_ok=True)
    api_error_path.touch(exist_ok=True)
    existing_rows = _existing_rows(output_path)
    done = {row_id(row) for row in existing_rows}
    existing_correct = {
        row_id(row): bool(row.get("is_correct"))
        for row in existing_rows
        if "is_correct" in row
    }

    config = {
        "task": "judge",
        "input": str(input_path),
        "answers": str(answer_path),
        "output": str(output_path),
        "failures": str(failure_path),
        "api_key_env": args.api_key_env,
        "api_key_configured": key_configured,
        "base_url_env": args.base_url_env,
        "base_url": base_url,
        "model_env": args.model_env,
        "model": model,
        "max_tokens": args.max_tokens,
        "temperature": args.temperature,
        "timeout": args.timeout,
        "retries": args.retries,
        "prompt_version": JUDGE_PROMPT_VERSION,
        "prompt_template_sha256": JUDGE_PROMPT_SHA256,
        "prompt_artifact_dir": str(prompt_dir),
        "pricing": pricing or "NOT_RECORDED",
        "start": args.start,
        "limit": args.limit,
        "workers": workers,
        "start_time_utc": run_started_at.isoformat(),
    }
    (output_path.parent / "judge_run_config.json").write_text(
        json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    successes = 0
    failures = 0
    correct = 0
    total = len(selected)

    def process(pair: tuple[int, dict[str, Any]]) -> tuple[int, str, dict[str, Any] | None, dict[str, Any] | None]:
        index, item = pair
        ident = row_id(item)
        started = time.perf_counter()
        raw_response = ""
        print(f"[{index}/{total}] id={ident} started", flush=True)
        prompt = render_accuracy_prompt(item, answers[ident])
        prompt_path = prompt_dir / f"{_safe_name(ident)}.txt"
        prompt_path.write_text(prompt, encoding="utf-8", newline="")
        try:
            raw_response, usage = complete(
                api_key=api_key,
                base_url=base_url,
                model=model,
                prompt=prompt,
                max_tokens=args.max_tokens,
                temperature=args.temperature,
                timeout=args.timeout,
                retries=args.retries,
                retry_backoff=args.retry_backoff,
            )
            request_cost = calculate_usage_cost(usage, pricing)
            if request_cost is not None:
                usage["cost"] = request_cost
            label = parse_judge_label(raw_response)
            is_correct = label == "CORRECT"
            return index, ident, {
                "id": ident,
                "label": label,
                "is_correct": is_correct,
                "judge_response": raw_response,
                "model": model,
                "latency_ms": (time.perf_counter() - started) * 1000,
                "usage": usage,
                "prompt_version": JUDGE_PROMPT_VERSION,
                "prompt_sha256": text_sha256(prompt),
                "prompt_file": str(prompt_path),
                "prompt_characters": len(prompt),
            }, None
        except Exception as exc:
            latency_ms = (time.perf_counter() - started) * 1000
            failure = {
                "id": ident,
                "stage": "judge",
                "error_type": type(exc).__name__,
                "error": str(exc),
                "judge_response": raw_response,
                "latency_ms": latency_ms,
                "prompt_file": str(prompt_path),
                "prompt_sha256": text_sha256(prompt),
            }
            if isinstance(exc, LLMRequestError):
                failure.update(
                    {
                        "api_category": exc.category,
                        "request_attempts": exc.attempts,
                        "retry_count": max(0, exc.attempts - 1),
                        "http_status": exc.http_status,
                    }
                )
            return index, ident, None, failure

    pending: list[tuple[int, dict[str, Any]]] = []
    for index, item in enumerate(selected, start=1):
        ident = row_id(item)
        if ident in done:
            print(f"[{index}/{total}] id={ident} skipped (already in output)", flush=True)
            successes += 1
            correct += int(existing_correct.get(ident, False))
        else:
            pending.append((index, item))

    if workers == 1:
        completed = map(process, pending)
        executor = None
    else:
        executor = ThreadPoolExecutor(max_workers=workers, thread_name_prefix="judge")
        completed = executor.map(process, pending)
    try:
        for index, ident, result, failure in completed:
            if result is not None:
                write_jsonl(output_path, [result], append=True)
                successes += 1
                correct += int(result["is_correct"])
                print(f"[{index}/{total}] id={ident} completed", flush=True)
            else:
                assert failure is not None
                write_jsonl(failure_path, [failure], append=True)
                if failure.get("api_category"):
                    write_jsonl(api_error_path, [failure], append=True)
                failures += 1
                print(
                    f"[{index}/{total}] id={ident} FAILED: "
                    f"{failure['error_type']}: {failure['error']}",
                    flush=True,
                )
    finally:
        if executor is not None:
            executor.shutdown(wait=True)

    selected_id_set = {row_id(item) for item in selected}
    result_rows = [
        row for row in (read_jsonl(output_path) if output_path.is_file() else [])
        if row_id(row) in selected_id_set
    ]
    failure_rows = [row for row in read_jsonl(failure_path) if row_id(row) in selected_id_set]
    latencies = [float(row["latency_ms"]) for row in result_rows if isinstance(row.get("latency_ms"), (int, float))]
    request_attempts = sum(int(row.get("usage", {}).get("request_attempts", 1)) for row in result_rows)
    retry_count = sum(int(row.get("usage", {}).get("retry_count", 0)) for row in result_rows)
    token_usage = summarize_token_usage(
        [row.get("usage", {}) for row in result_rows if isinstance(row.get("usage"), dict)],
        pricing,
    )
    run_finished_at = datetime.now(timezone.utc)
    summary = {
        "task": "judge",
        "input": str(input_path),
        "answers": str(answer_path),
        "requested_rows": total,
        "successful_rows": successes,
        "failed_rows": failures,
        "correct_rows": correct,
        "accuracy": correct / successes if successes else None,
        "success_rate": successes / total if total else None,
        "failure_rate": failures / total if total else None,
        "correct_count": sum(row.get("label") == "CORRECT" for row in result_rows),
        "wrong_count": sum(row.get("label") == "WRONG" for row in result_rows),
        "parse_failure_count": sum(row.get("error_type") == "ValueError" for row in failure_rows),
        "timeout_count": sum(row.get("api_category") == "timeout" for row in failure_rows),
        "api_request_count": request_attempts + sum(int(row.get("request_attempts", 0)) for row in failure_rows),
        "retry_count": retry_count + sum(int(row.get("retry_count", 0)) for row in failure_rows),
        "latency_ms": {
            "avg": sum(latencies) / len(latencies) if latencies else None,
            "p50": percentile(latencies, 0.50),
            "p95": percentile(latencies, 0.95),
            "p99": percentile(latencies, 0.99),
        },
        "token_usage": token_usage,
        "pricing": pricing or "NOT_RECORDED",
        "output": str(output_path),
        "failures": str(failure_path),
        "model": model,
        "workers": workers,
        "prompt_version": JUDGE_PROMPT_VERSION,
        "prompt_template_sha256": JUDGE_PROMPT_SHA256,
        "human_review_count": 0,
        "judge_human_disagreement_rate": "NOT_RECORDED",
        "start_time_utc": run_started_at.isoformat(),
        "end_time_utc": run_finished_at.isoformat(),
    }
    (output_path.parent / "judge_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if failures == 0 else 2


if __name__ == "__main__":
    raise SystemExit(run(parse_args()))
