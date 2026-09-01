"""ReMe CLI memory adapter preserving the existing BM25 evaluation behavior."""

from __future__ import annotations

import importlib.metadata
import json
import os
import shlex
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Callable

from .base import MemoryCaseRuntime, MemoryIndexResult, MemorySearchResult


def safe_name(value: str) -> str:
    cleaned = "".join(char if char.isalnum() or char in "._-" else "_" for char in value)
    return cleaned.strip("._") or "unnamed"


def render_session_markdown(case_id: str, session: dict[str, Any], dataset_id: str) -> str:
    lines = [
        "---",
        f"case_id: {json.dumps(case_id, ensure_ascii=False)}",
        f"session_id: {json.dumps(session['session_id'], ensure_ascii=False)}",
        f"timestamp: {json.dumps(session['timestamp'], ensure_ascii=False)}",
        f"dataset: {json.dumps(dataset_id, ensure_ascii=False)}",
        "---",
        "# Conversation Session",
        "",
    ]
    for message in session["messages"]:
        role = str(message.get("role", "unknown")).strip().lower() or "unknown"
        heading = {"user": "User", "assistant": "Assistant"}.get(role, role.title())
        lines.extend([f"## {heading}", "", str(message.get("content", "")), ""])
    return "\n".join(lines)


def write_case_workspace(workspace: Path, case: dict[str, Any], dataset_id: str) -> dict[str, str]:
    daily_dir = workspace / "daily" / safe_name(case["case_id"])
    daily_dir.mkdir(parents=True, exist_ok=True)
    path_map: dict[str, str] = {}
    used_names: set[str] = set()
    for session in case["sessions"]:
        stem = safe_name(session["session_id"])
        candidate = stem
        suffix = 2
        while candidate in used_names:
            candidate = f"{stem}__{suffix}"
            suffix += 1
        used_names.add(candidate)
        path = daily_dir / f"{candidate}.md"
        path.write_text(render_session_markdown(case["case_id"], session, dataset_id), encoding="utf-8")
        path_map[candidate] = session["session_id"]
        path_map[path.name] = session["session_id"]
        path_map[path.as_posix()] = session["session_id"]
        path_map[path.relative_to(workspace).as_posix()] = session["session_id"]
    return path_map


def http_post(port: int, endpoint: str, payload: dict[str, Any], timeout: float) -> Any:
    request = urllib.request.Request(
        f"http://127.0.0.1:{port}/{endpoint}",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read().decode("utf-8")
            content_type = response.headers.get("Content-Type", "")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"ReMe {endpoint} HTTP {exc.code}: {detail[:500]}") from exc
    if "text/event-stream" in content_type:
        chunks = [
            line[5:].strip()
            for line in body.splitlines()
            if line.startswith("data:") and line[5:].strip() != "[DONE]"
        ]
        body = chunks[-1] if chunks else ""
    if not body.strip():
        return {}
    try:
        return json.loads(body)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"ReMe {endpoint} returned non-JSON data: {body[:500]}") from exc


def wait_for_reme(port: int, timeout_seconds: float) -> None:
    deadline = time.time() + timeout_seconds
    last_error: Exception | None = None
    while time.time() < deadline:
        try:
            response = http_post(port, "health_check", {}, timeout=5)
            if isinstance(response, dict) and response.get("success") is False:
                raise RuntimeError(str(response.get("answer", "health_check failed")))
            return
        except Exception as exc:
            last_error = exc
            time.sleep(0.5)
    raise RuntimeError(f"ReMe did not become ready on port {port}: {last_error}")


def resolve_reme_command(value: str | None) -> list[str]:
    if value:
        command = [item.strip('"') for item in shlex.split(value, posix=False)]
        if command:
            return command
    env_value = os.environ.get("REME_CMD")
    if env_value:
        return [item.strip('"') for item in shlex.split(env_value, posix=False)]
    candidates = ["reme"]
    scripts_dir = Path(sys.executable).resolve().parent / "Scripts"
    candidates.extend([str(scripts_dir / "reme.exe"), str(scripts_dir / "reme")])
    for candidate in candidates:
        if Path(candidate).is_file() or shutil.which(candidate):
            return [candidate]
    raise FileNotFoundError("Could not find the ReMe CLI. Install it or pass --reme-cmd explicitly.")


def create_bm25_config(path: Path, vector_weight: float) -> Path:
    if vector_weight != 0.0:
        raise ValueError("Generated baseline config only supports vector_weight=0.0; use --reme-config for hybrid mode")
    path.write_text(
        """# Minimal service configuration for the ReMe retrieval-only baseline.
service:
  backend: http
  web_enabled: false
jobs:
  health_check:
    backend: base
    enable_serve: true
    steps:
      - backend: health_check_step
  reindex:
    backend: base
    enable_serve: true
    watch_dirs: [daily_dir, digest_dir, resource_dir]
    watch_suffixes: [md, jsonl]
    steps:
      - backend: clear_store_step
      - backend: init_changes_step
        monitor_type: file_store
        monitor_name: default
        dispatch_steps: [update_index_step]
  search:
    backend: base
    enable_serve: true
    steps:
      - backend: search_step
        vector_weight: 0.0
        candidate_multiplier: 5.0
        expand_links: false
components:
  tokenizer:
    default:
      backend: regex
  file_graph:
    default:
      backend: local
  keyword_index:
    default:
      backend: bm25
      tokenizer: default
  file_store:
    default:
      backend: local
      embedding_store: ""
      keyword_index: default
      file_graph: default
  file_chunker:
    markdown:
      backend: markdown
      supported_extensions: [md]
      embed_toc: true
      max_ast_sections: 100
      include_frontmatter_in_metadata: false
      include_frontmatter_keys_in_metadata: []
""",
        encoding="utf-8",
    )
    return path


def start_reme(
    command: list[str], workspace: Path, port: int, config: Path, log_path: Path
) -> tuple[subprocess.Popen[str], Any]:
    log_file = log_path.open("a", encoding="utf-8")
    process = subprocess.Popen(
        [
            *command,
            "start",
            f"config={config}",
            f"workspace_dir={workspace}",
            f"service.port={port}",
            "service.host=127.0.0.1",
            "service.web_enabled=false",
            "enable_logo=false",
        ],
        stdout=log_file,
        stderr=subprocess.STDOUT,
        text=True,
        cwd=str(Path(__file__).resolve().parents[3]),
    )
    return process, log_file


def stop_reme(process: subprocess.Popen[str], log_file: Any) -> None:
    try:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
    finally:
        log_file.close()


def find_results(node: Any) -> list[dict[str, Any]] | None:
    if isinstance(node, dict):
        results = node.get("results")
        if isinstance(results, list):
            return [item for item in results if isinstance(item, dict)]
        for value in node.values():
            found = find_results(value)
            if found is not None:
                return found
    elif isinstance(node, list):
        for value in node:
            found = find_results(value)
            if found is not None:
                return found
    return None


def find_index_results(node: Any) -> list[dict[str, Any]]:
    if isinstance(node, dict):
        for key in ("answer", "results"):
            value = node.get(key)
            if isinstance(value, list) and all(isinstance(item, dict) for item in value):
                if any("success" in item and "path" in item for item in value):
                    return value
        for value in node.values():
            found = find_index_results(value)
            if found:
                return found
    elif isinstance(node, list):
        for value in node:
            found = find_index_results(value)
            if found:
                return found
    return []


def find_index_health(node: Any) -> dict[str, Any]:
    if isinstance(node, dict):
        if "n_chunks" in node and ("n_nodes" in node or "n_chunks_with_embedding" in node):
            return node
        for value in node.values():
            found = find_index_health(value)
            if found:
                return found
    elif isinstance(node, list):
        for value in node:
            found = find_index_health(value)
            if found:
                return found
    return {}


def result_path(result: dict[str, Any]) -> str:
    for key in ("path", "source", "file"):
        if result.get(key):
            return str(result[key])
    metadata = result.get("metadata")
    if isinstance(metadata, dict):
        for key in ("path", "source", "file"):
            if metadata.get(key):
                return str(metadata[key])
    return ""


def result_text(result: dict[str, Any]) -> str:
    for key in ("content", "text", "chunk", "snippet"):
        if result.get(key) is not None:
            return str(result[key])
    return ""


def result_score(result: dict[str, Any]) -> float | None:
    for key in ("score", "fused_score", "keyword_score"):
        value = result.get(key)
        if value is None and isinstance(result.get("scores"), dict):
            value = result["scores"].get(key) or result["scores"].get("keyword")
        if value is not None:
            try:
                return float(value)
            except (TypeError, ValueError):
                return None
    return None


def session_id_for_result(path: str, path_map: dict[str, str]) -> str:
    normalized = path.replace("\\", "/")
    for candidate in (normalized, Path(normalized).name, Path(normalized).stem):
        if candidate in path_map:
            return path_map[candidate]
    return Path(normalized).stem


def deduplicate_sessions(
    raw_results: list[dict[str, Any]], top_k: int, path_map: dict[str, str]
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    seen: set[str] = set()
    for raw_rank, result in enumerate(raw_results, start=1):
        source = result_path(result)
        session_id = session_id_for_result(source, path_map)
        if not session_id or session_id in seen:
            continue
        seen.add(session_id)
        output.append(
            {
                "rank": len(output) + 1,
                "raw_rank": raw_rank,
                "session_id": session_id,
                "path": source,
                "score": result_score(result),
                "text": result_text(result),
            }
        )
        if len(output) >= top_k:
            break
    return output


def reme_version() -> str:
    try:
        return importlib.metadata.version("reme-ai")
    except importlib.metadata.PackageNotFoundError:
        return "NOT_RECORDED"


class ReMeCliMemoryAdapter:
    name = "reme"
    enabled = True

    def __init__(
        self,
        *,
        command: list[str],
        config_path: Path,
        startup_timeout: float,
        vector_weight: float,
        start_fn: Callable[..., tuple[subprocess.Popen[str], Any]] | None = None,
        stop_fn: Callable[..., None] | None = None,
        wait_fn: Callable[..., None] | None = None,
        http_fn: Callable[..., Any] | None = None,
    ) -> None:
        self.command = command
        self.config_path = config_path
        self.startup_timeout = startup_timeout
        self.vector_weight = vector_weight
        self._start = start_fn or start_reme
        self._stop = stop_fn or stop_reme
        self._wait = wait_fn or wait_for_reme
        self._http = http_fn or http_post

    def open_case(
        self,
        *,
        workspace: Path,
        case: dict[str, Any],
        dataset_id: str,
        port: int,
        service_log_path: Path,
    ) -> MemoryCaseRuntime:
        if workspace.exists():
            shutil.rmtree(workspace)
        workspace.mkdir(parents=True, exist_ok=True)
        started = time.perf_counter()
        path_map = write_case_workspace(workspace, case, dataset_id)
        written_files = list((workspace / "daily" / safe_name(case["case_id"])).glob("*.md"))
        runtime = MemoryCaseRuntime(
            workspace=workspace,
            path_map=path_map,
            written_files=written_files,
            add_latency_ms=(time.perf_counter() - started) * 1000,
            metadata={"port": port, "service_log": str(service_log_path)},
        )
        runtime.process, runtime.log_file = self._start(
            self.command, workspace, port, self.config_path, service_log_path
        )
        try:
            self._wait(port, self.startup_timeout)
        except Exception:
            self._stop(runtime.process, runtime.log_file)
            runtime.process = None
            runtime.log_file = None
            raise
        return runtime

    def index(self, runtime: MemoryCaseRuntime) -> MemoryIndexResult:
        started = time.perf_counter()
        response = self._http(int(runtime.metadata["port"]), "reindex", {}, timeout=300)
        latency_ms = (time.perf_counter() - started) * 1000
        if isinstance(response, dict) and response.get("success") is False:
            raise RuntimeError(f"ReMe reindex failed: {response.get('answer', '')}")
        items = find_index_results(response)
        health_response = self._http(int(runtime.metadata["port"]), "health_check", {}, timeout=30)
        health = find_index_health(health_response)
        failures = [item for item in items if item.get("success") is False]
        return MemoryIndexResult(response=response, items=items, health=health, failures=failures, latency_ms=latency_ms)

    def search(
        self,
        runtime: MemoryCaseRuntime,
        *,
        query: str,
        top_k: int,
        search_multiplier: int,
        min_score: float,
    ) -> MemorySearchResult:
        search_limit = max(top_k, top_k * search_multiplier)
        started = time.perf_counter()
        response = self._http(
            int(runtime.metadata["port"]),
            "search",
            {"query": query, "limit": search_limit, "min_score": min_score},
            timeout=120,
        )
        latency_ms = (time.perf_counter() - started) * 1000
        raw_results = find_results(response) or []
        retrieved = deduplicate_sessions(raw_results, top_k, runtime.path_map)
        return MemorySearchResult(
            response=response,
            raw_results=raw_results,
            retrieved=retrieved,
            latency_ms=latency_ms,
        )

    def close_case(self, runtime: MemoryCaseRuntime, *, keep_workspace: bool) -> None:
        if runtime.process is not None and runtime.log_file is not None:
            self._stop(runtime.process, runtime.log_file)
        if runtime.workspace.exists() and not keep_workspace:
            shutil.rmtree(runtime.workspace, ignore_errors=True)

    def run_metadata(self) -> dict[str, Any]:
        return {
            "memory_backend": "ReMe",
            "memory_version": reme_version(),
            "retrieval_backend": "BM25" if self.vector_weight == 0.0 else "ReMe configured hybrid",
            "embedding_enabled": self.vector_weight != 0.0,
            "llm_enabled": False,
            "reme_command": self.command,
            "reme_config": str(self.config_path),
        }
