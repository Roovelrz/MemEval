"""Common LLM adapter contract.

LLM Adapter 是 Eval 框架与模型服务之间的协议层，Answer 与 Judge 共用同一
协议、各自持有实例（可以指向不同模型/端点）。实现负责：请求、错误归类、
重试，以及把 provider 的 usage 原始数据透传给上层做成本核算。
"""

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

