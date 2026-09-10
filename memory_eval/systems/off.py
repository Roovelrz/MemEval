"""End-to-end no-memory System adapter for ablation controls."""

from __future__ import annotations

import hashlib
import time
from copy import deepcopy
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from memory_eval.adapters.memory.off import NoMemoryAdapter

from .base import (
    OptionalSystemOperations, SystemCapabilities, SystemCaseRuntime,
    SystemIngestResult, SystemOperationResult, SystemSearchResult,
)
from .reme import build_reme_case


@dataclass
class NoMemorySystemRuntime(SystemCaseRuntime):
    namespace: str = ""
    dataset_id: str = ""
    trace: list[dict[str, Any]] = field(default_factory=list)
    indexed: bool = False
    closed: bool = False


class NoMemorySystemAdapter(OptionalSystemOperations):
    """无记忆消融对照：走完整检索→回答→评审流程，但既不存储也不返回任何记忆。

    检索类指标如实记 0（而非 unsupported），回答由外部 LLM 阶段在无记忆
    上下文下生成，用于衡量 memory 系统带来的净增益。
    """

    name = "off"
    capabilities = SystemCapabilities(
        write_trace=True, retrieval=True, delete=True,
        user_isolation=True, latency_stats=True,
    )

    def __init__(self) -> None:
        self.backend = NoMemoryAdapter()
        self._active: dict[Path, NoMemorySystemRuntime] = {}

    def create_namespace(
        self, *, namespace: str, workspace: Path, case: dict[str, Any],
        context_path: Path, dataset_id: str, port: int, service_log_path: Path,
    ) -> NoMemorySystemRuntime:
        del port, service_log_path  # 无记忆对照不启动任何服务进程
        digest = hashlib.sha256(namespace.encode("utf-8")).hexdigest()[:16]
        runtime = self.open_case(
            workspace=workspace / digest, case=case, context_path=context_path,
            dataset_id=dataset_id,
        )
        runtime.namespace = namespace
        return runtime

    def open_case(
        self,
        *,
        workspace: Path,
        case: dict[str, Any],
        context_path: Path,
        dataset_id: str,
        port: int = 0,
        service_log_path: Path | None = None,
    ) -> NoMemorySystemRuntime:
        del port, service_log_path
        workspace = workspace.resolve()
        for path, active in self._active.items():
            if workspace == path or workspace in path.parents or path in workspace.parents:
                raise ValueError("Namespace workspace overlaps an active namespace")
        prepared = build_reme_case(case, context_path)
        backend_runtime = self.backend.open_case(
            workspace=workspace,
            case=prepared.case,
            dataset_id=dataset_id,
            port=0,
            service_log_path=Path(),
        )
        runtime = NoMemorySystemRuntime(
            case_id=prepared.case["case_id"],
            dimension_id=prepared.case["dimension_id"],
            backend_runtime=backend_runtime,
            canonical_case=prepared.case,
            event_to_session_id=prepared.event_to_session_id,
            memory_to_session_id=prepared.memory_to_session_id,
            namespace=prepared.case["case_id"], dataset_id=dataset_id,
        )
        self._active[workspace] = runtime
        return runtime

    def _require_open(self, runtime: NoMemorySystemRuntime) -> None:
        if runtime.closed or self._active.get(runtime.backend_runtime.workspace.resolve()) is not runtime:
            raise ValueError("Namespace is closed or belongs to another adapter")

    def ingest(self, runtime: NoMemorySystemRuntime) -> SystemIngestResult:
        self._require_open(runtime)
        runtime.indexed = False
        started = time.perf_counter()
        result = self.backend.index(runtime.backend_runtime)
        runtime.indexed = not result.failures
        runtime.trace.append({
            "operation": "ingest", "status": "ok" if runtime.indexed else "error",
            "latency_ms": (time.perf_counter() - started) * 1000,
            "raw_response": result.response, "items": deepcopy(result.items),
            "health": deepcopy(result.health), "failures": deepcopy(result.failures),
        })
        return SystemIngestResult(
            raw_response=result.response,
            items=result.items,
            failures=result.failures,
            latency_ms=result.latency_ms,
        )

    def search(
        self,
        runtime: NoMemorySystemRuntime,
        *,
        query: str,
        top_k: int,
        search_multiplier: int = 1,
        min_score: float = 0.0,
    ) -> SystemSearchResult:
        self._require_open(runtime)
        if not runtime.indexed:
            raise ValueError("Successfully ingest the namespace before searching")
        result = self.backend.search(
            runtime.backend_runtime,
            query=query,
            top_k=top_k,
            search_multiplier=search_multiplier,
            min_score=min_score,
        )
        runtime.trace.append({
            "operation": "search", "status": "ok", "query": query,
            "latency_ms": result.latency_ms, "raw_response": result.response,
            "memories": deepcopy(result.retrieved),
        })
        return SystemSearchResult(
            raw_response=result.response,
            memories=result.retrieved,
            latency_ms=result.latency_ms,
        )

    def list_memories(self, runtime: NoMemorySystemRuntime) -> SystemOperationResult:
        self._require_open(runtime)
        # 什么都没持久化，空列表即真实状态。
        return SystemOperationResult("ok", data=[])

    def delete(self, runtime: NoMemorySystemRuntime, *, memory_ids: list[str]) -> SystemOperationResult:
        self._require_open(runtime)
        del memory_ids
        # 无记忆系统无物可删：no-op 成功，deleted hit 不可能发生。
        return SystemOperationResult("ok", data={"deleted_ids": []})

    def reset(self, runtime: NoMemorySystemRuntime) -> None:
        self._require_open(runtime)
        workspace = runtime.backend_runtime.workspace
        self.backend.close_case(runtime.backend_runtime, keep_workspace=False)
        runtime.indexed = False
        runtime.closed = True
        self._active.pop(workspace.resolve(), None)
        runtime.backend_runtime = self.backend.open_case(
            workspace=workspace, case=runtime.canonical_case, dataset_id=runtime.dataset_id,
            port=0, service_log_path=Path(),
        )
        runtime.trace.clear()
        runtime.closed = False
        self._active[workspace.resolve()] = runtime

    def get_trace(self, runtime: NoMemorySystemRuntime) -> SystemOperationResult:
        return SystemOperationResult("ok", data={"kind": "adapter_operations", "events": deepcopy(runtime.trace)})

    def get_stats(self, runtime: NoMemorySystemRuntime) -> SystemOperationResult:
        operations = {}
        for event in runtime.trace:
            stats = operations.setdefault(event["operation"], {"calls": 0, "latency_ms": 0.0})
            stats["calls"] += 1
            stats["latency_ms"] += event["latency_ms"]
        return SystemOperationResult("ok", data={
            "operations": operations, "add_latency_ms": 0.0,
            "cost": None, "cost_status": "unsupported",
        })

    def cleanup(self, runtime: NoMemorySystemRuntime, *, keep_workspace: bool = False) -> None:
        self.close_case(runtime, keep_workspace=keep_workspace)

    def close_case(self, runtime: NoMemorySystemRuntime, *, keep_workspace: bool = False) -> None:
        if runtime.closed:
            return
        self._require_open(runtime)
        self.backend.close_case(runtime.backend_runtime, keep_workspace=keep_workspace)
        runtime.closed = True
        self._active.pop(runtime.backend_runtime.workspace.resolve(), None)

    def run_metadata(self) -> dict[str, Any]:
        return {"system_adapter": self.name, "capabilities": asdict(self.capabilities),
                "memory_unit": "session", **self.backend.run_metadata()}
