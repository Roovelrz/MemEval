"""Explicit registry for dataset-construction Source Adapters."""

from __future__ import annotations

from .agentmembench import AgentMemBenchSourceAdapter
from .base import SourceAdapter
from .beam import BeamSourceAdapter
from .locomo import LoCoMoSourceAdapter
from .longmemeval import LongMemEvalSourceAdapter
from .memoryagentbench import MemoryAgentBenchSourceAdapter
from .personamem_v2 import PersonaMemV2SourceAdapter
from .prefeval import PrefEvalSourceAdapter


SOURCE_ADAPTERS: dict[str, type[SourceAdapter]] = {
    "longmemeval": LongMemEvalSourceAdapter,
    "locomo": LoCoMoSourceAdapter,
    "prefeval": PrefEvalSourceAdapter,
    "personamem-v2": PersonaMemV2SourceAdapter,
    "memoryagentbench": MemoryAgentBenchSourceAdapter,
    "beam": BeamSourceAdapter,
    "agentmembench": AgentMemBenchSourceAdapter,
}


def create_source_adapter(name: str) -> SourceAdapter:
    key = name.strip().lower().replace("_", "-")
    try:
        adapter_class = SOURCE_ADAPTERS[key]
    except KeyError as exc:
        choices = ", ".join(sorted(SOURCE_ADAPTERS))
        raise ValueError(f"Unknown Source Adapter {name!r}; choose one of: {choices}") from exc
    return adapter_class()
