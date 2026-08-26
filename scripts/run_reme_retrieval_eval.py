"""Run an isolated ReMe BM25 retrieval baseline.

This runner deliberately stops at retrieval. It does not call an Answer Model
or Judge. Every case receives a fresh ReMe workspace, so one case cannot leak
files or an index into the next case.

The runner accepts the frozen Clean LongMemEval schema in this repository and
also accepts a small set of common JSON/JSONL variants. If a future dataset
uses different field names, change only ``normalize_case`` and its helpers.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
import random
import shlex
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from memory_eval.dataset_integrity import freeze_dataset_integrity


DEFAULT_DATASET = (
    REPO_ROOT
    / "datasets"
    / "zh_derived"
    / "longmemeval_zh"
    / "LongMemEval-ZH-20-v0.1"
    / "dataset.json"
)
DEFAULT_OUTPUT = REPO_ROOT / "results" / "reme_retrieval"


def load_json_or_jsonl(path: Path) -> list[dict[str, Any]]:
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        raise ValueError(f"Dataset is empty: {path}")
    if path.suffix.lower() == ".jsonl":
        rows = [json.loads(line) for line in text.splitlines() if line.strip()]
        if not all(isinstance(row, dict) for row in rows):
            raise ValueError("Every JSONL line must be an object")
        return rows

    payload = json.loads(text)
    if isinstance(payload, list) and all(isinstance(row, dict) for row in payload):
        return payload
    if isinstance(payload, dict):
        for key in ("cases", "items", "data", "samples"):
            value = payload.get(key)
            if isinstance(value, list) and all(isinstance(row, dict) for row in value):
                return value
    raise ValueError(f"Cannot find a case list in dataset: {path}")


def first_value(obj: dict[str, Any], keys: Iterable[str], default: Any = None) -> Any:
    for key in keys:
        if key in obj and obj[key] is not None:
            return obj[key]
    return default


def normalize_message(message: dict[str, Any]) -> dict[str, Any]:
    role = first_value(message, ("role", "speaker"), "unknown")
    content = first_value(
        message,
        ("content", "text", "translated_content", "zh_content"),
        "",
    )
    return {
        "role": str(role),
        "content": str(content),
        "has_answer": message.get("has_answer"),
    }


def normalize_session(session: dict[str, Any], index: int) -> dict[str, Any]:
    session_id = first_value(session, ("session_id", "id"), f"session_{index:04d}")
    timestamp = first_value(session, ("timestamp", "date", "session_date"), "")
    raw_messages = first_value(session, ("messages", "turns"), [])
    if not isinstance(raw_messages, list):
        raise ValueError(f"Session {session_id!r} messages/turns must be a list")
    return {
        "session_id": str(session_id),
        "timestamp": str(timestamp),
        "messages": [normalize_message(message) for message in raw_messages],
        "is_evidence_session": bool(session.get("is_evidence_session", False)),
    }


def normalize_case(raw: dict[str, Any], index: int) -> dict[str, Any]:
    """Map Clean LongMemEval or a compatible record to the runner schema."""
    case_id = first_value(raw, ("case_id", "question_id", "id"), f"case_{index:04d}")
    question = first_value(raw, ("question", "query"), "")
    gold_answer = first_value(raw, ("gold_answer", "answer"), "")
    raw_sessions = raw.get("sessions")

    # Support the original LongMemEval-S shape without changing the rest of
    # the runner. Clean JSON uses a list of session objects instead.
    if raw_sessions is None and "haystack_sessions" in raw:
        ids = raw.get("haystack_session_ids", [])
        dates = raw.get("haystack_dates", [])
        histories = raw.get("haystack_sessions", [])
        raw_sessions = [
            {
                "session_id": session_id,
                "timestamp": timestamp,
                "messages": messages,
                "is_evidence_session": session_id in raw.get("answer_session_ids", []),
            }
            for session_id, timestamp, messages in zip(ids, dates, histories, strict=True)
        ]
    if not isinstance(raw_sessions, list):
        raise ValueError(f"Case {case_id!r} has no sessions list")

    sessions = [normalize_session(session, i) for i, session in enumerate(raw_sessions)]
    explicit_evidence = first_value(raw, ("evidence_session_ids", "answer_session_ids"), None)
    if explicit_evidence is None:
        evidence_ids = [s["session_id"] for s in sessions if s["is_evidence_session"]]
    else:
        evidence_ids = [str(value) for value in explicit_evidence]

    return {
        "case_id": str(case_id),
        "question": str(question),
        "gold_answer": str(gold_answer),
        "question_type": str(raw.get("question_type", "")),
        "question_date": str(raw.get("question_date", "")),
        "sessions": sessions,
        "evidence_session_ids": evidence_ids,
    }


def safe_name(value: str) -> str:
    cleaned = "".join(char if char.isalnum() or char in "._-" else "_" for char in value)
    return cleaned.strip("._") or "unnamed"


def render_session_markdown(case_id: str, session: dict[str, Any]) -> str:
    lines = [
        "---",
        f"case_id: {json.dumps(case_id, ensure_ascii=False)}",
        f"session_id: {json.dumps(session['session_id'], ensure_ascii=False)}",
        f"timestamp: {json.dumps(session['timestamp'], ensure_ascii=False)}",
        "dataset: LongMemEval-ZH",
        "---",
        "# Conversation Session",
        "",
    ]
    for message in session["messages"]:
        role = str(message.get("role", "unknown")).strip().lower() or "unknown"
        heading = {"user": "User", "assistant": "Assistant"}.get(role, role.title())
        lines.extend([f"## {heading}", "", str(message.get("content", "")), ""])
    return "\n".join(lines)


def write_case_workspace(workspace: Path, case: dict[str, Any]) -> dict[str, str]:
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
        path.write_text(render_session_markdown(case["case_id"], session), encoding="utf-8")
        path_map[candidate] = session["session_id"]
        path_map[path.name] = session["session_id"]
        path_map[path.as_posix()] = session["session_id"]
        path_map[path.relative_to(workspace).as_posix()] = session["session_id"]
    return path_map


def http_post(port: int, endpoint: str, payload: dict[str, Any], timeout: float) -> Any:
    url = f"http://127.0.0.1:{port}/{endpoint}"
    request = urllib.request.Request(
        url,
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
        chunks = []
        for line in body.splitlines():
            if line.startswith("data:") and line[5:].strip() != "[DONE]":
                chunks.append(line[5:].strip())
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
        except Exception as exc:  # service may need several seconds to bind
            last_error = exc
            time.sleep(0.5)
    raise RuntimeError(f"ReMe did not become ready on port {port}: {last_error}")


def resolve_reme_command(value: str | None) -> list[str]:
    if value:
        command = shlex.split(value, posix=False)
        command = [item.strip('"') for item in command]
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
    raise FileNotFoundError(
        "Could not find the ReMe CLI. Install the local clone or pass "
        "--reme-cmd 'C:\\path\\to\\reme.exe'."
    )


def create_bm25_config(path: Path, vector_weight: float) -> Path:
    if vector_weight != 0.0:
        raise ValueError("Generated baseline config only supports vector_weight=0.0; use --reme-config for hybrid mode")
    path.write_text(
        """# Minimal service configuration for the ReMe retrieval-only baseline.
# It intentionally does not declare as_llm or embedding_store, so BM25 runs
# without API credentials and without embedding backfill.
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
    command: list[str],
    workspace: Path,
    port: int,
    config: Path,
    log_path: Path,
) -> tuple[subprocess.Popen[str], Any]:
    log_file = log_path.open("a", encoding="utf-8")
    args = [
        *command,
        "start",
        f"config={config}",
        f"workspace_dir={workspace}",
        f"service.port={port}",
        "service.host=127.0.0.1",
        "service.web_enabled=false",
        "enable_logo=false",
    ]
    process = subprocess.Popen(
        args,
        stdout=log_file,
        stderr=subprocess.STDOUT,
        text=True,
        cwd=str(REPO_ROOT),
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
    candidates = [normalized, Path(normalized).name, Path(normalized).stem]
    for candidate in candidates:
        if candidate in path_map:
            return path_map[candidate]
    return Path(normalized).stem


def deduplicate_sessions(
    raw_results: list[dict[str, Any]],
    top_k: int,
    path_map: dict[str, str],
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


def render_answer_context(item: dict[str, Any]) -> str:
    """Render one retrieved session with the metadata needed for temporal reasoning."""
    score = item.get("score")
    score_text = "NOT_RECORDED" if score is None else str(score)
    return "\n".join(
        [
            f'<memory rank="{item.get("rank", "")}">',
            f'session_id: {json.dumps(str(item.get("session_id", "")), ensure_ascii=False)}',
            f'timestamp: {json.dumps(str(item.get("timestamp", "")), ensure_ascii=False)}',
            f"retrieval_score: {score_text}",
            "content:",
            str(item.get("text", "")),
            "</memory>",
        ]
    )


def evaluate_retrieval(retrieved: list[dict[str, Any]], evidence_ids: list[str]) -> dict[str, float | int | None]:
    if not evidence_ids:
        return {"hit": None, "recall": None, "mrr": None}
    gold = set(evidence_ids)
    retrieved_ids = [item["session_id"] for item in retrieved]
    matched = [session_id for session_id in retrieved_ids if session_id in gold]
    reciprocal_rank = 0.0
    for rank, session_id in enumerate(retrieved_ids, start=1):
        if session_id in gold:
            reciprocal_rank = 1.0 / rank
            break
    return {
        "hit": int(bool(matched)),
        "recall": len(set(matched)) / len(gold),
        "mrr": reciprocal_rank,
    }


def mean(values: Iterable[float | int | None]) -> float | None:
    usable = [float(value) for value in values if value is not None]
    return sum(usable) / len(usable) if usable else None


def percentile(values: Iterable[float | int | None], quantile: float) -> float | None:
    usable = sorted(float(value) for value in values if value is not None)
    if not usable:
        return None
    position = (len(usable) - 1) * quantile
    lower = int(position)
    upper = min(lower + 1, len(usable) - 1)
    fraction = position - lower
    return usable[lower] + (usable[upper] - usable[lower]) * fraction


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def reme_version() -> str:
    try:
        return importlib.metadata.version("reme-ai")
    except importlib.metadata.PackageNotFoundError:
        return "NOT_RECORDED"


def git_metadata(repo: Path) -> dict[str, Any]:
    try:
        commit = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=repo, check=True, capture_output=True, text=True
        ).stdout.strip()
        dirty = bool(
            subprocess.run(
                ["git", "status", "--porcelain"], cwd=repo, check=True, capture_output=True, text=True
            ).stdout.strip()
        )
        return {"commit": commit, "dirty": dirty}
    except (OSError, subprocess.CalledProcessError):
        return {"commit": "NOT_RECORDED", "dirty": "NOT_RECORDED"}


def snapshot_eval_code(run_dir: Path, git_info: dict[str, Any]) -> dict[str, Any]:
    """Persist the exact runner/report source used by the run, even when dirty."""

    snapshot_dir = run_dir / "eval_code_snapshot"
    source_files = sorted(
        {
            *[
                path
                for root in (REPO_ROOT / "scripts", REPO_ROOT / "memory_eval")
                for pattern in ("*.py", "*.css", "*.js")
                for path in root.rglob(pattern)
            ],
            *[
                path
                for path in (REPO_ROOT / "pyproject.toml", REPO_ROOT / "requirements.txt")
                if path.is_file()
            ],
        }
    )
    manifest_files: list[dict[str, str]] = []
    for source in source_files:
        relative = source.relative_to(REPO_ROOT)
        target = snapshot_dir / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        manifest_files.append({"path": relative.as_posix(), "sha256": sha256_file(target)})
    manifest = {
        "schema_version": "memory_eval_code_snapshot_v1",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "git_commit": git_info.get("commit", "NOT_RECORDED"),
        "git_dirty": git_info.get("dirty", "NOT_RECORDED"),
        "python_version": sys.version,
        "files": manifest_files,
    }
    manifest_path = snapshot_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {
        "directory": str(snapshot_dir),
        "manifest": str(manifest_path),
        "manifest_sha256": sha256_file(manifest_path),
        "file_count": len(manifest_files),
    }


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


def retrieval_metrics_at_k(
    retrieved: list[dict[str, Any]], evidence_ids: list[str], k: int
) -> dict[str, float | int | None]:
    if not evidence_ids:
        return {"hit": None, "recall": None, "precision": None}
    selected = retrieved[:k]
    gold = set(evidence_ids)
    matched = {str(item.get("session_id", "")) for item in selected} & gold
    return {
        "hit": int(bool(matched)),
        "recall": len(matched) / len(gold),
        "precision": len(matched) / len(selected) if selected else 0.0,
    }


def append_jsonl(path: Path, row: dict[str, Any]) -> None:
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def _read_failure_rows(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            value = json.loads(line)
            if isinstance(value, dict):
                rows.append(value)
    return rows


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the ReMe BM25 retrieval baseline")
    parser.add_argument("--data", "--dataset", dest="data", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--cases", "--limit", dest="limit", type=int, default=1, help="0 means all")
    parser.add_argument("--start", type=int, default=0)
    parser.add_argument("--top-k", type=int, default=10)
    parser.add_argument("--search-multiplier", type=int, default=3)
    parser.add_argument("--min-score", type=float, default=0.0)
    parser.add_argument("--shuffle", action="store_true")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--run-id", default="")
    parser.add_argument("--base-port", type=int, default=23330)
    parser.add_argument("--startup-timeout", type=float, default=60.0)
    parser.add_argument("--reme-cmd", default=None, help="ReMe executable or command string")
    parser.add_argument("--reme-config", type=Path, default=None, help="Custom ReMe config; default is generated BM25-only config")
    parser.add_argument("--vector-weight", type=float, default=0.0, help="0.0 is the BM25 baseline")
    parser.add_argument("--model", default="none", help="Model label stored in run_config; BM25 baseline does not call a model")
    parser.add_argument("--keep-workspaces", action="store_true")
    return parser.parse_args()


def run(args: argparse.Namespace) -> int:
    run_started_at = datetime.now(timezone.utc)
    if args.limit < 0 or args.start < 0:
        raise ValueError("--cases/--limit and --start must be non-negative")
    if args.top_k < 1 or args.search_multiplier < 1:
        raise ValueError("--top-k and --search-multiplier must be positive")

    dataset_path = args.data.resolve()
    raw_cases = load_json_or_jsonl(dataset_path)
    all_cases = [normalize_case(raw, index) for index, raw in enumerate(raw_cases)]
    cases = list(all_cases)
    if args.shuffle:
        random.Random(args.seed).shuffle(cases)
    cases = cases[args.start:]
    if args.limit > 0:
        cases = cases[: args.limit]
    if not cases:
        raise ValueError("No cases selected")

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_id = args.run_id.strip() or f"reme_bm25_{len(cases)}cases_k{args.top_k}_{timestamp}"
    run_dir = args.output_dir.resolve() / run_id
    workspace_root = run_dir / "workspaces"
    raw_search_dir = run_dir / "raw_search"
    raw_reindex_dir = run_dir / "raw_reindex"
    run_dir.mkdir(parents=True, exist_ok=True)
    workspace_root.mkdir(parents=True, exist_ok=True)
    raw_search_dir.mkdir(parents=True, exist_ok=True)
    raw_reindex_dir.mkdir(parents=True, exist_ok=True)

    config_path = args.reme_config.resolve() if args.reme_config else create_bm25_config(run_dir / "reme_bm25.yaml", args.vector_weight)
    command = resolve_reme_command(args.reme_cmd)
    retrieval_path = run_dir / "retrieval.jsonl"
    prepared_path = run_dir / "prepared.jsonl"
    failures_path = run_dir / "failures.jsonl"
    add_trace_path = run_dir / "add_trace.jsonl"
    service_log_path = run_dir / "reme_service.log"
    for path in (retrieval_path, prepared_path, failures_path, add_trace_path):
        if path.exists():
            path.unlink()
        path.touch()

    source_manifest = dataset_path.with_name("manifest.json")
    dataset_manifest_path = run_dir / "dataset_manifest.json"
    if source_manifest.is_file():
        shutil.copy2(source_manifest, dataset_manifest_path)
        source_manifest_data = json.loads(source_manifest.read_text(encoding="utf-8"))
    else:
        source_manifest_data = {}
        dataset_manifest_path.write_text(
            json.dumps(
                {
                    "dataset_id": dataset_path.stem,
                    "dataset_sha256": sha256_file(dataset_path),
                    "selected_case_ids": [case["case_id"] for case in cases],
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

    dataset_validation = freeze_dataset_integrity(
        dataset_path,
        run_dir,
        cases,
        source_case_count=len(all_cases),
    )
    eval_code = git_metadata(REPO_ROOT)
    eval_code_snapshot = snapshot_eval_code(run_dir, eval_code)

    run_config = {
        "dataset": str(dataset_path),
        "dataset_format": dataset_path.suffix.lower() or "json",
        "memory_backend": "ReMe",
        "memory_version": reme_version(),
        "retrieval_backend": "BM25" if args.vector_weight == 0.0 else "ReMe configured hybrid",
        "model": args.model,
        "reme_config": str(config_path),
        "vector_weight": args.vector_weight,
        "embedding_enabled": args.vector_weight != 0.0,
        "llm_enabled": False,
        "requested_cases": len(cases),
        "selected_case_ids": [case["case_id"] for case in cases],
        "dataset_name": source_manifest_data.get("source_dataset", {}).get("name", dataset_path.stem),
        "dataset_version": source_manifest_data.get("dataset_id", dataset_path.parent.name),
        "dataset_sha256": sha256_file(dataset_path),
        "selected_session_count": sum(len(case["sessions"]) for case in cases),
        "selected_turn_count": sum(
            len(session["messages"]) for case in cases for session in case["sessions"]
        ),
        "selected_evidence_session_count": sum(len(case["evidence_session_ids"]) for case in cases),
        "start": args.start,
        "shuffle": args.shuffle,
        "seed": args.seed,
        "top_k": args.top_k,
        "search_multiplier": args.search_multiplier,
        "min_score": args.min_score,
        "reme_command": command,
        "reme_config_sha256": sha256_file(config_path),
        "eval_code_commit": eval_code["commit"],
        "eval_code_dirty": eval_code["dirty"],
        "eval_code_snapshot": eval_code_snapshot,
        "dataset_validation": str(run_dir / "dataset_validation.json"),
        "dataset_validation_status": dataset_validation["status"],
        "start_time_utc": run_started_at.isoformat(),
    }
    (run_dir / "run_config.json").write_text(json.dumps(run_config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    successes: list[dict[str, Any]] = []
    add_rows: list[dict[str, Any]] = []
    for case_index, case in enumerate(cases):
        case_id = case["case_id"]
        workspace = workspace_root / f"{case_index:04d}_{safe_name(case_id)}"
        if workspace.exists():
            shutil.rmtree(workspace)
        workspace.mkdir(parents=True, exist_ok=True)
        add_started = time.perf_counter()
        path_map = write_case_workspace(workspace, case)
        add_latency_ms = (time.perf_counter() - add_started) * 1000
        session_ids = [session["session_id"] for session in case["sessions"]]
        duplicate_session_ids = sorted(
            ident for ident in set(session_ids) if session_ids.count(ident) > 1
        )
        empty_session_ids = [
            session["session_id"]
            for session in case["sessions"]
            if not any(str(message.get("content", "")).strip() for message in session["messages"])
        ]
        written_files = list((workspace / "daily" / safe_name(case_id)).glob("*.md"))
        added_session_ids = [path_map[path.name] for path in written_files]
        added_evidence_ids = sorted(set(added_session_ids) & set(case["evidence_session_ids"]))
        add_row: dict[str, Any] = {
            "case_id": case_id,
            "add_mode": "filesystem_session_ingest",
            "expected_sessions": len(case["sessions"]),
            "added_sessions": len(written_files),
            "expected_turns": sum(len(session["messages"]) for session in case["sessions"]),
            "added_turns": sum(len(session["messages"]) for session in case["sessions"]),
            "expected_evidence_sessions": len(case["evidence_session_ids"]),
            "added_evidence_sessions": len(added_evidence_ids),
            "failed_session_ids": sorted(set(session_ids) - set(added_session_ids)),
            "duplicate_session_ids": duplicate_session_ids,
            "empty_content_session_ids": empty_session_ids,
            "namespace": case_id,
            "user_id": "NOT_APPLICABLE",
            "workspace": str(workspace),
            "add_request_count": len(case["sessions"]),
            "add_latency_ms": add_latency_ms,
            "add_status": "PASS" if len(written_files) == len(case["sessions"]) else "FAIL",
            "add_error": None,
            "index_status": "NOT_RUN",
            "embedding_status": "NOT_APPLICABLE" if not args.vector_weight else "NOT_RECORDED",
            "embedding_call_count": 0 if not args.vector_weight else "NOT_RECORDED",
            "embedding_failure_count": 0 if not args.vector_weight else "NOT_RECORDED",
            "extraction_status": "NOT_APPLICABLE",
            "extraction_call_count": 0,
            "extraction_failure_count": 0,
        }
        port = args.base_port + case_index
        process: subprocess.Popen[str] | None = None
        log_file: Any = None
        print(f"[{case_index + 1}/{len(cases)}] case={case_id}", flush=True)
        current_stage = "service_start"
        try:
            process, log_file = start_reme(command, workspace, port, config_path, service_log_path)
            wait_for_reme(port, args.startup_timeout)
            current_stage = "index"
            reindex_start = time.perf_counter()
            reindex_response = http_post(port, "reindex", {}, timeout=300)
            reindex_latency_ms = (time.perf_counter() - reindex_start) * 1000
            raw_reindex_path = raw_reindex_dir / f"{case_index:04d}_{safe_name(case_id)}.json"
            raw_reindex_path.write_text(
                json.dumps(reindex_response, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
            )
            if isinstance(reindex_response, dict) and reindex_response.get("success") is False:
                raise RuntimeError(f"ReMe reindex failed: {reindex_response.get('answer', '')}")
            index_results = find_index_results(reindex_response)
            health_response = http_post(port, "health_check", {}, timeout=30)
            index_health = find_index_health(health_response)
            index_failures = [item for item in index_results if item.get("success") is False]
            add_row.update(
                {
                    "index_status": "PASS" if not index_failures else "FAIL",
                    "index_request_count": 1,
                    "index_http_status": 200,
                    "index_latency_ms": reindex_latency_ms,
                    "indexed_document_count": index_health.get("n_nodes", len(index_results) or len(written_files)),
                    "indexed_chunk_count": index_health.get("n_chunks", "NOT_RECORDED"),
                    "chunks_with_embedding": index_health.get("n_chunks_with_embedding", 0),
                    "embedding_status": "NOT_APPLICABLE" if not args.vector_weight else "RECORDED_BY_REME_HEALTH",
                    "index_failed_paths": [str(item.get("path", "")) for item in index_failures],
                    "raw_reindex_file": str(raw_reindex_path),
                }
            )
            append_jsonl(add_trace_path, add_row)
            add_rows.append(add_row)

            search_limit = max(args.top_k, args.top_k * args.search_multiplier)
            current_stage = "search"
            search_start = time.perf_counter()
            search_response = http_post(
                port,
                "search",
                {"query": case["question"], "limit": search_limit, "min_score": args.min_score},
                timeout=120,
            )
            search_latency_ms = (time.perf_counter() - search_start) * 1000
            raw_search_path = raw_search_dir / f"{case_index:04d}_{safe_name(case_id)}.json"
            raw_search_path.write_text(json.dumps(search_response, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            raw_results = find_results(search_response) or []
            retrieved = deduplicate_sessions(raw_results, args.top_k, path_map)
            session_map = {session["session_id"]: session for session in case["sessions"]}
            for item in retrieved:
                session = session_map.get(item["session_id"], {})
                item["timestamp"] = str(session.get("timestamp", ""))
            metrics = evaluate_retrieval(retrieved, case["evidence_session_ids"])
            cut_metrics = {
                k: retrieval_metrics_at_k(retrieved, case["evidence_session_ids"], k)
                for k in (1, 3, 5, 10)
                if k <= args.top_k
            }
            evidence_ranks = [
                int(item["rank"])
                for item in retrieved
                if item["session_id"] in set(case["evidence_session_ids"])
            ]
            row = {
                "case_id": case_id,
                "question_type": case["question_type"],
                "question": case["question"],
                "question_date": case["question_date"],
                "gold_answer": case["gold_answer"],
                "session_count": len(case["sessions"]),
                "evidence_session_ids": case["evidence_session_ids"],
                "retrieved": retrieved,
                "raw_result_count": len(raw_results),
                "hit_at_k": metrics["hit"],
                "recall_at_k": metrics["recall"],
                "mrr": metrics["mrr"],
                "metrics_by_k": {str(k): value for k, value in cut_metrics.items()},
                "mean_evidence_rank": mean(evidence_ranks),
                "retrieved_evidence_count": len(evidence_ranks),
                "missing_evidence_count": len(case["evidence_session_ids"]) - len(set(
                    item["session_id"] for item in retrieved if item["session_id"] in set(case["evidence_session_ids"])
                )),
                "index_latency_ms": reindex_latency_ms,
                "search_latency_ms": search_latency_ms,
                "search_status": "PASS",
                "search_request_count": 1,
                "search_http_status": 200,
                "search_retry_count": 0,
                "returned_session_count": len(retrieved),
                "raw_search_file": str(raw_search_path),
            }
            append_jsonl(retrieval_path, row)
            append_jsonl(
                prepared_path,
                {
                    "id": case_id,
                    "question": case["question"],
                    "question_date": case["question_date"],
                    "gold_answer": case["gold_answer"],
                    "question_type": case["question_type"],
                    "answer_context_schema": "structured-memory-v1",
                    "retrieved_context": [render_answer_context(item) for item in retrieved],
                    "retrieved_context_metadata": [
                        {
                            "rank": item["rank"],
                            "session_id": item["session_id"],
                            "timestamp": item["timestamp"],
                            "score": item["score"],
                        }
                        for item in retrieved
                    ],
                },
            )
            successes.append(row)
            print(
                f"  hit@{args.top_k}={metrics['hit']} recall@{args.top_k}={metrics['recall']} "
                f"search={search_latency_ms:.1f}ms",
                flush=True,
            )
        except Exception as exc:
            if add_row not in add_rows:
                if current_stage in {"service_start", "index"}:
                    add_row["index_status"] = "FAIL"
                add_row["index_error"] = str(exc) if current_stage == "index" else None
                append_jsonl(add_trace_path, add_row)
                add_rows.append(add_row)
            append_jsonl(
                failures_path,
                {
                    "case_id": case_id,
                    "case_index": case_index,
                    "stage": current_stage,
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                },
            )
            print(f"  FAILED: {type(exc).__name__}: {exc}", flush=True)
        finally:
            if process is not None and log_file is not None:
                stop_reme(process, log_file)
            if workspace.exists() and not args.keep_workspaces:
                shutil.rmtree(workspace, ignore_errors=True)

    run_finished_at = datetime.now(timezone.utc)
    full_recall = [row for row in successes if row["recall_at_k"] == 1.0]
    partial_recall = [row for row in successes if isinstance(row["recall_at_k"], (int, float)) and 0 < row["recall_at_k"] < 1]
    zero_recall = [row for row in successes if row["recall_at_k"] == 0.0]
    type_breakdown: dict[str, Any] = {}
    for question_type in sorted({row["question_type"] for row in successes}):
        rows = [row for row in successes if row["question_type"] == question_type]
        type_breakdown[question_type] = {
            "case_count": len(rows),
            f"hit_at_{args.top_k}": mean(row["hit_at_k"] for row in rows),
            f"recall_at_{args.top_k}": mean(row["recall_at_k"] for row in rows),
            "mrr": mean(row["mrr"] for row in rows),
            "avg_search_latency_ms": mean(row["search_latency_ms"] for row in rows),
        }
    indexed_document_count = sum(
        int(row["indexed_document_count"])
        for row in add_rows
        if isinstance(row.get("indexed_document_count"), (int, float))
    )
    indexed_chunk_count = sum(
        int(row["indexed_chunk_count"])
        for row in add_rows
        if isinstance(row.get("indexed_chunk_count"), (int, float))
    )
    added_session_count = sum(int(row["added_sessions"]) for row in add_rows)
    chunks_with_embedding = sum(
        int(row["chunks_with_embedding"])
        for row in add_rows
        if isinstance(row.get("chunks_with_embedding"), (int, float))
    )
    summary = {
        "run_id": run_id,
        "dataset": str(dataset_path),
        "requested_cases": len(cases),
        "successful_cases": len(successes),
        "failed_cases": len(cases) - len(successes),
        "start_time_utc": run_started_at.isoformat(),
        "end_time_utc": run_finished_at.isoformat(),
        "duration_ms": (run_finished_at - run_started_at).total_seconds() * 1000,
        "add_success_rate": mean(1 if row["add_status"] == "PASS" else 0 for row in add_rows),
        "added_sessions": added_session_count,
        "failed_add_sessions": sum(len(row["failed_session_ids"]) for row in add_rows),
        "added_turns": sum(int(row["added_turns"]) for row in add_rows),
        "evidence_add_success_rate": (
            sum(int(row["added_evidence_sessions"]) for row in add_rows)
            / sum(int(row["expected_evidence_sessions"]) for row in add_rows)
            if sum(int(row["expected_evidence_sessions"]) for row in add_rows)
            else None
        ),
        "duplicate_add_count": sum(len(row["duplicate_session_ids"]) for row in add_rows),
        "empty_content_add_count": sum(len(row["empty_content_session_ids"]) for row in add_rows),
        "add_latency_ms": {
            "avg": mean(row["add_latency_ms"] for row in add_rows),
            "p50": percentile((row["add_latency_ms"] for row in add_rows), 0.50),
            "p95": percentile((row["add_latency_ms"] for row in add_rows), 0.95),
            "p99": percentile((row["add_latency_ms"] for row in add_rows), 0.99),
        },
        "index_success_rate": mean(1 if row["index_status"] == "PASS" else 0 for row in add_rows),
        "indexed_document_count": indexed_document_count,
        "indexed_chunk_count": indexed_chunk_count,
        "average_chunks_per_session": indexed_chunk_count / added_session_count if added_session_count else None,
        "embedding": {
            "enabled": bool(args.vector_weight),
            "status": "NOT_APPLICABLE" if not args.vector_weight else "RECORDED_BY_REME_HEALTH",
            "call_count": 0 if not args.vector_weight else "NOT_RECORDED",
            "failure_count": 0 if not args.vector_weight else "NOT_RECORDED",
            "chunks_with_embedding": chunks_with_embedding,
        },
        "extraction": {
            "enabled": False,
            "status": "NOT_APPLICABLE",
            "call_count": 0,
            "failure_count": 0,
        },
        "index_latency_ms": {
            "avg": mean(row.get("index_latency_ms") for row in add_rows),
            "p50": percentile((row.get("index_latency_ms") for row in add_rows), 0.50),
            "p95": percentile((row.get("index_latency_ms") for row in add_rows), 0.95),
            "p99": percentile((row.get("index_latency_ms") for row in add_rows), 0.99),
        },
        "search_success_rate": len(successes) / len(cases),
        "search_request_count": len(successes),
        "empty_search_result_count": sum(not row["retrieved"] for row in successes),
        "search_retry_count": sum(int(row.get("search_retry_count", 0)) for row in successes),
        "search_latency_ms": {
            "avg": mean(row["search_latency_ms"] for row in successes),
            "p50": percentile((row["search_latency_ms"] for row in successes), 0.50),
            "p95": percentile((row["search_latency_ms"] for row in successes), 0.95),
            "p99": percentile((row["search_latency_ms"] for row in successes), 0.99),
        },
        f"hit_at_{args.top_k}": mean(row["hit_at_k"] for row in successes),
        f"recall_at_{args.top_k}": mean(row["recall_at_k"] for row in successes),
        "mrr": mean(row["mrr"] for row in successes),
        "avg_index_latency_ms": mean(row["index_latency_ms"] for row in successes),
        "avg_search_latency_ms": mean(row["search_latency_ms"] for row in successes),
        "full_evidence_recall_rate": len(full_recall) / len(successes) if successes else None,
        "partial_evidence_rate": len(partial_recall) / len(successes) if successes else None,
        "zero_evidence_rate": len(zero_recall) / len(successes) if successes else None,
        "question_type_breakdown": type_breakdown,
        "api_stability": {
            "memory_add_requests": sum(int(row["add_request_count"]) for row in add_rows),
            "memory_index_requests": sum(int(row.get("index_request_count", 0)) for row in add_rows),
            "memory_search_requests": len(successes),
            "http_2xx": sum(1 for row in add_rows if row.get("index_http_status") == 200) + len(successes),
            "http_4xx": 0,
            "http_5xx": 0,
            "timeouts": sum(1 for row in _read_failure_rows(failures_path) if "timeout" in str(row.get("error_type", "")).lower()),
            "retries": 0,
        },
    }
    (run_dir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("\n=== ReMe Retrieval Eval Finished ===")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"Results: {run_dir}")
    return 0 if len(successes) == len(cases) else 2


if __name__ == "__main__":
    raise SystemExit(run(parse_args()))
