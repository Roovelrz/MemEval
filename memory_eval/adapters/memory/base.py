"""Common contract for memory systems evaluated by the retrieval runner.

Memory Adapter 是 Eval 框架与被测记忆系统之间的协议层：Runner 按
`open_case -> index -> search -> close_case` 的固定生命周期调用，不关心
被测系统是 CLI 进程（ReMe）、远程服务还是空实现（off）。协议输入输出都
在这里定义；具体实现见同目录 `reme.py` / `off.py`，按名称创建见
`registry.py`。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol


@dataclass
class MemoryCaseRuntime:
    """单个 case 的隔离运行态：workspace 即该 case 的全部世界。

    - `path_map`：写入文件（stem / 文件名 / 相对路径）到 session_id 的映射，
      用于把检索返回的文件路径归一化回 session 维度。
    - `process` / `log_file`：被测系统为该 case 启动的服务进程与日志句柄，
      仅进程型实现（ReMe）使用；close_case 必须负责回收。
    """

    workspace: Path
    path_map: dict[str, str] = field(default_factory=dict)
    written_files: list[Path] = field(default_factory=list)
    add_latency_ms: float = 0.0
    process: Any = None
    log_file: Any = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class MemoryIndexResult:
    """index() 的结果：写入产物、系统健康快照与逐 session 失败清单。"""

    response: Any
    items: list[dict[str, Any]]
    health: dict[str, Any]
    failures: list[dict[str, Any]]
    latency_ms: float


@dataclass
class MemorySearchResult:
    """search() 的结果：原始返回与归一化后的检索记忆。

    `retrieved` 中每项至少含 `session_id` 与文本内容，供上层按
    session/event 维度计算检索指标。
    """

    response: Any
    raw_results: list[dict[str, Any]]
    retrieved: list[dict[str, Any]]
    latency_ms: float


class MemoryAdapter(Protocol):
    """Add sessions, index them, and retrieve memory for one isolated case.

    生命周期约定（Runner 视角）：

    1. `open_case`：为该 case 创建独立 workspace、写入 sessions、启动服务；
       同一时间一个 workspace 只属于一个 case，case 之间不得共享状态。
    2. `index`：建立索引并返回健康快照；失败清单为空视为写入成功。
    3. `search`：执行检索并归一化结果；可在 index 之后多次调用。
    4. `close_case`：停止服务并清理 workspace（`keep_workspace=True` 时保留
       现场供人工调试）。

    `run_metadata` 描述被测系统的版本与配置开关，会原样进入 run 汇总，
    用于实验溯源。
    """

    name: str
    enabled: bool

    def open_case(
        self,
        *,
        workspace: Path,
        case: dict[str, Any],
        dataset_id: str,
        port: int,
        service_log_path: Path,
    ) -> MemoryCaseRuntime:
        ...

    def index(self, runtime: MemoryCaseRuntime) -> MemoryIndexResult:
        ...

    def search(
        self,
        runtime: MemoryCaseRuntime,
        *,
        query: str,
        top_k: int,
        search_multiplier: int,
        min_score: float,
    ) -> MemorySearchResult:
        ...

    def close_case(self, runtime: MemoryCaseRuntime, *, keep_workspace: bool) -> None:
        ...

    def run_metadata(self) -> dict[str, Any]:
        ...
