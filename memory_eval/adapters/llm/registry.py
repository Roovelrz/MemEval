"""LLM adapter registry."""

from __future__ import annotations

from .base import LLMAdapter
from .openai_compatible import OpenAICompatibleLLMAdapter


LLM_ADAPTERS = {
    "openai-compatible": OpenAICompatibleLLMAdapter,
}


def create_llm_adapter(name: str, *, api_key: str, base_url: str, model: str) -> LLMAdapter:
    selected = name.strip().lower()
    factory = LLM_ADAPTERS.get(selected)
    if factory is None:
        available = ", ".join(sorted(LLM_ADAPTERS))
        raise ValueError(f"Unknown LLM adapter {name!r}; available: {available}")
    return factory(api_key=api_key, base_url=base_url, model=model)

