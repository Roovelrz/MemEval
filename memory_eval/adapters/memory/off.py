"""No-memory control adapter.

无记忆消融对照的协议层实现：完整走 open/index/search/close 生命周期，但
既不存储也不返回任何记忆。检索结果恒为空，检索指标在上层如实记 0（而非
unsupported），用于和 `reme` 对照、衡量记忆系统带来的净增益。
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from .base import MemoryCaseRuntime, MemoryIndexResult, MemorySearchResult


class NoMemoryAdapter:
    """Intentionally returns no memory, for the no-memory experimental control.

    语义约定：
    - `index` 恒定成功且无产物——系统没有写入任何东西；
    - `search` 恒定返回空——答案只能来自 Answer LLM 的参数知识；
    - 不启动任何进程或服务，端口与日志参数仅用于满足协议签名。
    """

    name = "off"
    enabled = False

    def open_case(
        self,
        *,
        workspace: Path,
        case: dict[str, Any],
        dataset_id: str,
        port: int,
        service_log_path: Path,
    ) -> MemoryCaseRuntime:
        del case, dataset_id, port, service_log_path
        return MemoryCaseRuntime(workspace=workspace)

    def index(self, runtime: MemoryCaseRuntime) -> MemoryIndexResult:
        del runtime
        return MemoryIndexResult(response={}, items=[], health={}, failures=[], latency_ms=0.0)

    def search(
        self,
        runtime: MemoryCaseRuntime,
        *,
        query: str,
        top_k: int,
        search_multiplier: int,
        min_score: float,
    ) -> MemorySearchResult:
        del runtime, query, top_k, search_multiplier, min_score
        return MemorySearchResult(response={}, raw_results=[], retrieved=[], latency_ms=0.0)

    def close_case(self, runtime: MemoryCaseRuntime, *, keep_workspace: bool) -> None:
        if runtime.workspace.exists() and not keep_workspace:
            shutil.rmtree(runtime.workspace, ignore_errors=True)

    def run_metadata(self) -> dict[str, Any]:
        # 元数据如实标注"无"，让 run 汇总与 Trace 不需要特判该对照。
        return {
            "memory_backend": "none",
            "memory_version": "NOT_APPLICABLE",
            "retrieval_backend": "none",
            "embedding_enabled": False,
            "llm_enabled": False,
        }
