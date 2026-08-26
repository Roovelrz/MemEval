"""Organize one eval run into detailed provenance and concise review folders."""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

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

    html_manifest = build_html_report(detailed_dir, dashboard_dir)
    summary_entrypoint.write_text(_summary_entrypoint(), encoding="utf-8", newline="")
    trace_summary = _read_json(trace_json_path)
    markdown_source = detailed_dir / "trace" / "trace_summary.md"
    if markdown_source.is_file():
        shutil.copy2(markdown_source, summary_dir / "trace_summary.md")
    concise_path = summary_dir / "summary.json"
    concise_path.write_text(
        json.dumps(_concise_summary(trace_summary), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
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
