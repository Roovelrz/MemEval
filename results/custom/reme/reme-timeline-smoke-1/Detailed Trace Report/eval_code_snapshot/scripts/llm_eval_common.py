"""Shared, dependency-light helpers for the Answer and Judge runners.

The runners use an OpenAI-compatible HTTP endpoint directly.  Credentials are
resolved from environment variables and are never written to run artifacts.
"""

from __future__ import annotations

import json
import hashlib
import re
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


LOCAL_ENV_PATH = Path(__file__).resolve().parents[1] / ".env"
ANSWER_PROMPT_VERSION = "longmemeval-answer-v2-structured-time"
JUDGE_PROMPT_VERSION = "longmemeval-judge-v1"

DEEPSEEK_PRICING_SOURCE = "https://api-docs.deepseek.com/quick_start/pricing"
MODEL_PRICING_USD_PER_MILLION: dict[str, dict[str, Any]] = {
    "deepseek-v4-flash": {
        "cache_hit_input": 0.0028,
        "cache_miss_input": 0.14,
        "output": 0.28,
        "source": DEEPSEEK_PRICING_SOURCE,
        "observed_date": "2026-08-26",
    }
}


def load_local_env(path: Path = LOCAL_ENV_PATH) -> None:
    """Load simple KEY=VALUE entries without overriding process variables."""
    import os

    if not path.is_file():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, value = line.split("=", 1)
        name = name.strip()
        value = value.strip().strip('"').strip("'")
        if name and name not in os.environ:
            os.environ[name] = value


OPEN_ENDED_ANSWER_TEMPLATE = """You are asked to answer a question based on your memories of a conversation.

<instructions>
1. Use only the provided memories. Prefer the memory that answers the question most directly.
2. Your memories are episodic raw observations. Reason about what they imply. Do not refuse just because the answer is not stated verbatim.
3. The question may contain typos. Match it to the most relevant memory even if the wording differs.
4. When multiple answers are possible, list all supported answers, not just the first.
5. For counts or time intervals, enumerate carefully before answering.
6. Preserve specific names, titles, places, and labels from the memories. Use "Rob" not "a colleague", "Sweden" not "home country".
7. Each memory has a session timestamp. Use it together with the question date to resolve elapsed-time and temporal-order questions. Convert relative times like "yesterday", "last month", and "last year" only when those timestamps make the answer clear. Keep week-based expressions relative.
8. If memories conflict, prefer the most recent supported memory.
9. For list questions, include all required items and no extras.
10. Keep the final answer minimal. Do not add explanation, background, or extra dates unless needed for correctness.
</instructions>

<memories>
Memories for user {{speaker_1_name}}:

{{speaker_1_memories}}

Memories for user {{speaker_2_name}}:

{{speaker_2_memories}}
</memories>

Question date: {{question_date}}
Question: {{question}}
Answer with the shortest correct phrase or sentence. No preamble, no fluff:"""


ACCURACY_PROMPT = """Your task is to label an answer as ’CORRECT’ or ’WRONG’ given:
(1) a question,
(2) a gold (ground truth) answer,
(3) a generated answer.

Core principle — Inclusion + Non-contradiction
- Be GENEROUS: if the generated answer clearly includes the gold’s key content (or a clear paraphrase of the same content) and does not contradict it, mark CORRECT — even if extra details are added.
- Mark WRONG only when the generated answer does not include the gold’s content, changes it, or contradicts it.

TIME (strict granularity; relative form equivalence; no calendar math)
- Granularity must match exactly: HOUR↔HOUR, DAY↔DAY, MONTH↔MONTH, YEAR↔YEAR.
  Do not answer a gold at a different time unit — even if the numeric value overlaps. Do not answer a month-level gold with a specific day, nor a year with a specific month/day/hour, etc.
  (e.g., gold = "July 26, 2019" [DAY]; generated = "2019-07-26 08:09:17" [includes Second] → WRONG)
- Do NOT convert relative ↔ absolute. If the gold uses a relative time expression, the generated answer must also use a relative form (or a clear paraphrase of that same form), not a computed date/range.
- Treat harmless modifiers in relative forms (e.g., “the/last/previous/just prior”) as equivalent when both the anchor date and the time unit are the same.

- Lists of DISTINCT facts:
- If the gold answer lists multiple distinct facts (joined by "and", commas, or slashes), the generated answer must cover all of them.
- Extra non-contradictory items generally count as WRONG.
    - Example: gold = A, B, C ; gen = A, B, C → CORRECT
    - Example: gold = A, B, C ; gen = A, B, C, D → WRONG
- Exception: If a gold element is elaborated or split into finer details in the generated answer (e.g., C → C, C′), it is still considered CORRECT.

Preference/Benefit Questions (e.g., "what X likes/values most")
- If gold lists multiple reasons/aspects, the generated answer only needs to include any one of them without contradiction to be CORRECT.

Now it's time for the real question:
Question: {question}
Gold answer: {gold_answer}
Generated answer: {generated_answer}

First, provide a short (one sentence) explanation of your reasoning, then finish with CORRECT or WRONG.
Do NOT include both CORRECT and WRONG in your response, or it will break the evaluation script.

Just return the label CORRECT or WRONG in a json format with the key as "label":

```json
{{
    "label": "CORRECT" or "WRONG"
}}
```"""


def text_sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


ANSWER_PROMPT_SHA256 = text_sha256(OPEN_ENDED_ANSWER_TEMPLATE)
JUDGE_PROMPT_SHA256 = text_sha256(ACCURACY_PROMPT)


def percentile(values: list[float], quantile: float) -> float | None:
    usable = sorted(values)
    if not usable:
        return None
    position = (len(usable) - 1) * quantile
    lower = int(position)
    upper = min(lower + 1, len(usable) - 1)
    fraction = position - lower
    return usable[lower] + (usable[upper] - usable[lower]) * fraction


def resolve_model_pricing(
    model: str,
    *,
    cache_hit_input: float | None = None,
    cache_miss_input: float | None = None,
    output: float | None = None,
    multiplier: float = 1.0,
) -> dict[str, Any] | None:
    """Resolve auditable USD-per-million-token rates for one model.

    Known-model defaults are deliberately small and explicit. Unknown models
    require all three rates, so a partial override cannot silently undercount.
    """

    if multiplier <= 0:
        raise ValueError("price multiplier must be positive")
    configured = MODEL_PRICING_USD_PER_MILLION.get(model.strip().lower())
    overrides = (cache_hit_input, cache_miss_input, output)
    if configured is None and all(value is None for value in overrides):
        return None
    if configured is None and any(value is None for value in overrides):
        raise ValueError("unknown model pricing requires cache-hit, cache-miss, and output rates")

    resolved = dict(configured or {})
    for name, value in (
        ("cache_hit_input", cache_hit_input),
        ("cache_miss_input", cache_miss_input),
        ("output", output),
    ):
        if value is not None:
            if value < 0:
                raise ValueError("token prices must be non-negative")
            resolved[name] = float(value)
    resolved.update(
        {
            "model": model,
            "currency": "USD",
            "unit_tokens": 1_000_000,
            "multiplier": float(multiplier),
            "source": resolved.get("source", "CLI_OVERRIDE"),
            "observed_date": resolved.get("observed_date", "USER_SUPPLIED"),
        }
    )
    return resolved


def calculate_usage_cost(usage: dict[str, Any], pricing: dict[str, Any] | None) -> dict[str, Any] | None:
    """Calculate one request's cost, billing unclassified input as cache miss."""

    if pricing is None:
        return None
    input_tokens = int(usage.get("prompt_tokens", usage.get("input_tokens", 0)) or 0)
    output_tokens = int(usage.get("completion_tokens", usage.get("output_tokens", 0)) or 0)
    cache_hit_tokens = int(usage.get("prompt_cache_hit_tokens", 0) or 0)
    raw_cache_miss = usage.get("prompt_cache_miss_tokens")
    cache_miss_tokens = (
        int(raw_cache_miss or 0)
        if raw_cache_miss is not None
        else max(0, input_tokens - cache_hit_tokens)
    )
    classified_input = cache_hit_tokens + cache_miss_tokens
    if classified_input < input_tokens:
        cache_miss_tokens += input_tokens - classified_input
    input_tokens = max(input_tokens, cache_hit_tokens + cache_miss_tokens)

    divisor = float(pricing["unit_tokens"])
    multiplier = float(pricing.get("multiplier", 1.0))
    hit_cost = cache_hit_tokens * float(pricing["cache_hit_input"]) * multiplier / divisor
    miss_cost = cache_miss_tokens * float(pricing["cache_miss_input"]) * multiplier / divisor
    output_cost = output_tokens * float(pricing["output"]) * multiplier / divisor
    return {
        "currency": "USD",
        "input_tokens": input_tokens,
        "cache_hit_input_tokens": cache_hit_tokens,
        "cache_miss_input_tokens": cache_miss_tokens,
        "output_tokens": output_tokens,
        "cache_hit_input_cost_usd": hit_cost,
        "cache_miss_input_cost_usd": miss_cost,
        "output_cost_usd": output_cost,
        "total_cost_usd": hit_cost + miss_cost + output_cost,
    }


def summarize_token_usage(
    usages: list[dict[str, Any]], pricing: dict[str, Any] | None
) -> dict[str, Any]:
    costs = [calculate_usage_cost(usage, pricing) for usage in usages]
    recorded_costs = [cost for cost in costs if cost is not None]
    input_tokens = sum(int(usage.get("prompt_tokens", usage.get("input_tokens", 0)) or 0) for usage in usages)
    output_tokens = sum(int(usage.get("completion_tokens", usage.get("output_tokens", 0)) or 0) for usage in usages)
    cache_hit_tokens = sum(int(usage.get("prompt_cache_hit_tokens", 0) or 0) for usage in usages)
    cache_miss_tokens = sum(
        int(usage.get("prompt_cache_miss_tokens", 0) or 0)
        if usage.get("prompt_cache_miss_tokens") is not None
        else max(
            0,
            int(usage.get("prompt_tokens", usage.get("input_tokens", 0)) or 0)
            - int(usage.get("prompt_cache_hit_tokens", 0) or 0),
        )
        for usage in usages
    )
    return {
        "input_tokens": input_tokens,
        "cache_hit_input_tokens": cache_hit_tokens,
        "cache_miss_input_tokens": cache_miss_tokens,
        "output_tokens": output_tokens,
        "total_tokens": sum(
            int(usage.get("total_tokens") or 0)
            or int(usage.get("prompt_tokens", usage.get("input_tokens", 0)) or 0)
            + int(usage.get("completion_tokens", usage.get("output_tokens", 0)) or 0)
            for usage in usages
        ),
        "cost_usd": (
            sum(float(cost["total_cost_usd"]) for cost in recorded_costs)
            if pricing is not None
            else "NOT_RECORDED"
        ),
        "pricing": pricing or "NOT_RECORDED",
    }


class LLMRequestError(RuntimeError):
    """Final API failure with retry diagnostics safe to persist in eval traces."""

    def __init__(self, message: str, *, attempts: int, http_status: int | None, category: str):
        super().__init__(message)
        self.attempts = attempts
        self.http_status = http_status
        self.category = category


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSONL at {path}:{line_number}: {exc}") from exc
        if not isinstance(value, dict):
            raise ValueError(f"JSONL row at {path}:{line_number} must be an object")
        rows.append(value)
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]], append: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    mode = "a" if append else "w"
    with path.open(mode, encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def reconcile_failure_rows(path: Path, successful_ids: set[str]) -> list[dict[str, Any]]:
    """Keep only unresolved failures after a resumable stage succeeds."""

    rows = read_jsonl(path) if path.is_file() else []
    unresolved = [row for row in rows if row_id(row) not in successful_ids]
    if unresolved != rows:
        write_jsonl(path, unresolved)
    return unresolved


def row_id(row: dict[str, Any]) -> str:
    value = row.get("id", row.get("case_id"))
    if value is None or str(value).strip() == "":
        raise ValueError("Every row needs an 'id' or 'case_id'")
    return str(value)


def memory_text(value: object) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return "\n".join(memory_text(item) for item in value)
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False)
    return str(value or "")


def render_answer_prompt(item: dict[str, Any]) -> str:
    fallback_memories = item.get("retrieved_context", item.get("memories", ""))
    values = {
        "speaker_1_name": item.get("speaker_1_name", "speaker 1"),
        "speaker_1_memories": item.get("speaker_1_memories", fallback_memories),
        "speaker_2_name": item.get("speaker_2_name", "speaker 2"),
        "speaker_2_memories": item.get("speaker_2_memories", ""),
        "question_date": item.get("question_date", "NOT_RECORDED"),
        "question": item.get("question", item.get("query", "")),
    }
    return re.sub(
        r"\{\{(speaker_1_name|speaker_1_memories|speaker_2_name|speaker_2_memories|question_date|question)\}\}",
        lambda match: memory_text(values[match.group(1)]),
        OPEN_ENDED_ANSWER_TEMPLATE,
    )


def gold_answer(item: dict[str, Any]) -> str:
    for key in ("gold_answer", "golden_answer", "reference_answer", "correct_answer", "answer"):
        if key in item:
            return memory_text(item[key])
    raise ValueError(f"record {row_id(item)} has no gold answer")


def render_accuracy_prompt(item: dict[str, Any], generated_answer: str) -> str:
    values = {
        "question": memory_text(item.get("question", item.get("query", ""))),
        "gold_answer": gold_answer(item),
        "generated_answer": generated_answer,
    }
    return re.sub(
        r"\{(question|gold_answer|generated_answer)\}",
        lambda match: values[match.group(1)],
        ACCURACY_PROMPT,
    )


def parse_judge_label(response: str) -> str:
    match = re.search(r"\{.*?\}", response, re.DOTALL)
    if match:
        try:
            payload = json.loads(match.group(0))
        except json.JSONDecodeError:
            payload = None
        if isinstance(payload, dict):
            label = str(payload.get("label", "")).upper()
            if label in {"CORRECT", "WRONG"}:
                return label

    # Some OpenAI-compatible reasoning models follow the semantic instruction
    # but return a bare label or one short explanatory sentence instead of the
    # requested JSON. Accept it only when exactly one unambiguous label occurs.
    labels = set(re.findall(r"\b(CORRECT|WRONG)\b", response.upper()))
    if len(labels) == 1:
        return labels.pop()
    raise ValueError("judge response has no single unambiguous CORRECT/WRONG label")


def resolve_endpoint(
    *,
    api_key: str | None,
    api_key_env: str,
    base_url: str | None,
    base_url_env: str,
    model: str | None,
    model_env: str,
) -> tuple[str, str, str, bool]:
    import os

    load_local_env()
    resolved_key = api_key or os.environ.get(api_key_env, "")
    resolved_base = (base_url or os.environ.get(base_url_env, "")).rstrip("/")
    resolved_model = model or os.environ.get(model_env, "")
    missing = [
        label
        for label, value in ((api_key_env, resolved_key), (base_url_env, resolved_base), (model_env, resolved_model))
        if not value
    ]
    if missing:
        raise ValueError(f"Missing LLM configuration: {', '.join(missing)}")
    return resolved_key, resolved_base, resolved_model, bool(resolved_key)


def complete(
    *,
    api_key: str,
    base_url: str,
    model: str,
    prompt: str,
    max_tokens: int,
    temperature: float,
    timeout: float,
    retries: int,
    retry_backoff: float,
) -> tuple[str, dict[str, Any]]:
    last_error: Exception | None = None
    last_status: int | None = None
    last_category = "unknown"
    current_max_tokens = max_tokens
    max_attempts = retries + 1
    length_recovery_count = 0
    attempt = 0
    attempts_made = 0
    while attempt < max_attempts:
        attempts_made = attempt + 1
        request = urllib.request.Request(
            base_url + "/chat/completions",
            data=json.dumps(
                {
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": temperature,
                    "max_tokens": current_max_tokens,
                },
                ensure_ascii=False,
            ).encode("utf-8"),
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                last_status = int(getattr(response, "status", 200))
                payload = json.loads(response.read().decode("utf-8"))
            choices = payload.get("choices") if isinstance(payload, dict) else None
            if not isinstance(choices, list) or not choices or not isinstance(choices[0], dict):
                raise ValueError("LLM response has no choices[0]")
            message = choices[0].get("message", {})
            if not isinstance(message, dict):
                raise ValueError("LLM response message is not an object")
            content = message.get("content")
            if isinstance(content, list):
                content = "".join(
                    str(block.get("text", "")) if isinstance(block, dict) else str(block)
                    for block in content
                )
            content = str(content or "").strip()
            if not content:
                reasoning = str(message.get("reasoning_content") or "")
                finish_reason = str(choices[0].get("finish_reason") or "unknown")
                attempted_max_tokens = current_max_tokens
                if finish_reason == "length" and current_max_tokens < 8192:
                    current_max_tokens = 8192
                    length_recovery_count += 1
                    max_attempts = max(max_attempts, attempt + 2)
                raise ValueError(
                    "LLM response content is empty "
                    f"(finish_reason={finish_reason}, reasoning_chars={len(reasoning)}, "
                    f"max_tokens={attempted_max_tokens})"
                )
            raw_usage = payload.get("usage", {})
            usage = dict(raw_usage) if isinstance(raw_usage, dict) else {}
            usage.update(
                {
                    "request_attempts": attempt + 1,
                    "retry_count": attempt,
                    "http_status": last_status,
                    "initial_max_tokens": max_tokens,
                    "final_max_tokens": current_max_tokens,
                    "length_recovery_count": length_recovery_count,
                }
            )
            return content, usage
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            last_error = RuntimeError(f"LLM HTTP {exc.code}: {detail[:500]}")
            last_status = exc.code
            last_category = "rate_limit" if exc.code == 429 else ("server_error" if exc.code >= 500 else "http_error")
            if exc.code not in {408, 409, 425, 429} and exc.code < 500:
                break
        except (TimeoutError,) as exc:
            last_error = exc
            last_category = "timeout"
        except urllib.error.URLError as exc:
            last_error = exc
            last_category = "connection_error"
        except (json.JSONDecodeError, ValueError) as exc:
            last_error = exc
            last_category = "invalid_response"
        if attempt + 1 < max_attempts:
            time.sleep(retry_backoff * (2**attempt))
        attempt += 1
    assert last_error is not None
    raise LLMRequestError(
        str(last_error),
        attempts=attempts_made,
        http_status=last_status,
        category=last_category,
    ) from last_error
