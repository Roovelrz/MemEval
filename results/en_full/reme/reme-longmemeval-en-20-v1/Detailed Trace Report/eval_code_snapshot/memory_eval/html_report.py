"""Render a local static dashboard from Trace artifacts without re-evaluating cases."""

from __future__ import annotations

import hashlib
import html
import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


NOT_RECORDED = "NOT_RECORDED"
CAPABILITY_LABELS = {
    "knowledge-update": "知识更新",
    "multi-session": "多会话推理",
    "single-session-assistant": "单会话助手信息",
    "single-session-preference": "单会话偏好",
    "single-session-user": "单会话用户信息",
    "temporal-reasoning": "时间推理",
}
ROOT_CAUSES = (
    "PASS",
    "DATA_ERROR",
    "ADD_FAILURE",
    "INDEX_FAILURE",
    "RETRIEVAL_MISS",
    "RETRIEVAL_PARTIAL",
    "RETRIEVAL_LOW_RANK",
    "RETRIEVAL_WRONG_CHUNK",
    "CONTEXT_LOSS",
    "CONTEXT_TRUNCATION",
    "ANSWER_FAILURE",
    "JUDGE_SUSPECT",
    "API_FAILURE",
    "TIMEOUT",
    "PIPELINE_FAILURE",
)
ROOT_PRIORITY = {
    name: index
    for index, name in enumerate(
        (
            "PIPELINE_FAILURE",
            "API_FAILURE",
            "ADD_FAILURE",
            "INDEX_FAILURE",
            "RETRIEVAL_MISS",
            "RETRIEVAL_WRONG_CHUNK",
            "RETRIEVAL_PARTIAL",
            "CONTEXT_LOSS",
            "CONTEXT_TRUNCATION",
            "ANSWER_FAILURE",
            "JUDGE_SUSPECT",
            "RETRIEVAL_LOW_RANK",
            "DATA_ERROR",
            "TIMEOUT",
            "PASS",
        )
    )
}
ASSET_DIR = Path(__file__).resolve().with_name("html_assets")


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return value


def _safe_name(value: object) -> str:
    cleaned = "".join(char if char.isalnum() or char in "._-" else "_" for char in str(value))
    return cleaned.strip("._") or "unnamed"


def _slug(value: object) -> str:
    return _safe_name(str(value).lower().replace("_", "-"))


def _escape(value: object) -> str:
    return html.escape(str(value), quote=True)


def _is_rate_field(name: str) -> bool:
    lowered = name.lower()
    return any(
        token in lowered
        for token in ("rate", "accuracy", "hit_at", "recall_at", "precision", "mrr")
    ) and not lowered.endswith(("count", "rank"))


def _scalar(value: object, field: str = "") -> str:
    if value is None:
        return '<span class="value-missing">NOT_RECORDED</span>'
    if isinstance(value, bool):
        return '<span class="status-pass">true</span>' if value else '<span class="status-muted">false</span>'
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        raw = f"{value:.4f}" if isinstance(value, float) else str(value)
        if _is_rate_field(field) and 0 <= float(value) <= 1:
            return f'<span class="metric-value">{value * 100:.1f}%</span><span class="raw-value">{raw}</span>'
        return _escape(raw)
    text = str(value)
    css = "value-missing" if text in {NOT_RECORDED, "NOT_APPLICABLE"} else ""
    return f'<span class="{css}">{_escape(text)}</span>' if css else _escape(text)


def _value(value: object, field: str = "") -> str:
    if isinstance(value, dict):
        rows = "".join(
            f'<div class="nested-row"><code>{_escape(key)}</code><span>{_value(item, str(key))}</span></div>'
            for key, item in value.items()
        )
        return f'<div class="nested-fields">{rows or _scalar(None)}</div>'
    if isinstance(value, list):
        if not value:
            return '<span class="status-muted">[]</span>'
        if all(not isinstance(item, (dict, list)) for item in value):
            return '<div class="tag-list">' + "".join(f'<span class="tag">{_scalar(item, field)}</span>' for item in value) + "</div>"
        return f'<pre class="json-block">{_escape(json.dumps(value, ensure_ascii=False, indent=2))}</pre>'
    return _scalar(value, field)


def _field_table(data: dict[str, Any], fields: Iterable[str] | None = None) -> str:
    names = list(fields) if fields is not None else list(data)
    rows = "".join(
        f"<tr><th><code>{_escape(name)}</code></th><td>{_value(data.get(name), name)}</td></tr>"
        for name in names
    )
    return f'<div class="table-wrap"><table class="field-table"><tbody>{rows}</tbody></table></div>'


def _metric_card(label: str, value: object, *, tone: str = "neutral", note: str = "") -> str:
    return (
        f'<article class="metric-card tone-{tone}"><div class="metric-label"><code>{_escape(label)}</code></div>'
        f'<div class="metric-number">{_scalar(value, label)}</div>'
        f'{f"<div class=\"metric-note\">{_escape(note)}</div>" if note else ""}</article>'
    )


def _case_link(case_id: object, prefix: str = "") -> str:
    return f'{prefix}cases/{_safe_name(case_id)}.html'


def _quadrant_code(value: object) -> str:
    text = str(value or "")
    return text[0].upper() if text and text[0].upper() in "ABCD" else "N"


def _status_badge(value: object) -> str:
    text = str(value if value is not None else NOT_RECORDED)
    normalized = text.upper()
    if normalized in {"PASS", "CORRECT", "TRUE", "A"}:
        tone = "pass"
    elif normalized in {NOT_RECORDED, "NOT_APPLICABLE", "NONE", "N"}:
        tone = "muted"
    else:
        tone = "fail"
    return f'<span class="status-badge status-{tone}">{_escape(text)}</span>'


def _nav(prefix: str, active: str) -> str:
    items = (
        ("home", "总览", "index.html"),
        ("quadrant", "四象限分析", "analysis/quadrant.html"),
        ("cases", "Case 追踪", "cases/index.html"),
        ("pipeline", "流程观测", "pipeline/add.html"),
        ("performance", "性能与时延", "performance/latency.html"),
        ("comparison", "版本对比", "comparison/index.html"),
        ("run-info", "运行信息", "run-info/index.html"),
    )
    links = "".join(
        f'<a class="nav-link {"active" if key == active else ""}" href="{prefix}{path}"><span>{label}</span></a>'
        for key, label, path in items
    )
    return f'<nav class="sidebar"><div class="brand"><span class="brand-mark">M</span><div><strong>Memory Eval</strong><small>Trace Dashboard</small></div></div>{links}</nav>'


def _benchmark_selector(summary: dict[str, Any], prefix: str) -> str:
    benchmarks = summary.get("_benchmark_runs", [])
    if not isinstance(benchmarks, list) or not benchmarks:
        return ""
    current_id = summary.get("dataset_id", summary.get("run_info", {}).get("dataset_id"))
    options = "".join(
        f'<option value="{_escape(prefix + str(item.get("href", "index.html")))}" '
        f'{"selected" if item.get("dataset_id") == current_id else ""}>'
        f'{_escape(item.get("dataset_name", item.get("dataset_id", NOT_RECORDED)))}</option>'
        for item in benchmarks
    )
    return (
        '<label class="benchmark-switch"><span>Benchmark</span>'
        f'<select data-benchmark-switch>{options}</select></label>'
    )


def _page(
    title: str,
    content: str,
    summary: dict[str, Any],
    *,
    depth: int = 1,
    active: str = "",
    subtitle: str = "",
    page_class: str = "",
) -> str:
    prefix = "../" * depth
    run_info = summary.get("run_info", {})
    run_id = run_info.get("run_id", NOT_RECORDED)
    benchmark_selector = _benchmark_selector(summary, prefix)
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{_escape(title)} · Memory Eval</title>
  <link rel="stylesheet" href="{prefix}assets/style.css">
</head>
<body class="{_escape(page_class)}">
  <button class="menu-button" type="button" data-menu-toggle aria-label="切换导航">☰</button>
  {_nav(prefix, active)}
  <main class="main-content">
    <header class="page-header">
      <div><p class="eyebrow">RUN · {_escape(run_id)}</p><h1>{_escape(title)}</h1>{f'<p>{_escape(subtitle)}</p>' if subtitle else ''}</div>
      <div class="header-actions">{benchmark_selector}<a class="button secondary" href="{prefix}trace_summary.md">查看 Markdown Trace</a></div>
    </header>
    {content}
    <footer>由现有 Trace 产物静态生成 · 不参与评测、判分或根因计算</footer>
  </main>
  <script src="{prefix}assets/app.js"></script>
</body>
</html>
"""


def _case_table(cases: list[dict[str, Any]], *, link_prefix: str = "", filters: bool = True) -> str:
    ordered = sorted(cases, key=lambda item: (ROOT_PRIORITY.get(str(item.get("root_cause")), 99), str(item.get("case_id"))))
    filter_html = ""
    if filters:
        controls = []
        for key in ("question_type", "root_cause", "answer_correct", "judge_label", "quadrant"):
            values = sorted({str(item.get(key, NOT_RECORDED)) for item in ordered})
            options = "".join(f'<option value="{_escape(value)}">{_escape(value)}</option>' for value in values)
            controls.append(f'<label><span>{_escape(key)}</span><select data-filter-key="{_escape(key)}"><option value="">全部</option>{options}</select></label>')
        filter_html = '<div class="filters"><label class="search-box"><span>搜索</span><input type="search" data-table-search placeholder="case_id / explanation"></label>' + "".join(controls) + "</div>"
    rows = []
    for case in ordered:
        attributes = " ".join(
            f'data-{key.replace("_", "-")}="{_escape(case.get(key, NOT_RECORDED))}"'
            for key in ("question_type", "root_cause", "answer_correct", "judge_label", "quadrant")
        )
        case_id = case.get("case_id", NOT_RECORDED)
        rows.append(
            f'<tr {attributes}><td><a class="case-link" href="{_case_link(case_id, link_prefix)}">{_escape(case_id)}</a></td>'
            f'<td>{_escape(case.get("question_type", NOT_RECORDED))}</td>'
            f'<td>{_scalar(case.get("hit_at_k"), "hit_at_k")}</td><td>{_scalar(case.get("recall_at_k"), "recall_at_k")}</td>'
            f'<td>{_scalar(case.get("mrr"), "mrr")}</td><td>{_scalar(case.get("first_evidence_rank"), "first_evidence_rank")}</td>'
            f'<td>{_status_badge(case.get("answer_correct"))}</td><td>{_status_badge(case.get("judge_label"))}</td>'
            f'<td><span class="quadrant q-{_quadrant_code(case.get("quadrant")).lower()}">{_escape(_quadrant_code(case.get("quadrant")))}</span></td>'
            f'<td>{_status_badge(case.get("root_cause"))}</td><td class="explanation-cell">{_escape(case.get("explanation", NOT_RECORDED))}</td></tr>'
        )
    return f"""{filter_html}<div class="table-wrap"><table class="data-table" data-filter-table>
<thead><tr><th>case_id</th><th>question_type</th><th>hit_at_k</th><th>recall_at_k</th><th>mrr</th><th>first_evidence_rank</th><th>answer_correct</th><th>judge_label</th><th>quadrant</th><th>root_cause</th><th>explanation</th></tr></thead>
<tbody>{''.join(rows)}</tbody></table></div><p class="table-count"><span data-visible-count>{len(rows)}</span> / {len(rows)} cases</p>"""


def _quadrant_payload(summary: dict[str, Any], cases: list[dict[str, Any]], prefix: str) -> dict[str, Any]:
    case_points = []
    for case in cases:
        code = _quadrant_code(case.get("quadrant"))
        case_points.append(
            {
                **case,
                "level": "case",
                "label": case.get("case_id"),
                "quadrant_code": code,
                "href": _case_link(case.get("case_id"), prefix),
            }
        )
    type_points = [
        {
            "level": "type",
            "label": question_type,
            "question_type": question_type,
            "root_cause": "AGGREGATED",
            "quadrant": "AGGREGATED",
            "quadrant_code": "N",
            "hit_at_k": values.get(f"hit_at_{summary.get('top_k', 10)}"),
            "recall_at_k": values.get(f"recall_at_{summary.get('top_k', 10)}"),
            "mrr": values.get("mrr"),
            "answer_correct": values.get("accuracy"),
            "judge_label": "AGGREGATED",
            "x": values.get(f"recall_at_{summary.get('top_k', 10)}"),
            "y": values.get("accuracy"),
            "href": f"{prefix}capabilities/{_slug(question_type)}.html",
        }
        for question_type, values in summary.get("question_type_breakdown", {}).items()
    ]
    run_points = [
        {
            "level": "run",
            "label": summary.get("run_info", {}).get("run_id", "run"),
            "question_type": "ALL",
            "root_cause": "AGGREGATED",
            "quadrant": "AGGREGATED",
            "quadrant_code": "N",
            "hit_at_k": summary.get("hit_at_k"),
            "recall_at_k": summary.get("recall_at_k"),
            "mrr": summary.get("mrr"),
            "answer_correct": summary.get("answer_accuracy"),
            "judge_label": "AGGREGATED",
            "x": summary.get("recall_at_k"),
            "y": summary.get("answer_accuracy"),
            "href": f"{prefix}run-info/index.html",
        }
    ]
    return {"case": case_points, "type": type_points, "run": run_points}


def _quadrant_chart(summary: dict[str, Any], cases: list[dict[str, Any]], *, prefix: str) -> str:
    payload = json.dumps(_quadrant_payload(summary, cases, prefix), ensure_ascii=False).replace("</", "<\\/")
    options = lambda key: "".join(
        f'<option value="{_escape(value)}">{_escape(value)}</option>'
        for value in sorted({str(case.get(key, NOT_RECORDED)) for case in cases})
    )
    return f"""<section class="panel quadrant-panel">
<div class="section-heading"><div><p class="eyebrow">INTERACTIVE ANALYSIS</p><h2>端到端能力四象限分析</h2></div>
<div class="segmented"><button class="active" data-chart-level="case">Case</button><button data-chart-level="type">Question Type</button><button data-chart-level="run">Run</button></div></div>
<div class="chart-filters"><label>question_type<select data-chart-filter="question_type"><option value="">全部</option>{options('question_type')}</select></label><label>root_cause<select data-chart-filter="root_cause"><option value="">全部</option>{options('root_cause')}</select></label><label>quadrant<select data-chart-filter="quadrant"><option value="">全部</option>{options('quadrant')}</select></label></div>
<div class="quadrant-layout"><div class="y-label">Answer PASS ↑</div><div class="quadrant-chart" data-quadrant-chart>
<div class="quadrant-zone zone-d"><strong>D</strong><span>检索失败 · 回答成功</span></div><div class="quadrant-zone zone-a"><strong>A</strong><span>检索成功 · 回答成功</span></div>
<div class="quadrant-zone zone-b"><strong>B</strong><span>检索失败 · 回答失败</span></div><div class="quadrant-zone zone-c"><strong>C</strong><span>检索成功 · 回答失败</span></div><div class="axis-x">Retrieval PASS →</div><div class="chart-points" data-chart-points></div></div></div>
<script type="application/json" data-chart-data>{payload}</script></section>"""


def _home(summary: dict[str, Any], cases: list[dict[str, Any]]) -> str:
    recall = summary.get("recall_at_k")
    mrr = summary.get("mrr")
    answer_accuracy = summary.get("answer_accuracy")
    grounded = summary.get("grounded_end_to_end_accuracy")
    retrieval_quality = recall * 0.6 + mrr * 0.4 if isinstance(recall, (int, float)) and isinstance(mrr, (int, float)) else None
    composite = retrieval_quality * 0.4 + answer_accuracy * 0.2 + grounded * 0.4 if all(isinstance(value, (int, float)) for value in (retrieval_quality, answer_accuracy, grounded)) else None
    composite_value = float(composite or 0)
    composite_label = f"{composite_value * 100:.1f}%" if composite is not None else NOT_RECORDED
    retrieval = summary.get("retrieval_stage", {})
    api = summary.get("api_stability", {})
    top_k = summary.get("top_k", 10)
    root_counts = summary.get("root_cause_distribution", {})
    nonzero_roots = [(name, int(root_counts.get(name, 0))) for name in ROOT_CAUSES if name != "PASS" and root_counts.get(name, 0)]
    root_cards = "".join(
        f'<a class="root-card" href="failures/{_slug(name)}.html"><span>{_status_badge(name)}</span><strong>{count}</strong></a>'
        for name, count in nonzero_roots
    ) or '<div class="empty-state">当前 Run 没有非 PASS 根因。</div>'
    capabilities = "".join(
        f'<a class="capability-card" href="capabilities/{_slug(name)}.html"><span>{_escape(CAPABILITY_LABELS.get(name, name))}</span><code>{_escape(name)}</code><div class="capability-score">{_scalar(values.get("accuracy"), "accuracy")}</div><small>case_count · {_escape(values.get("case_count", 0))}</small></a>'
        for name, values in summary.get("question_type_breakdown", {}).items()
    )
    bad_cases = [case for case in cases if case.get("root_cause") != "PASS"][:8]
    benchmark_rows = "".join(
        "<tr>"
        f'<td><a href="{_escape(item.get("href", "index.html"))}">{_escape(item.get("dataset_name", item.get("dataset_id", NOT_RECORDED)))}</a></td>'
        f'<td>{_scalar(item.get("case_count"), "case_count")}</td>'
        f'<td>{_scalar(item.get("hit_at_k"), "hit_at_10")}</td>'
        f'<td>{_scalar(item.get("recall_at_k"), "recall_at_10")}</td>'
        f'<td>{_scalar(item.get("mrr"), "mrr")}</td>'
        f'<td>{_scalar(item.get("answer_accuracy"), "answer_accuracy")}</td>'
        f'<td>{_scalar(item.get("grounded_end_to_end_accuracy"), "grounded_end_to_end_accuracy")}</td>'
        f'<td>{_scalar(item.get("pipeline_success_rate"), "pipeline_success_rate")}</td>'
        "</tr>"
        for item in summary.get("_benchmark_runs", [])
    )
    benchmark_table = f"""
<section class="panel"><div class="section-heading"><div><p class="eyebrow">BILINGUAL BENCHMARKS</p><h2>Benchmark 表现</h2></div></div>
<div class="table-wrap"><table class="data-table"><thead><tr><th>Benchmark</th><th>Cases</th><th>Hit@10</th><th>Recall@10</th><th>MRR</th><th>Answer Accuracy</th><th>Grounded E2E</th><th>Pipeline Success</th></tr></thead><tbody>{benchmark_rows}</tbody></table></div></section>
"""
    content = f"""
{benchmark_table}
<section class="hero-grid">
  <article class="score-card"><div class="score-ring" style="--score:{composite_value:.4f}"><span>{_escape(composite_label)}</span></div><div><p class="eyebrow">DISPLAY-ONLY AGGREGATE</p><h2>综合能力评分</h2><p>retrieval_quality × 40% + answer_accuracy × 20% + grounded_end_to_end_accuracy × 40%</p><small>仅用于当前本地 Eval 的展示，不修改原始 Trace 指标。</small></div></article>
  <article class="panel"><div class="section-heading"><h2>工程健康度</h2>{_status_badge('PASS' if summary.get('pipeline_success_rate') == 1 else 'ATTENTION')}</div><div class="metric-grid compact">{_metric_card('pipeline_success_rate', summary.get('pipeline_success_rate'))}{_metric_card('add_success_rate', retrieval.get('add_success_rate'))}{_metric_card('index_success_rate', retrieval.get('index_success_rate'))}{_metric_card('search_success_rate', retrieval.get('search_success_rate'))}{_metric_card('api_error_count', api.get('api_error_count'))}{_metric_card('timeouts', api.get('timeouts'))}</div></article>
</section>
<section class="panel"><div class="section-heading"><div><p class="eyebrow">CORE METRICS</p><h2>检索质量 · 回答质量 · 有依据端到端能力</h2></div></div><div class="metric-grid">{_metric_card('hit_at_k', summary.get('hit_at_k'), tone='blue', note=f'hit_at_{top_k}')}{_metric_card('recall_at_k', recall, tone='blue', note=f'recall_at_{top_k}')}{_metric_card('mrr', mrr, tone='blue')}{_metric_card('answer_accuracy', answer_accuracy, tone='violet')}{_metric_card('grounded_end_to_end_accuracy', grounded, tone='green')}{_metric_card('answer_failure_count', summary.get('answer_failure_count'), tone='red')}</div></section>
{_quadrant_chart(summary, cases, prefix='')}
<section class="panel"><div class="section-heading"><div><p class="eyebrow">CAPABILITY BREAKDOWN</p><h2>能力维度表现</h2></div></div><div class="capability-grid">{capabilities}</div></section>
<section class="panel"><div class="section-heading"><div><p class="eyebrow">EVIDENCE COVERAGE</p><h2>证据数量分层表现</h2></div></div>{_field_table(summary.get('evidence_count_breakdown', {}))}</section>
<section class="panel"><div class="section-heading"><div><p class="eyebrow">ROOT CAUSE</p><h2>失败归因</h2></div><a href="cases/index.html">查看全部 Case</a></div><div class="root-grid">{root_cards}</div></section>
<section class="panel"><div class="section-heading"><div><p class="eyebrow">BAD CASES</p><h2>重点 Bad Case</h2></div></div>{_case_table(bad_cases, link_prefix='', filters=False)}</section>
"""
    return _page("Memory Eval Dashboard", content, summary, depth=0, active="home", subtitle="从聚合能力到单 Case Trace 的本地静态诊断入口", page_class="dashboard-home")


def _capability_page(summary: dict[str, Any], cases: list[dict[str, Any]], question_type: str) -> str:
    values = summary.get("question_type_breakdown", {}).get(question_type, {})
    matched = [case for case in cases if case.get("question_type") == question_type]
    content = f'<section class="panel"><div class="metric-grid">' + "".join(
        _metric_card(key, value, tone="blue" if "hit" in key or "recall" in key or key == "mrr" else "neutral")
        for key, value in values.items()
    ) + f'</div></section><section class="panel"><div class="section-heading"><h2>Case 列表</h2><code>question_type={_escape(question_type)}</code></div>{_case_table(matched, link_prefix="../", filters=False)}</section>'
    return _page(CAPABILITY_LABELS.get(question_type, question_type), content, summary, active="cases", subtitle=question_type)


def _pipeline_page(summary: dict[str, Any], stage: str) -> str:
    retrieval = summary.get("retrieval_stage", {})
    if stage == "add":
        fields = ("add_success_rate", "added_sessions", "failed_add_sessions", "added_turns", "evidence_add_success_rate", "duplicate_add_count", "empty_content_add_count", "add_latency_ms")
        data = retrieval
        title = "写入阶段"
    elif stage == "index":
        fields = ("index_success_rate", "indexed_document_count", "indexed_chunk_count", "average_chunks_per_session", "index_latency_ms", "embedding", "extraction")
        data = {**retrieval, **summary.get("processing_observability", {})}
        title = "索引阶段"
    elif stage == "search":
        fields = ("search_success_rate", "search_request_count", "empty_search_result_count", "search_retry_count", "search_latency_ms", f"hit_at_{summary.get('top_k', 10)}", f"recall_at_{summary.get('top_k', 10)}", "mrr", "full_evidence_recall_rate", "partial_evidence_rate", "zero_evidence_rate")
        data = retrieval
        title = "检索阶段"
    elif stage == "answer":
        data = summary.get("answer_stage", {})
        fields = None
        title = "回答阶段"
    else:
        data = summary.get("judge_stage", {})
        fields = None
        title = "判分阶段"
    tabs = "".join(f'<a class="tab {"active" if name == stage else ""}" href="{name}.html">{label}</a>' for name, label in (("add", "写入阶段"), ("index", "索引阶段"), ("search", "检索阶段"), ("answer", "回答阶段"), ("judge", "判分阶段")))
    content = f'<div class="tabs">{tabs}</div><section class="panel">{_field_table(data, fields)}</section>'
    return _page(title, content, summary, active="pipeline", subtitle="二级、三级字段保持 Trace 原始名称")


def _failure_page(summary: dict[str, Any], cases: list[dict[str, Any]], root_cause: str) -> str:
    matched = [case for case in cases if case.get("root_cause") == root_cause]
    content = f'<section class="panel"><div class="section-heading"><div>{_status_badge(root_cause)}<h2>{len(matched)} Cases</h2></div></div>{_case_table(matched, link_prefix="../", filters=False)}</section>'
    return _page("失败归因", content, summary, active="cases", subtitle=root_cause)


def _latency_page(summary: dict[str, Any]) -> str:
    data = summary.get("latency_breakdown", {})
    maximum = max((float(value.get("p95", 0) or 0) for value in data.values() if isinstance(value, dict)), default=1.0)
    bars = "".join(
        f'<div class="latency-row"><code>{_escape(stage)}</code><div class="latency-track"><span style="width:{min(100, float(values.get("p95", 0) or 0) / maximum * 100):.1f}%"></span></div><strong>{_scalar(values.get("p95"))} ms</strong></div>'
        for stage, values in data.items()
    )
    tabs = _performance_tabs("latency")
    return _page("性能与时延", f'{tabs}<section class="panel"><h2>P95 latency</h2><div class="latency-bars">{bars}</div></section><section class="panel">{_field_table(data)}</section>', summary, active="performance", subtitle="latency_breakdown")


def _performance_tabs(active: str) -> str:
    return '<div class="tabs">' + "".join(
        f'<a class="tab {"active" if key == active else ""}" href="{path}">{label}</a>'
        for key, path, label in (
            ("latency", "latency.html", "性能与时延"),
            ("api-stability", "api-stability.html", "API 稳定性"),
            ("token-usage", "token-usage.html", "Token 与 Cost"),
        )
    ) + "</div>"


def _performance_page(summary: dict[str, Any], kind: str) -> str:
    if kind == "api-stability":
        title, data = "API 稳定性", summary.get("api_stability", {})
    else:
        title = "Token Usage 与 Cost"
        data = {"answer_stage.token_usage": summary.get("answer_stage", {}).get("token_usage"), "judge_stage.token_usage": summary.get("judge_stage", {}).get("token_usage"), "llm_cost": summary.get("llm_cost")}
    return _page(title, f'{_performance_tabs(kind)}<section class="panel">{_field_table(data)}</section>', summary, active="performance")


def _comparison_page(summary: dict[str, Any]) -> str:
    comparison = summary.get("comparison")
    if not isinstance(comparison, dict):
        body = '<div class="empty-state">当前 Trace 没有 comparison 数据。</div>'
    else:
        links = []
        for field in ("newly_fixed_cases", "newly_failed_cases"):
            case_links = "".join(f'<a class="tag" href="../cases/{_safe_name(case_id)}.html">{_escape(case_id)}</a>' for case_id in comparison.get(field, [])) or '<span class="status-muted">[]</span>'
            links.append(f'<div class="comparison-cases"><code>{field}</code><div class="tag-list">{case_links}</div></div>')
        body = _field_table(comparison, ("baseline_run", "shared_case_count", "metric_deltas", "root_cause_deltas", "comparison_notes")) + "".join(links)
    return _page("版本对比", f'<section class="panel">{body}</section>', summary, active="comparison", subtitle="comparison")


def _run_info_page(summary: dict[str, Any]) -> str:
    sections = "".join(
        f'<section class="panel"><div class="section-heading"><h2>{_escape(name)}</h2></div>{_field_table(summary.get(name, {}) if isinstance(summary.get(name), dict) else {name: summary.get(name)})}</section>'
        for name in ("run_info", "version_fixed_fields", "dataset_integrity", "conclusions")
    )
    gaps = summary.get("observability_gaps", [])
    sections += '<section class="panel"><div class="section-heading"><h2>observability_gaps</h2></div><ul class="gap-list">' + "".join(f'<li>{_escape(item)}</li>' for item in gaps) + "</ul></section>"
    return _page("运行信息", sections, summary, active="run-info")


def _case_detail(summary: dict[str, Any], detail: dict[str, Any]) -> str:
    basic = detail.get("case", {})
    add = detail.get("add", {})
    retrieval = detail.get("retrieval", {})
    answer = detail.get("answer", {})
    judge = detail.get("judge", {})
    final = detail.get("final", {})
    top_results = []
    for item in retrieval.get("top_results", []):
        evidence = bool(item.get("is_evidence"))
        top_results.append(
            f'<article class="result-card {"evidence-result" if evidence else ""}"><header><span class="rank">#{_escape(item.get("rank", NOT_RECORDED))}</span><code>{_escape(item.get("session_id", NOT_RECORDED))}</code>{_status_badge("EVIDENCE" if evidence else "DISTRACTOR")}</header>'
            f'<div class="result-meta"><span>score · {_scalar(item.get("score"))}</span><span>timestamp · {_escape(item.get("timestamp", NOT_RECORDED))}</span></div><details {"open" if evidence else ""}><summary>text</summary><pre>{_escape(item.get("text", item.get("text_excerpt", NOT_RECORDED)))}</pre></details></article>'
        )
    contexts = "".join(f'<details class="context-block"><summary>retrieved_contexts[{index}]</summary><pre>{_escape(text)}</pre></details>' for index, text in enumerate(answer.get("retrieved_contexts", []), start=1))
    raw_json = json.dumps(detail, ensure_ascii=False, indent=2)
    content = f"""
<section class="diagnosis-banner {"pass" if final.get('root_cause') == 'PASS' else 'fail'}"><div><p class="eyebrow">问题诊断</p><h2>{_escape(final.get('root_cause', NOT_RECORDED))}</h2><p>{_escape(final.get('explanation', NOT_RECORDED))}</p></div><div><span class="quadrant-detail q-{_quadrant_code(final.get('quadrant')).lower()}">{_escape(final.get('quadrant', NOT_RECORDED))}</span></div></section>
<section class="panel"><div class="section-heading"><h2>数据输入</h2></div>{_field_table(basic)}</section>
<section class="panel"><div class="section-heading"><h2>写入追踪</h2></div>{_field_table(add)}</section>
<section class="panel"><div class="section-heading"><h2>检索追踪</h2></div>{_field_table(retrieval, ("query", "top_k", "hit_at_k", "recall_at_k", "mrr", "first_evidence_rank", "first_evidence_rank_full", "gold_evidence_count", "retrieved_evidence_count", "missing_evidence_ids", "best_evidence_score", "best_non_evidence_score", "evidence_score_gap", "evidence_content_present", "search_latency_ms", "failure"))}<h3>top_results</h3><div class="result-list">{''.join(top_results)}</div></section>
<section class="panel"><div class="section-heading"><h2>回答追踪</h2></div>{_field_table(answer, ("context_count", "context_characters", "context_token_estimate", "context_order", "context_timestamps", "evidence_context_positions", "distractor_count", "evidence_in_retrieved_context", "evidence_in_prompt", "truncation_occurred", "evidence_after_truncation", "generated_answer", "gold_answer", "answer_difference", "model", "latency_ms", "usage", "failure"))}<h3>retrieved_contexts</h3>{contexts or _scalar(None)}</section>
<section class="panel"><div class="section-heading"><h2>判分追踪</h2></div>{_field_table(judge)}</section>
<section class="panel"><div class="section-heading"><h2>问题诊断</h2></div>{_field_table(final)}</section>
<section class="panel"><details><summary>完整 Trace JSON</summary><pre class="json-block">{_escape(raw_json)}</pre></details></section>
"""
    return _page(f"Case · {basic.get('case_id', NOT_RECORDED)}", content, summary, active="cases", subtitle=str(basic.get("question_type", "")), page_class="case-detail-page")


def build_html_report(
    run_dir: str | Path,
    output_dir: str | Path | None = None,
    benchmark_runs: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build the complete static dashboard and return a machine-readable manifest."""

    run_dir = Path(run_dir).resolve()
    summary_path = run_dir / "trace" / "trace_summary.json"
    if not summary_path.is_file():
        raise FileNotFoundError(f"Trace summary not found: {summary_path}")
    case_dir = run_dir / "trace" / "cases"
    case_paths = sorted(case_dir.glob("*.json"))
    if not case_paths:
        raise FileNotFoundError(
            f"Detailed case JSON not found in {case_dir}; rebuild Trace with scripts/build_trace_report.py first"
        )
    summary = _read_json(summary_path)
    details = [_read_json(path) for path in case_paths]
    summary_cases = [item for item in summary.get("cases", []) if isinstance(item, dict)]
    output = Path(output_dir).resolve() if output_dir else run_dir / "report"
    output.mkdir(parents=True, exist_ok=True)
    current_id = summary.get("dataset_id", summary.get("run_info", {}).get("dataset_id", NOT_RECORDED))
    rows = benchmark_runs or [
        {
            "dataset_id": current_id,
            "dataset_name": summary.get("dataset_name", summary.get("run_info", {}).get("dataset_name", current_id)),
            "case_count": summary.get("case_count", summary.get("total_cases")),
            "hit_at_k": summary.get("hit_at_k"),
            "recall_at_k": summary.get("recall_at_k"),
            "mrr": summary.get("mrr"),
            "answer_accuracy": summary.get("answer_accuracy"),
            "grounded_end_to_end_accuracy": summary.get("grounded_end_to_end_accuracy"),
            "pipeline_success_rate": summary.get("pipeline_success_rate"),
            "dashboard_dir": str(output),
        }
    ]
    summary["_benchmark_runs"] = [
        {
            **item,
            "href": os.path.relpath(
                Path(str(item.get("dashboard_dir", output))) / "index.html",
                output,
            ).replace("\\", "/"),
        }
        for item in rows
    ]

    generated: list[Path] = []

    def write(relative: str, content: str) -> None:
        path = output / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8", newline="")
        generated.append(path)

    for asset in ("style.css", "app.js"):
        source = ASSET_DIR / asset
        if not source.is_file():
            raise FileNotFoundError(f"HTML asset not found: {source}")
        target = output / "assets" / asset
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        generated.append(target)

    markdown_source = run_dir / "trace" / "trace_summary.md"
    if markdown_source.is_file():
        markdown_target = output / "trace_summary.md"
        shutil.copy2(markdown_source, markdown_target)
        generated.append(markdown_target)

    write("index.html", _home(summary, summary_cases))
    write("analysis/quadrant.html", _page("端到端能力四象限分析", _quadrant_chart(summary, summary_cases, prefix="../"), summary, active="quadrant", subtitle="Case / Question Type / Run 三种粒度"))
    for question_type in CAPABILITY_LABELS:
        write(f"capabilities/{_slug(question_type)}.html", _capability_page(summary, summary_cases, question_type))
    for stage in ("add", "index", "search", "answer", "judge"):
        write(f"pipeline/{stage}.html", _pipeline_page(summary, stage))
    for root_cause in ROOT_CAUSES:
        if root_cause != "PASS":
            write(f"failures/{_slug(root_cause)}.html", _failure_page(summary, summary_cases, root_cause))
    write("cases/index.html", _page("Case 追踪", f'<section class="panel">{_case_table(summary_cases, link_prefix="../")}</section>', summary, active="cases", subtitle="默认按失败优先级排序，可组合筛选"))
    for detail in details:
        case_id = detail.get("case", {}).get("case_id", NOT_RECORDED)
        write(f"cases/{_safe_name(case_id)}.html", _case_detail(summary, detail))
    write("performance/latency.html", _latency_page(summary))
    write("performance/api-stability.html", _performance_page(summary, "api-stability"))
    write("performance/token-usage.html", _performance_page(summary, "token-usage"))
    write("comparison/index.html", _comparison_page(summary))
    write("run-info/index.html", _run_info_page(summary))

    manifest = {
        "schema_version": "memory_eval_html_report_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "run_dir": str(run_dir),
        "trace_summary": str(summary_path),
        "output_dir": str(output),
        "page_count": sum(path.suffix == ".html" for path in generated),
        "case_page_count": len(details),
        "files": [str(path.relative_to(output)).replace("\\", "/") for path in generated],
        "source_sha256": hashlib.sha256(summary_path.read_bytes()).hexdigest(),
    }
    manifest_path = output / "report_manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest
