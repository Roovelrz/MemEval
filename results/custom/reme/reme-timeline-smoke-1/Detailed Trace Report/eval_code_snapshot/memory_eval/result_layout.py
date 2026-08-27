"""Organize one eval run into detailed provenance and concise review folders."""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from memory_eval.dataset_registry import load_dataset_registry
from memory_eval.html_report import build_html_report


DETAILED_DIR_NAME = "Detailed Trace Report"
SUMMARY_DIR_NAME = "Trace Summary"


def _summary_entrypoint() -> str:
    return """<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta http-equiv="refresh" content="0; url=Dashboard/index.html">
  <title>Memory Eval Trace Summary</title>
  <style>
    body { margin: 0; display: grid; min-height: 100vh; place-items: center; background: #f3f6fb; color: #182033; font-family: "Segoe UI", "Microsoft YaHei", sans-serif; }
    main { padding: 32px; border: 1px solid #dfe5ef; border-radius: 14px; background: white; text-align: center; box-shadow: 0 10px 30px rgba(26,39,73,.08); }
    a { color: #2563eb; }
  </style>
</head>
<body>
  <main><h1>Memory Eval Trace Summary</h1><p>正在打开 Dashboard……</p><a href="Dashboard/index.html">如果没有自动跳转，请点击这里</a></main>
</body>
</html>
"""


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return value


def _concise_summary(trace_summary: dict[str, Any]) -> dict[str, Any]:
    """Keep only high-signal Run metrics; per-case details remain in Detailed Trace Report."""

    return {
        "schema_version": "memory_eval_concise_summary_v1",
        "run_info": trace_summary.get("run_info"),
        "dataset": trace_summary.get("dataset"),
        "dataset_id": trace_summary.get("dataset_id"),
        "dataset_name": trace_summary.get("dataset_name"),
        "dataset_version": trace_summary.get("dataset_version"),
        "source_dataset": trace_summary.get("source_dataset"),
        "language": trace_summary.get("language"),
        "translated": trace_summary.get("translated"),
        "case_count": trace_summary.get("case_count"),
        "total_cases": trace_summary.get("total_cases"),
        "successful_pipeline_cases": trace_summary.get("successful_pipeline_cases"),
        "failed_pipeline_cases": trace_summary.get("failed_pipeline_cases"),
        "top_k": trace_summary.get("top_k"),
        "hit_at_k": trace_summary.get("hit_at_k"),
        "recall_at_k": trace_summary.get("recall_at_k"),
        "mrr": trace_summary.get("mrr"),
        "answer_accuracy": trace_summary.get("answer_accuracy"),
        "pipeline_success_rate": trace_summary.get("pipeline_success_rate"),
        "grounded_end_to_end_accuracy": trace_summary.get("grounded_end_to_end_accuracy"),
        "quadrants": trace_summary.get("quadrants"),
        "root_cause_distribution": trace_summary.get("root_cause_distribution"),
        "question_type_breakdown": trace_summary.get("question_type_breakdown"),
        "evidence_count_breakdown": trace_summary.get("evidence_count_breakdown"),
        "latency_breakdown": trace_summary.get("latency_breakdown"),
        "llm_cost": trace_summary.get("llm_cost"),
        "api_stability": trace_summary.get("api_stability"),
        "conclusions": trace_summary.get("conclusions"),
        "comparison": trace_summary.get("comparison"),
    }


def _results_root(path: Path) -> Path | None:
    for candidate in (path, *path.parents):
        if candidate.name.lower() == "results":
            return candidate
    return None


def _benchmark_row(summary_path: Path) -> dict[str, Any] | None:
    try:
        summary = _read_json(summary_path)
    except (OSError, ValueError, json.JSONDecodeError):
        return None
    dataset_id = summary.get("dataset_id")
    if not dataset_id or dataset_id == "NOT_RECORDED":
        return None
    run_info = summary.get("run_info") if isinstance(summary.get("run_info"), dict) else {}
    registered = load_dataset_registry().get(str(dataset_id), {})
    summary_dir = summary_path.parent
    return {
        "dataset_id": dataset_id,
        "dataset_name": registered.get("dataset_name") or summary.get("dataset_name") or run_info.get("dataset_name") or dataset_id,
        "dataset_version": registered.get("version") or summary.get("dataset_version") or run_info.get("dataset_version"),
        "language": registered.get("language") or summary.get("language") or run_info.get("language"),
        "translated": registered.get("translated", summary.get("translated", run_info.get("translated"))),
        "run_id": run_info.get("run_id", summary_dir.parent.name),
        "case_count": summary.get("case_count", summary.get("total_cases")),
        "hit_at_k": summary.get("hit_at_k"),
        "recall_at_k": summary.get("recall_at_k"),
        "mrr": summary.get("mrr"),
        "answer_accuracy": summary.get("answer_accuracy"),
        "grounded_end_to_end_accuracy": summary.get("grounded_end_to_end_accuracy"),
        "pipeline_success_rate": summary.get("pipeline_success_rate"),
        "summary_dir": str(summary_dir.resolve()),
        "dashboard_dir": str((summary_dir / "Dashboard").resolve()),
        "modified_time": summary_path.stat().st_mtime,
    }


def _benchmark_catalog(results_root: Path) -> list[dict[str, Any]]:
    latest: dict[str, dict[str, Any]] = {}
    for summary_path in results_root.glob(f"**/{SUMMARY_DIR_NAME}/summary.json"):
        row = _benchmark_row(summary_path)
        if row is None:
            continue
        previous = latest.get(str(row["dataset_id"]))
        score = (int(row.get("case_count") or 0), float(row["modified_time"]))
        previous_score = (
            int(previous.get("case_count") or 0),
            float(previous["modified_time"]),
        ) if previous else (-1, -1.0)
        if score > previous_score:
            latest[str(row["dataset_id"])] = row
    preferred = {"LongMemEval-EN-Full": 0, "LongMemEval-ZH-20-v0.1": 1}
    return sorted(
        latest.values(),
        key=lambda item: (preferred.get(str(item["dataset_id"]), 99), str(item["dataset_id"])),
    )


def _refresh_benchmark_dashboards(current_summary_dir: Path) -> dict[str, Any]:
    results_root = _results_root(current_summary_dir)
    current_row = _benchmark_row(current_summary_dir / "summary.json")
    if current_row is None:
        raise ValueError(f"Cannot build benchmark metadata from {current_summary_dir}")
    catalog = _benchmark_catalog(results_root) if results_root else [current_row]
    targets = {str(item["summary_dir"]): item for item in catalog}
    targets[str(current_row["summary_dir"])] = current_row
    current_manifest: dict[str, Any] | None = None
    for target in targets.values():
        target_summary_dir = Path(str(target["summary_dir"]))
        detailed_dir = target_summary_dir.parent / DETAILED_DIR_NAME
        if not (detailed_dir / "trace" / "trace_summary.json").is_file():
            continue
        local_catalog = [
            target if item["dataset_id"] == target["dataset_id"] else item
            for item in catalog
        ]
        if not any(item["dataset_id"] == target["dataset_id"] for item in catalog):
            local_catalog.append(target)
        dashboard_dir = target_summary_dir / "Dashboard"
        manifest = build_html_report(detailed_dir, dashboard_dir, local_catalog)
        (target_summary_dir / "Dashboard.html").write_text(
            _summary_entrypoint(), encoding="utf-8", newline=""
        )
        if target_summary_dir == current_summary_dir:
            current_manifest = manifest
    if current_manifest is None:
        raise RuntimeError(f"Current dashboard was not rebuilt: {current_summary_dir}")
    return current_manifest


def _refresh_end_to_end_summary(
    path: Path,
    run_dir: Path,
    detailed_dir: Path,
    summary_dir: Path,
    dashboard_dir: Path,
) -> None:
    if not path.is_file():
        return
    summary = _read_json(path)
    retrieval_summary_path = detailed_dir / "summary.json"
    answer_summary_path = detailed_dir / "answer_summary.json"
    judge_summary_path = detailed_dir / "judge_summary.json"
    retrieval_summary = _read_json(retrieval_summary_path) if retrieval_summary_path.is_file() else None
    answer_summary = _read_json(answer_summary_path) if answer_summary_path.is_file() else None
    judge_summary = _read_json(judge_summary_path) if judge_summary_path.is_file() else None

    def stage_code(
        stage: dict[str, Any] | None,
        requested_key: str,
        successful_key: str,
        failed_key: str,
    ) -> int | None:
        if stage is None:
            return None
        requested = stage.get(requested_key)
        successful = stage.get(successful_key)
        failed = stage.get(failed_key)
        return 0 if requested == successful and failed == 0 else 2

    summary["retrieval"] = retrieval_summary
    summary["answer"] = answer_summary
    summary["judge"] = judge_summary
    summary["stage_exit_codes"] = {
        "retrieval": stage_code(
            retrieval_summary, "requested_cases", "successful_cases", "failed_cases"
        ),
        "answer": stage_code(
            answer_summary, "requested_rows", "successful_rows", "failed_rows"
        ),
        "judge": stage_code(
            judge_summary, "requested_rows", "successful_rows", "failed_rows"
        ),
        "trace": 0,
        "html": 0,
    }
    refreshed_at = datetime.now(timezone.utc)
    summary["recovered_at_utc"] = refreshed_at.isoformat()
    summary["end_time_utc"] = refreshed_at.isoformat()
    try:
        started_at = datetime.fromisoformat(str(summary.get("start_time_utc", "")))
    except ValueError:
        started_at = None
    if started_at is not None:
        summary["duration_ms"] = (refreshed_at - started_at).total_seconds() * 1000
    summary["run_dir"] = str(run_dir)
    summary["detailed_trace_report_dir"] = str(detailed_dir)
    summary["trace_summary_dir"] = str(summary_dir)
    summary["artifacts"] = {
        "prepared": str(detailed_dir / "prepared.jsonl"),
        "answers": str(detailed_dir / "answers.jsonl"),
        "scores": str(detailed_dir / "scores.jsonl"),
        "trace_summary": str(detailed_dir / "trace" / "trace_summary.md"),
        "trace_index": str(detailed_dir / "trace" / "trace_index.md"),
        "judge_review": str(detailed_dir / "trace" / "judge_review.md"),
        "html_dashboard": str(summary_dir / "Dashboard.html"),
        "html_report_manifest": str(dashboard_dir / "report_manifest.json"),
        "concise_summary": str(summary_dir / "summary.json"),
    }
    path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def refresh_result_layout(run_dir: str | Path) -> dict[str, Any]:
    """Refresh Trace Summary artifacts for an already organized resumable Run."""

    run_dir = Path(run_dir).resolve()
    detailed_dir = run_dir / DETAILED_DIR_NAME
    summary_dir = run_dir / SUMMARY_DIR_NAME
    dashboard_dir = summary_dir / "Dashboard"
    trace_json_path = detailed_dir / "trace" / "trace_summary.json"
    if not trace_json_path.is_file():
        raise FileNotFoundError(f"Trace summary not found: {trace_json_path}")

    summary_dir.mkdir(parents=True, exist_ok=True)
    trace_summary = _read_json(trace_json_path)
    markdown_source = detailed_dir / "trace" / "trace_summary.md"
    if markdown_source.is_file():
        shutil.copy2(markdown_source, summary_dir / "trace_summary.md")
    concise_path = summary_dir / "summary.json"
    concise_path.write_text(
        json.dumps(_concise_summary(trace_summary), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    html_manifest = _refresh_benchmark_dashboards(summary_dir)
    _refresh_end_to_end_summary(
        detailed_dir / "end_to_end_summary.json",
        run_dir,
        detailed_dir,
        summary_dir,
        dashboard_dir,
    )

    refreshed_at = datetime.now(timezone.utc).isoformat()
    layout_manifest_path = detailed_dir / "result_layout_manifest.json"
    layout_manifest = _read_json(layout_manifest_path) if layout_manifest_path.is_file() else {}
    layout_manifest.update(
        {
            "schema_version": "memory_eval_result_layout_v1",
            "refreshed_at_utc": refreshed_at,
            "run_dir": str(run_dir),
            "detailed_trace_report_dir": str(detailed_dir),
            "trace_summary_dir": str(summary_dir),
            "dashboard_dir": str(dashboard_dir),
            "summary_entrypoint": str(summary_dir / "Dashboard.html"),
            "html_page_count": html_manifest["page_count"],
            "case_page_count": html_manifest["case_page_count"],
            "concise_summary": str(concise_path),
        }
    )
    layout_manifest_path.write_text(
        json.dumps(layout_manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    layout_manifest["layout_manifest"] = str(layout_manifest_path)
    return layout_manifest


def organize_result_layout(run_dir: str | Path) -> dict[str, Any]:
    """Move Run artifacts into the fixed two-folder layout and rebuild HTML."""

    run_dir = Path(run_dir).resolve()
    if not run_dir.is_dir():
        raise FileNotFoundError(f"Run directory not found: {run_dir}")

    detailed_dir = (run_dir / DETAILED_DIR_NAME).resolve()
    summary_dir = (run_dir / SUMMARY_DIR_NAME).resolve()
    dashboard_dir = (summary_dir / "Dashboard").resolve()
    if detailed_dir.parent != run_dir or summary_dir.parent != run_dir:
        raise ValueError("Result layout targets must stay directly inside the Run directory")

    moved: list[dict[str, str]] = []
    detailed_dir.mkdir(parents=True, exist_ok=True)
    summary_dir.mkdir(parents=True, exist_ok=True)
    legacy_report = run_dir / "report"
    if legacy_report.exists():
        if dashboard_dir.exists():
            raise FileExistsError(
                f"Cannot move legacy report: dashboard destination exists: {dashboard_dir}"
            )
        shutil.move(str(legacy_report), str(dashboard_dir))
        moved.append(
            {"source": "report", "destination": f"{SUMMARY_DIR_NAME}/Dashboard"}
        )

    for source in sorted(run_dir.iterdir(), key=lambda path: path.name.lower()):
        if source.name in {DETAILED_DIR_NAME, SUMMARY_DIR_NAME}:
            continue
        destination = detailed_dir / source.name
        if destination.exists():
            raise FileExistsError(
                f"Cannot organize {source}: destination already exists: {destination}"
            )
        shutil.move(str(source), str(destination))
        moved.append(
            {
                "source": source.name,
                "destination": f"{DETAILED_DIR_NAME}/{source.name}",
            }
        )

    dashboard_dir.mkdir(parents=True, exist_ok=True)
    summary_entrypoint = summary_dir / "Dashboard.html"
    legacy_entrypoint = summary_dir / "index.html"
    if legacy_entrypoint.is_file():
        legacy_entrypoint.replace(summary_entrypoint)
    for source in sorted(summary_dir.iterdir(), key=lambda path: path.name.lower()):
        if source.name in {"Dashboard", "Dashboard.html", "summary.json", "trace_summary.md"}:
            continue
        destination = dashboard_dir / source.name
        if destination.exists():
            raise FileExistsError(
                f"Cannot consolidate Dashboard: destination already exists: {destination}"
            )
        shutil.move(str(source), str(destination))

    trace_json_path = detailed_dir / "trace" / "trace_summary.json"
    if not trace_json_path.is_file():
        raise FileNotFoundError(f"Trace summary not found after organization: {trace_json_path}")

    trace_summary = _read_json(trace_json_path)
    markdown_source = detailed_dir / "trace" / "trace_summary.md"
    if markdown_source.is_file():
        shutil.copy2(markdown_source, summary_dir / "trace_summary.md")
    concise_path = summary_dir / "summary.json"
    concise_path.write_text(
        json.dumps(_concise_summary(trace_summary), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    html_manifest = _refresh_benchmark_dashboards(summary_dir)
    _refresh_end_to_end_summary(
        detailed_dir / "end_to_end_summary.json",
        run_dir,
        detailed_dir,
        summary_dir,
        dashboard_dir,
    )

    layout_manifest = {
        "schema_version": "memory_eval_result_layout_v1",
        "organized_at_utc": datetime.now(timezone.utc).isoformat(),
        "run_dir": str(run_dir),
        "detailed_trace_report_dir": str(detailed_dir),
        "trace_summary_dir": str(summary_dir),
        "dashboard_dir": str(dashboard_dir),
        "summary_entrypoint": str(summary_entrypoint),
        "moved_entries": moved,
        "html_page_count": html_manifest["page_count"],
        "case_page_count": html_manifest["case_page_count"],
        "concise_summary": str(concise_path),
    }
    layout_manifest_path = detailed_dir / "result_layout_manifest.json"
    layout_manifest_path.write_text(
        json.dumps(layout_manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    layout_manifest["layout_manifest"] = str(layout_manifest_path)
    return layout_manifest
