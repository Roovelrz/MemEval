"""ReMe-backed session storage and BM25 retrieval for LongMemEval."""

from __future__ import annotations

import asyncio
import json
import re
import shutil
from pathlib import Path, PurePosixPath
from typing import Any, Callable

from memory_eval.datasets.models import MemoryHit


SAFE_NAME = re.compile(r"[^A-Za-z0-9_.-]+")


def _safe_name(value: str) -> str:
    cleaned = SAFE_NAME.sub("_", value).strip("._")
    return cleaned or "unnamed"


def _frontmatter_value(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


class ReMeAdapter:
    """Persist whole sessions as Markdown and retrieve ReMe BM25 chunks.

    The adapter owns exactly one sequential workspace. ``reset`` removes only
    that workspace, so every LongMemEval case is indexed in isolation.
    """

    def __init__(
        self,
        work_root: str | Path,
        application_factory: Callable[..., Any] | None = None,
    ) -> None:
        self.work_root = Path(work_root).resolve()
        self.workspace = self.work_root / "workspace"
        self._application_factory = application_factory
        self._active_namespace: str | None = None
        self._case_id = ""
        self._path_metadata: dict[str, dict[str, str]] = {}

    def reset(self, namespace: str) -> None:
        self._clear_workspace()
        self.workspace.mkdir(parents=True, exist_ok=True)
        (self.workspace / "daily").mkdir(parents=True, exist_ok=True)
        self._active_namespace = namespace
        self._case_id = namespace.rsplit(":", 1)[-1]
        self._path_metadata.clear()

    def _clear_workspace(self) -> None:
        work_root = self.work_root.resolve()
        workspace = self.workspace.resolve()
        if workspace == work_root or work_root not in workspace.parents:
            raise ValueError("ReMe workspace must be a child of work_root")
        if workspace.exists():
            shutil.rmtree(workspace)

    def add_session(
        self,
        namespace: str,
        session_id: str,
        timestamp: str,
        messages: list[dict],
    ) -> None:
        self._require_namespace(namespace)
        case_dir = self.workspace / "daily" / _safe_name(self._case_id)
        case_dir.mkdir(parents=True, exist_ok=True)
        stem = _safe_name(session_id)
        path = case_dir / f"{stem}.md"
        suffix = 2
        while path.exists():
            path = case_dir / f"{stem}__{suffix}.md"
            suffix += 1

        lines = [
            "---",
            f"session_id: {_frontmatter_value(session_id)}",
            f"timestamp: {_frontmatter_value(timestamp)}",
            "dataset: longmemeval",
            f"case_id: {_frontmatter_value(self._case_id)}",
            "---",
            "# Session",
            "",
        ]
        for message in messages:
            role = str(message.get("role", "unknown")).strip().lower() or "unknown"
            heading = {"user": "User", "assistant": "Assistant"}.get(role, role.title())
            lines.extend([f"## {heading}", "", str(message.get("content", "")), ""])
        path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")

        relative = path.relative_to(self.workspace).as_posix()
        self._path_metadata[relative] = {
            "session_id": session_id,
            "timestamp": timestamp,
        }

    def search(self, namespace: str, query: str, top_k: int) -> list[MemoryHit]:
        self._require_namespace(namespace)
        if top_k < 1:
            raise ValueError("top_k must be positive")
        try:
            return asyncio.run(self._search(query=query, top_k=top_k))
        finally:
            self._clear_workspace()
            self._active_namespace = None
            self._path_metadata.clear()

    def _require_namespace(self, namespace: str) -> None:
        if namespace != self._active_namespace:
            raise ValueError("reset(namespace) must be called before add/search")

    def _config(self) -> dict[str, Any]:
        return {
            "app_name": "memory-eval-reme",
            "workspace_dir": str(self.workspace),
            "enable_logo": False,
            "log_to_console": False,
            "log_to_file": False,
            "service": {"backend": "cli"},
            "jobs": {
                "reindex": {
                    "backend": "base",
                    "watch_dirs": ["daily_dir"],
                    "watch_suffixes": ["md"],
                    "steps": [
                        {"backend": "clear_store_step"},
                        {
                            "backend": "init_changes_step",
                            "monitor_type": "file_store",
                            "monitor_name": "default",
                            "dispatch_steps": ["update_index_step"],
                        },
                    ],
                },
                "search": {
                    "backend": "base",
                    "steps": [
                        {
                            "backend": "search_step",
                            "vector_weight": 0.0,
                            "candidate_multiplier": 5.0,
                            "expand_links": False,
                        },
                    ],
                },
            },
            "components": {
                "tokenizer": {"default": {"backend": "regex"}},
                "file_graph": {"default": {"backend": "local"}},
                "file_chunker": {
                    "markdown": {
                        "backend": "markdown",
                        "supported_extensions": ["md"],
                        "embed_toc": True,
                    },
                },
                "keyword_index": {
                    "default": {"backend": "bm25", "tokenizer": "default"},
                },
                "file_store": {
                    "default": {
                        "backend": "local",
                        "store_name": "local",
                        "embedding_store": "",
                        "keyword_index": "default",
                        "file_graph": "default",
                    },
                },
            },
        }

    def _make_application(self) -> Any:
        if self._application_factory is None:
            try:
                from reme import Application
            except ImportError as exc:
                raise RuntimeError(
                    "ReMe is not installed. Install the local clone with "
                    "`py -3.12 -m pip install -e ..\\ReMe` and its core dependencies."
                ) from exc
            factory = Application
        else:
            factory = self._application_factory
        return factory(**self._config())

    async def _search(self, query: str, top_k: int) -> list[MemoryHit]:
        application = self._make_application()
        await application.start()
        try:
            reindex = await application.run_job("reindex")
            if not bool(getattr(reindex, "success", False)):
                raise RuntimeError(f"ReMe reindex failed: {getattr(reindex, 'answer', '')}")
            response = await application.run_job(
                "search",
                query=query,
                limit=top_k,
                vector_weight=0.0,
            )
            if not bool(getattr(response, "success", False)):
                raise RuntimeError(f"ReMe search failed: {getattr(response, 'answer', '')}")
            results = getattr(response, "metadata", {}).get("results", [])
            return [self._to_hit(result) for result in results]
        finally:
            await application.close()

    def _to_hit(self, result: dict[str, Any]) -> MemoryHit:
        source = PurePosixPath(str(result.get("path", "")).replace("\\", "/")).as_posix()
        metadata = self._path_metadata.get(source)
        if metadata is None:
            metadata = {
                "session_id": PurePosixPath(source).stem,
                "timestamp": "",
            }
        scores = result.get("scores") or {}
        score = scores.get("score", scores.get("keyword"))
        return MemoryHit(
            text=str(result.get("text", "")),
            score=float(score) if score is not None else None,
            metadata={
                **metadata,
                "source": source,
                "backend": "bm25",
                "chunk_id": result.get("id"),
                "start_line": result.get("start_line"),
                "end_line": result.get("end_line"),
            },
        )
