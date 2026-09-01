"""Common LLM adapter contract."""

from __future__ import annotations

from typing import Any, Protocol


class LLMRequestError(RuntimeError):
    """Final model failure with retry diagnostics safe for eval traces."""

    def __init__(self, message: str, *, attempts: int, http_status: int | None, category: str):
        super().__init__(message)
        self.attempts = attempts
        self.http_status = http_status
        self.category = category


class LLMAdapter(Protocol):
    """Generate one completion while preserving raw usage metadata."""

    name: str
    model: str
    base_url: str

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
        ...

