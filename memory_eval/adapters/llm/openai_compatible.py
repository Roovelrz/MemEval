"""Dependency-free OpenAI-compatible chat-completions adapter."""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from .base import LLMRequestError


LOCAL_ENV_PATH = Path(__file__).resolve().parents[3] / ".env"


def load_local_env(path: Path = LOCAL_ENV_PATH) -> None:
    """Load simple KEY=VALUE entries without overriding process variables."""

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


def resolve_endpoint(
    *,
    api_key: str | None,
    api_key_env: str,
    base_url: str | None,
    base_url_env: str,
    model: str | None,
    model_env: str,
) -> tuple[str, str, str, bool]:
    load_local_env()
    resolved_key = api_key or os.environ.get(api_key_env, "")
    resolved_base = (base_url or os.environ.get(base_url_env, "")).rstrip("/")
    resolved_model = model or os.environ.get(model_env, "")
    missing = [
        label
        for label, value in (
            (api_key_env, resolved_key),
            (base_url_env, resolved_base),
            (model_env, resolved_model),
        )
        if not value
    ]
    if missing:
        raise ValueError(f"Missing LLM configuration: {', '.join(missing)}")
    return resolved_key, resolved_base, resolved_model, bool(resolved_key)


class OpenAICompatibleLLMAdapter:
    name = "openai-compatible"

    def __init__(self, *, api_key: str, base_url: str, model: str) -> None:
        if not api_key or not base_url or not model:
            raise ValueError("OpenAI-compatible adapter requires api_key, base_url, and model")
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model

    def complete(
        self,
        *,
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
                self.base_url + "/chat/completions",
                data=json.dumps(
                    {
                        "model": self.model,
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": temperature,
                        "max_tokens": current_max_tokens,
                    },
                    ensure_ascii=False,
                ).encode("utf-8"),
                headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
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
            except TimeoutError as exc:
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

