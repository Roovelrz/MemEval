"""Generate answers from retrieved memory contexts with an OpenAI-compatible API.

This is intentionally independent from AML and from the ReMe process.  It
consumes ``prepared.jsonl`` produced by a retrieval runner and can resume an
interrupted run by skipping IDs already present in the output file.
"""

from __future__ import annotations

import argparse
import json
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:  # works both as ``python scripts/run_answer_eval.py`` and as a package import
    from scripts.llm_eval_common import (
        ANSWER_PROMPT_SHA256,
        ANSWER_PROMPT_VERSION,
        LLMRequestError,
        complete,
        calculate_usage_cost,
        memory_text,
        percentile,
        read_jsonl,
        render_answer_prompt,
        resolve_model_pricing,
        resolve_endpoint,
        row_id,
        summarize_token_usage,
        text_sha256,
        write_jsonl,
    )
except ModuleNotFoundError:  # pragma: no cover - direct script execution path
    from llm_eval_common import (
        ANSWER_PROMPT_SHA256,
        ANSWER_PROMPT_VERSION,
        LLMRequestError,
        complete,
        calculate_usage_cost,
        memory_text,
        percentile,
        read_jsonl,
        render_answer_prompt,
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
    parser = argparse.ArgumentParser(description="Generate answers for prepared memory-eval cases")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT, help="prepared.jsonl from retrieval")
    parser.add_argument("--output", type=Path, required=True, help="answers JSONL output")
    parser.add_argument("--failures", type=Path, default=None, help="failure JSONL (default: answer_failures.jsonl beside output)")
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


def _existing_ids(path: Path) -> set[str]:
    if not path.exists():
        return set()
    return {row_id(row) for row in read_jsonl(path)}


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
    rows = read_jsonl(input_path)
    rows = rows[args.start:]
    if args.limit:
        rows = rows[: args.limit]
    if not rows:
        raise ValueError("No input rows selected")

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
    failure_path = (args.failures or output_path.with_name("answer_failures.jsonl")).resolve()
    api_error_path = output_path.with_name("api_errors.jsonl")
    prompt_dir = output_path.parent / "answer_prompts"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    prompt_dir.mkdir(parents=True, exist_ok=True)
    if args.overwrite:
        for path in (output_path, failure_path):
            if path.exists():
                path.unlink()
    failure_path.touch(exist_ok=True)
    api_error_path.touch(exist_ok=True)
    done = _existing_ids(output_path)

    config = {
        "task": "answer",
        "input": str(input_path),
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
        "prompt_version": ANSWER_PROMPT_VERSION,
        "prompt_template_sha256": ANSWER_PROMPT_SHA256,
        "prompt_artifact_dir": str(prompt_dir),
        "pricing": pricing or "NOT_RECORDED",
        "start": args.start,
        "limit": args.limit,
        "workers": workers,
        "start_time_utc": run_started_at.isoformat(),
    }
    (output_path.parent / "answer_run_config.json").write_text(
        json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    successes = 0
    failures = 0
    total = len(rows)

    def process(pair: tuple[int, dict[str, Any]]) -> tuple[int, str, dict[str, Any] | None, dict[str, Any] | None]:
        index, item = pair
        ident = row_id(item)
        started = time.perf_counter()
        print(f"[{index}/{total}] id={ident} started", flush=True)
        prompt = render_answer_prompt(item)
        prompt_path = prompt_dir / f"{_safe_name(ident)}.txt"
        prompt_path.write_text(prompt, encoding="utf-8", newline="")
        contexts = item.get("retrieved_context", [])
        if not isinstance(contexts, list):
            contexts = [contexts]
        context_text = memory_text(contexts)
        try:
            generated, usage = complete(
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
            return index, ident, {
                "id": ident,
                "generated_answer": generated,
                "model": model,
                "latency_ms": (time.perf_counter() - started) * 1000,
                "usage": usage,
                "prompt_version": ANSWER_PROMPT_VERSION,
                "prompt_sha256": text_sha256(prompt),
                "prompt_file": str(prompt_path),
                "prompt_characters": len(prompt),
                "context_characters": len(context_text),
                "context_token_estimate": (len(context_text) + 3) // 4,
                "client_truncation_occurred": False,
            }, None
        except Exception as exc:
            latency_ms = (time.perf_counter() - started) * 1000
            failure = {
                "id": ident,
                "stage": "answer",
                "error_type": type(exc).__name__,
                "error": str(exc),
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
    for index, item in enumerate(rows, start=1):
        ident = row_id(item)
        if ident in done:
            print(f"[{index}/{total}] id={ident} skipped (already in output)", flush=True)
            successes += 1
        else:
            pending.append((index, item))

    if workers == 1:
        completed = map(process, pending)
        executor = None
    else:
        executor = ThreadPoolExecutor(max_workers=workers, thread_name_prefix="answer")
        completed = executor.map(process, pending)
    try:
        for index, ident, result, failure in completed:
            if result is not None:
                write_jsonl(output_path, [result], append=True)
                successes += 1
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

    result_rows = [
        row for row in (read_jsonl(output_path) if output_path.is_file() else [])
        if row_id(row) in {row_id(item) for item in rows}
    ]
    failure_rows = [row for row in read_jsonl(failure_path) if row_id(row) in {row_id(item) for item in rows}]
    latencies = [float(row["latency_ms"]) for row in result_rows if isinstance(row.get("latency_ms"), (int, float))]
    request_attempts = sum(int(row.get("usage", {}).get("request_attempts", 1)) for row in result_rows)
    retry_count = sum(int(row.get("usage", {}).get("retry_count", 0)) for row in result_rows)
    token_usage = summarize_token_usage(
        [row.get("usage", {}) for row in result_rows if isinstance(row.get("usage"), dict)],
        pricing,
    )
    run_finished_at = datetime.now(timezone.utc)
    summary = {
        "task": "answer",
        "input": str(input_path),
        "requested_rows": total,
        "successful_rows": successes,
        "failed_rows": failures,
        "success_rate": successes / total if total else None,
        "failure_rate": failures / total if total else None,
        "empty_answer_count": sum(not str(row.get("generated_answer", "")).strip() for row in result_rows),
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
        "prompt_version": ANSWER_PROMPT_VERSION,
        "prompt_template_sha256": ANSWER_PROMPT_SHA256,
        "start_time_utc": run_started_at.isoformat(),
        "end_time_utc": run_finished_at.isoformat(),
    }
    (output_path.parent / "answer_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if failures == 0 else 2


if __name__ == "__main__":
    raise SystemExit(run(parse_args()))
