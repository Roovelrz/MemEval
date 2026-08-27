"""Render a local static dashboard from Trace artifacts without re-evaluating cases."""

from __future__ import annotations

import hashlib
import html
import json
import os
import re
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
            return f'<span class="metric-value">{value * 100:.1f}%</span>'
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


def _display_field_name(name: str, top_k: int | None = None) -> str:
    lowered = name.lower()
    if lowered == "hit_at_k":
        return f"Hit@{top_k}" if top_k is not None else "Hit@K"
    if lowered == "recall_at_k":
        return f"Recall@{top_k}" if top_k is not None else "Recall@K"
    match = re.fullmatch(r"(hit|recall)_at_(\d+)", lowered)
    if match:
        return f"{match.group(1).title()}@{match.group(2)}"
    return name


def _field_table(
    data: dict[str, Any],
    fields: Iterable[str] | None = None,
    *,
    top_k: int | None = None,
) -> str:
    names = list(fields) if fields is not None else list(data)
    rows = "".join(
        f"<tr><th><code>{_escape(_display_field_name(name, top_k))}</code></th><td>{_value(data.get(name), name)}</td></tr>"
        for name in names
    )
    return f'<div class="table-wrap"><table class="field-table"><tbody>{rows}</tbody></table></div>'


def _metric_card(
    label: str,
    value: object,
    *,
    tone: str = "neutral",
    note: str = "",
    display_label: str | None = None,
    hover_html: str = "",
) -> str:
    visible_label = display_label or _display_field_name(label)
    hover = f'<div class="metric-tooltip" role="tooltip">{hover_html}</div>' if hover_html else ""
    hover_class = " has-hover" if hover_html else ""
    tabindex = ' tabindex="0"' if hover_html else ""
    return (
        f'<article class="metric-card tone-{tone}{hover_class}"{tabindex}><div class="metric-label"><code>{_escape(visible_label)}</code></div>'
        f'<div class="metric-number">{_scalar(value, label)}</div>'
        f'{f"<div class=\"metric-note\">{_escape(note)}</div>" if note else ""}{hover}</article>'
    )


def _aggregate_retrieval_metrics(summary: dict[str, Any], details: list[dict[str, Any]]) -> dict[str, dict[str, float]]:
    """Aggregate per-case Hit/Recall values for the small K comparison tooltip."""

    samples: dict[str, dict[str, list[float]]] = {}
    for detail in details:
        retrieval = detail.get("retrieval", {})
        metrics_by_k = retrieval.get("metrics_by_k") if isinstance(retrieval, dict) else None
        if not isinstance(metrics_by_k, dict):
            continue
        for raw_k, metrics in metrics_by_k.items():
            if not isinstance(metrics, dict):
                continue
            key = str(raw_k)
            bucket = samples.setdefault(key, {"hit": [], "recall": []})
            for name in ("hit", "recall"):
                value = metrics.get(name)
                if isinstance(value, (int, float)) and not isinstance(value, bool):
                    bucket[name].append(float(value))

    result: dict[str, dict[str, float]] = {
        key: {
            name: sum(values) / len(values)
            for name, values in bucket.items()
            if values
        }
        for key, bucket in samples.items()
    }

    # Accept a future aggregate map if the Trace producer starts persisting one.
    retrieval_stage = summary.get("retrieval_stage")
    sources = (
        summary.get("metrics_by_k"),
        retrieval_stage.get("metrics_by_k") if isinstance(retrieval_stage, dict) else None,
    )
    for source in sources:
        if not isinstance(source, dict):
            continue
        for raw_k, metrics in source.items():
            if not isinstance(metrics, dict):
                continue
            key = str(raw_k)
            target = result.setdefault(key, {})
            for name in ("hit", "recall"):
                value = metrics.get(name)
                if name not in target and isinstance(value, (int, float)) and not isinstance(value, bool):
                    target[name] = float(value)

    top_k = str(summary.get("top_k", 10))
    fallback = result.setdefault(top_k, {})
    if "hit" not in fallback and isinstance(summary.get("hit_at_k"), (int, float)):
        fallback["hit"] = float(summary["hit_at_k"])
    if "recall" not in fallback and isinstance(summary.get("recall_at_k"), (int, float)):
        fallback["recall"] = float(summary["recall_at_k"])
    return result


def _primary_retrieval_metrics(summary: dict[str, Any]) -> tuple[int, object, object]:
    metrics_by_k = summary.get("_metrics_by_k", {})
    preferred = metrics_by_k.get("3") if isinstance(metrics_by_k, dict) else None
    if isinstance(preferred, dict) and any(
        isinstance(preferred.get(name), (int, float)) for name in ("hit", "recall")
    ):
        return 3, preferred.get("hit"), preferred.get("recall")
    top_k = int(summary.get("top_k", 10) or 10)
    fallback = metrics_by_k.get(str(top_k), {}) if isinstance(metrics_by_k, dict) else {}
    return top_k, fallback.get("hit", summary.get("hit_at_k")), fallback.get("recall", summary.get("recall_at_k"))


def _retrieval_metric_tooltip(metrics_by_k: dict[str, dict[str, float]]) -> str:
    rows = []
    for k in (1, 3, 5, 10):
        metrics = metrics_by_k.get(str(k), {})
        rows.append(
            f'<div class="metric-tooltip-row"><code>Hit@{k}</code>{_scalar(metrics.get("hit"), f"hit_at_{k}")}<code>Recall@{k}</code>{_scalar(metrics.get("recall"), f"recall_at_{k}")}</div>'
        )
    return '<strong>完整 K 指标</strong><div class="metric-tooltip-grid">' + "".join(rows) + '</div><small> </small>'


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
        ("pipeline", "流程观测", "pipeline/add.html"),
        ("performance", "性能与时延", "performance/latency.html"),
        ("comparison", "版本对比", "comparison/index.html"),
        ("run-info", "运行信息", "run-info/index.html"),
    )
    primary = "".join(
        f'<a class="nav-link {"active" if key == active else ""}" href="{prefix}{path}"><span>{label}</span></a>'
        for key, label, path in items[:2]
    )
    case_active = active in {"cases", "capabilities", "failures"}
    case_links = (
        f'<a class="nav-link {"active" if case_active else ""}" href="{prefix}cases/index.html"><span>Case 追踪</span></a>'
        '<div class="nav-children">'
        f'<a class="nav-sublink {"active" if active == "cases" else ""}" href="{prefix}cases/index.html">Case 列表</a>'
        f'<a class="nav-sublink {"active" if active == "capabilities" else ""}" href="{prefix}capabilities/index.html">能力维度表现</a>'
        f'<a class="nav-sublink {"active" if active == "failures" else ""}" href="{prefix}failures/index.html">失败归因</a>'
        '</div>'
    )
    secondary = "".join(
        f'<a class="nav-link {"active" if key == active else ""}" href="{prefix}{path}"><span>{label}</span></a>'
        for key, label, path in items[2:]
    )
    return f'<nav class="sidebar"><div class="brand"><span class="brand-mark">M</span><div><strong>Memory Eval</strong><small>Trace Dashboard</small></div></div>{primary}{case_links}{secondary}</nav>'


def _case_tracking_tabs(active: str) -> str:
    return '<div class="tabs case-tracking-tabs">' + "".join(
        f'<a class="tab {"active" if key == active else ""}" href="../{path}">{label}</a>'
        for key, path, label in (
            ("cases", "cases/index.html", "Case 列表"),
            ("capabilities", "capabilities/index.html", "能力维度表现"),
            ("failures", "failures/index.html", "失败归因"),
        )
    ) + "</div>"


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
    back_fallback = f"{prefix}index.html" if depth > 0 else "../trace_summary.md"
    back_button = f'<button class="button secondary" type="button" data-back-button data-back-fallback="{back_fallback}">← 返回上一级</button>'
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
      <div class="header-actions">{back_button}{benchmark_selector}<a class="button secondary" href="{prefix}trace_summary.md">查看 Markdown Trace</a></div>
    </header>
    {content}
    <footer>由现有 Trace 产物静态生成 · 不参与评测、判分或根因计算</footer>
  </main>
  <script src="{prefix}assets/app.js"></script>
</body>
</html>
"""


def _case_table(
    cases: list[dict[str, Any]],
    *,
    link_prefix: str = "",
    filters: bool = True,
    top_k: int = 10,
) -> str:
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
            f'<td>{_scalar(case.get("hit_at_k"), f"hit_at_{top_k}")}</td><td>{_scalar(case.get("recall_at_k"), f"recall_at_{top_k}")}</td>'
            f'<td>{_scalar(case.get("mrr"), "mrr")}</td><td>{_scalar(case.get("first_evidence_rank"), "first_evidence_rank")}</td>'
            f'<td>{_status_badge(case.get("answer_correct"))}</td><td>{_status_badge(case.get("judge_label"))}</td>'
            f'<td><span class="quadrant q-{_quadrant_code(case.get("quadrant")).lower()}">{_escape(_quadrant_code(case.get("quadrant")))}</span></td>'
            f'<td>{_status_badge(case.get("root_cause"))}</td><td class="explanation-cell">{_escape(case.get("explanation", NOT_RECORDED))}</td></tr>'
        )
    return f"""{filter_html}<div class="table-wrap"><table class="data-table" data-filter-table>
<thead><tr><th>case_id</th><th>question_type</th><th>Hit@{top_k}</th><th>Recall@{top_k}</th><th>mrr</th><th>first_evidence_rank</th><th>answer_correct</th><th>judge_label</th><th>quadrant</th><th>root_cause</th><th>explanation</th></tr></thead>
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
    return {
        "top_k": int(summary.get("top_k", 10)),
        "case": case_points,
        "type": type_points,
        "run": run_points,
    }


def _quadrant_chart(summary: dict[str, Any], cases: list[dict[str, Any]], *, prefix: str) -> str:
    payload = json.dumps(_quadrant_payload(summary, cases, prefix), ensure_ascii=False).replace("</", "<\\/")
    quadrant_counts = {
        code: sum(_quadrant_code(case.get("quadrant")) == code for case in cases)
        for code in "ABCD"
    }
    options = lambda key: "".join(
        f'<option value="{_escape(value)}">{_escape(value)}</option>'
        for value in sorted({str(case.get(key, NOT_RECORDED)) for case in cases})
    )
    return f"""<section class="panel quadrant-panel">
<div class="section-heading"><div><p class="eyebrow">INTERACTIVE ANALYSIS</p><h2>端到端能力四象限分析</h2></div>
<div class="segmented"><button class="active" data-chart-level="case">Case</button><button data-chart-level="type">Question Type</button><button data-chart-level="run">Run</button></div></div>
<div class="chart-filters"><label>question_type<select data-chart-filter="question_type"><option value="">全部</option>{options('question_type')}</select></label><label>root_cause<select data-chart-filter="root_cause"><option value="">全部</option>{options('root_cause')}</select></label><label>quadrant<select data-chart-filter="quadrant"><option value="">全部</option>{options('quadrant')}</select></label></div>
<div class="quadrant-layout"><div class="y-label">Answer PASS ↑</div><div class="quadrant-chart" data-quadrant-chart data-score-axis-x="best_evidence_score" data-score-axis-y="best_non_evidence_score" aria-label="象限内点位按 best_evidence_score 和 best_non_evidence_score 排列">
<div class="quadrant-zone zone-c"><strong>C <em data-quadrant-count="C">{quadrant_counts['C']}</em></strong><span>检索失败 · 回答成功</span></div><div class="quadrant-zone zone-a"><strong>A <em data-quadrant-count="A">{quadrant_counts['A']}</em></strong><span>检索成功 · 回答成功</span></div>
<div class="quadrant-zone zone-d"><strong>D <em data-quadrant-count="D">{quadrant_counts['D']}</em></strong><span>检索失败 · 回答失败</span></div><div class="quadrant-zone zone-b"><strong>B <em data-quadrant-count="B">{quadrant_counts['B']}</em></strong><span>检索成功 · 回答失败</span></div><div class="axis-x">Retrieval PASS →</div><div class="chart-points" data-chart-points></div></div></div>
<script type="application/json" data-chart-data>{payload}</script></section>"""


def _home(summary: dict[str, Any], cases: list[dict[str, Any]]) -> str:
    aggregate_recall = summary.get("recall_at_k")
    mrr = summary.get("mrr")
    answer_accuracy = summary.get("answer_accuracy")
    grounded = summary.get("grounded_end_to_end_accuracy")
    retrieval_quality = aggregate_recall * 0.6 + mrr * 0.4 if isinstance(aggregate_recall, (int, float)) and isinstance(mrr, (int, float)) else None
    composite = retrieval_quality * 0.4 + answer_accuracy * 0.2 + grounded * 0.4 if all(isinstance(value, (int, float)) for value in (retrieval_quality, answer_accuracy, grounded)) else None
    composite_value = float(composite or 0)
    composite_label = f"{composite_value * 100:.1f}%" if composite is not None else NOT_RECORDED
    retrieval = summary.get("retrieval_stage", {})
    api = summary.get("api_stability", {})
    top_k = summary.get("top_k", 10)
    primary_k, primary_hit, primary_recall = _primary_retrieval_metrics(summary)
    retrieval_tooltip = _retrieval_metric_tooltip(summary.get("_metrics_by_k", {}))
    root_counts = summary.get("root_cause_distribution", {})
    nonzero_roots = [(name, int(root_counts.get(name, 0))) for name in ROOT_CAUSES if name != "PASS" and root_counts.get(name, 0)]
    root_cards = "".join(
        f'<a class="root-card" href="failures/{_slug(name)}.html"><span>{_status_badge(name)}</span><strong>{count}</strong></a>'
        for name, count in nonzero_roots
    ) or '<div class="empty-state">当前 Run 没有非 PASS 根因。</div>'
    capabilities = "".join(
        f'<a class="capability-card" href="capabilities/{_slug(name)}.html"><span>{_escape(CAPABILITY_LABELS.get(name, name))}</span><code>{_escape(name)}</code><div class="capability-score"><span>accuracy</span><strong>{_scalar(values.get("accuracy"), "accuracy")}</strong></div><small>case_count · {_escape(values.get("case_count", 0))}</small></a>'
        for name, values in summary.get("question_type_breakdown", {}).items()
    )
    bad_cases = [case for case in cases if case.get("root_cause") != "PASS"][:8]
    benchmark_rows = "".join(
        "<tr>"
        f'<td><a href="{_escape(item.get("href", "index.html"))}">{_escape(item.get("dataset_name", item.get("dataset_id", NOT_RECORDED)))}</a></td>'
        f'<td>{_scalar(item.get("case_count"), "case_count")}</td>'
        f'<td>{_scalar(item.get("hit_at_k"), f"hit_at_{top_k}")}</td>'
        f'<td>{_scalar(item.get("recall_at_k"), f"recall_at_{top_k}")}</td>'
        f'<td>{_scalar(item.get("mrr"), "mrr")}</td>'
        f'<td>{_scalar(item.get("answer_accuracy"), "answer_accuracy")}</td>'
        f'<td>{_scalar(item.get("grounded_end_to_end_accuracy"), "grounded_end_to_end_accuracy")}</td>'
        f'<td>{_scalar(item.get("pipeline_success_rate"), "pipeline_success_rate")}</td>'
        "</tr>"
        for item in summary.get("_benchmark_runs", [])
    )
    benchmark_table = f"""
<section class="panel"><div class="section-heading"><div><p class="eyebrow">BILINGUAL BENCHMARKS</p><h2>Benchmark 表现</h2></div></div>
<div class="table-wrap"><table class="data-table"><thead><tr><th>Benchmark</th><th>Cases</th><th>Hit@{top_k}</th><th>Recall@{top_k}</th><th>MRR</th><th>Answer Accuracy</th><th>Grounded E2E</th><th>Pipeline Success</th></tr></thead><tbody>{benchmark_rows}</tbody></table></div></section>
"""
    content = f"""
{benchmark_table}
<section class="hero-grid">
  <article class="score-card"><div class="score-ring" style="--score:{composite_value:.4f}"><span>{_escape(composite_label)}</span></div><div><p class="eyebrow">DISPLAY-ONLY AGGREGATE</p><h2>综合能力评分</h2><p>retrieval_quality × 40% + answer_accuracy × 20% + grounded_end_to_end_accuracy × 40%</p><small>仅用于当前本地 Eval 的展示，不修改原始 Trace 指标。</small></div></article>
  <article class="panel"><div class="section-heading"><h2>工程健康度</h2>{_status_badge('PASS' if summary.get('pipeline_success_rate') == 1 else 'ATTENTION')}</div><div class="metric-grid compact">{_metric_card('pipeline_success_rate', summary.get('pipeline_success_rate'))}{_metric_card('add_success_rate', retrieval.get('add_success_rate'))}{_metric_card('index_success_rate', retrieval.get('index_success_rate'))}{_metric_card('search_success_rate', retrieval.get('search_success_rate'))}{_metric_card('api_error_count', api.get('api_error_count'))}{_metric_card('timeouts', api.get('timeouts'))}</div></article>
</section>
<section class="panel"><div class="section-heading"><div><p class="eyebrow">CORE METRICS</p><h2>检索质量 · 回答质量 · 有依据端到端能力</h2></div><span class="metric-primary-hint">主指标：@{primary_k}</span></div><div class="metric-grid">{_metric_card('hit_at_k', primary_hit, tone='blue', note=f'前 {primary_k} 条是否命中至少一个 Evidence', display_label=f'Hit@{primary_k}', hover_html=retrieval_tooltip)}{_metric_card('recall_at_k', primary_recall, tone='blue', note=f'前 {primary_k} 条覆盖了多少 Evidence', display_label=f'Recall@{primary_k}', hover_html=retrieval_tooltip)}{_metric_card('mrr', mrr, tone='blue', display_label='MRR', note='第一个相关 Evidence 排名越靠前，MRR 越高。')}{_metric_card('answer_accuracy', answer_accuracy, tone='violet', note='Judge 判定回答正确的 Case 占比。')}{_metric_card('grounded_end_to_end_accuracy', grounded, tone='green', note='检索找到正确 Evidence 且最终回答正确的 Case 占比。')}{_metric_card('answer_failure_count', summary.get('answer_failure_count'), tone='red', note='被归因到 Answer 失败的 Case 数。')}</div></section>
{_quadrant_chart(summary, cases, prefix='')}
<section class="panel"><div class="section-heading"><div><p class="eyebrow">CAPABILITY BREAKDOWN</p><h2>能力维度表现</h2></div><a href="capabilities/index.html">独立查看</a></div><div class="capability-grid">{capabilities}</div></section>
<section class="panel"><div class="section-heading"><div><p class="eyebrow">EVIDENCE COVERAGE</p><h2>证据数量分层表现</h2></div></div>{_field_table(summary.get('evidence_count_breakdown', {}))}</section>
<section class="panel"><div class="section-heading"><div><p class="eyebrow">ROOT CAUSE</p><h2>失败归因</h2></div><a href="failures/index.html">独立查看</a></div><div class="root-grid">{root_cards}</div></section>
<section class="panel"><div class="section-heading"><div><p class="eyebrow">BAD CASES</p><h2>重点 Bad Case</h2></div></div>{_case_table(bad_cases, link_prefix='', filters=False, top_k=top_k)}</section>
"""
    return _page("Memory Eval Dashboard", content, summary, depth=0, active="home", subtitle="从聚合能力到单 Case Trace 的本地静态诊断入口", page_class="dashboard-home")


def _capability_page(summary: dict[str, Any], cases: list[dict[str, Any]], question_type: str) -> str:
    values = summary.get("question_type_breakdown", {}).get(question_type, {})
    matched = [case for case in cases if case.get("question_type") == question_type]
    top_k = int(summary.get("top_k", 10))
    content = _case_tracking_tabs("capabilities") + f'<section class="panel"><div class="metric-grid">' + "".join(
        _metric_card(
            key,
            value,
            tone="blue" if "hit" in key or "recall" in key or key == "mrr" else "neutral",
        )
        for key, value in values.items()
    ) + f'</div></section><section class="panel"><div class="section-heading"><h2>Case 列表</h2><code>question_type={_escape(question_type)}</code></div>{_case_table(matched, link_prefix="../", filters=False, top_k=top_k)}</section>'
    return _page(CAPABILITY_LABELS.get(question_type, question_type), content, summary, active="capabilities", subtitle=question_type)


def _capabilities_index(summary: dict[str, Any], cases: list[dict[str, Any]]) -> str:
    cards = "".join(
        f'<a class="capability-card" href="{_slug(name)}.html"><span>{_escape(CAPABILITY_LABELS.get(name, name))}</span><code>{_escape(name)}</code><div class="capability-score"><span>accuracy</span><strong>{_scalar(values.get("accuracy"), "accuracy")}</strong></div><small>case_count · {_escape(values.get("case_count", 0))}</small></a>'
        for name, values in summary.get("question_type_breakdown", {}).items()
    ) or '<div class="empty-state">当前 Run 没有能力维度数据。</div>'
    content = _case_tracking_tabs("capabilities") + f'<section class="panel"><div class="section-heading"><div><p class="eyebrow">CASE TRACKING</p><h2>能力维度表现</h2></div><span>{len(cases)} Cases</span></div><div class="capability-grid">{cards}</div></section>'
    return _page("能力维度表现", content, summary, active="capabilities", subtitle="按 question_type 独立查看指标与对应 Case")


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
    content = f'<div class="tabs">{tabs}</div><section class="panel">{_field_table(data, fields, top_k=int(summary.get("top_k", 10)))}</section>'
    return _page(title, content, summary, active="pipeline", subtitle="二级、三级字段保持 Trace 原始名称")


def _failure_page(summary: dict[str, Any], cases: list[dict[str, Any]], root_cause: str) -> str:
    matched = [case for case in cases if case.get("root_cause") == root_cause]
    top_k = int(summary.get("top_k", 10))
    content = _case_tracking_tabs("failures") + f'<section class="panel"><div class="section-heading"><div>{_status_badge(root_cause)}<h2>{len(matched)} Cases</h2></div></div>{_case_table(matched, link_prefix="../", filters=False, top_k=top_k)}</section>'
    return _page("失败归因", content, summary, active="failures", subtitle=root_cause)


def _failures_index(summary: dict[str, Any], cases: list[dict[str, Any]]) -> str:
    counts = summary.get("root_cause_distribution", {})
    cards = "".join(
        f'<a class="root-card" href="{_slug(name)}.html"><span>{_status_badge(name)}</span><strong>{int(counts.get(name, 0))}</strong></a>'
        for name in ROOT_CAUSES
        if name != "PASS" and counts.get(name, 0)
    ) or '<div class="empty-state">当前 Run 没有非 PASS 根因。</div>'
    content = _case_tracking_tabs("failures") + f'<section class="panel"><div class="section-heading"><div><p class="eyebrow">CASE TRACKING</p><h2>失败归因</h2></div><span>{sum(int(counts.get(name, 0)) for name in ROOT_CAUSES if name != "PASS")} Failed Cases</span></div><div class="root-grid">{cards}</div></section>'
    return _page("失败归因", content, summary, active="failures", subtitle="按 root_cause 独立查看对应 Case")


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


def _timeline_text(value: object, limit: int = 96) -> str:
    text = " ".join(str(value or "").split())
    if not text:
        return ""
    return text if len(text) <= limit else text[: limit - 1] + "…"


def _timeline_failure_text(value: object) -> str:
    if isinstance(value, dict):
        for key in ("error", "message", "type", "reason"):
            if value.get(key):
                return _timeline_text(value[key])
        return _timeline_text(json.dumps(value, ensure_ascii=False))
    return _timeline_text(value)


def _case_stage_timeline(detail: dict[str, Any]) -> str:
    """Render a compact, hoverable progress line for one Case Trace."""

    add = detail.get("add", {}) if isinstance(detail.get("add", {}), dict) else {}
    retrieval = detail.get("retrieval", {}) if isinstance(detail.get("retrieval", {}), dict) else {}
    answer = detail.get("answer", {}) if isinstance(detail.get("answer", {}), dict) else {}
    judge = detail.get("judge", {}) if isinstance(detail.get("judge", {}), dict) else {}
    final = detail.get("final", {}) if isinstance(detail.get("final", {}), dict) else {}

    def stage(key: str, label: str, status: str, reason: str) -> dict[str, str]:
        normalized = status if status in {"pass", "fail", "unknown"} else "unknown"
        return {"key": key, "label": label, "status": normalized, "reason": reason or "未记录"}

    add_status = str(add.get("add_status", "")).upper()
    if add.get("evidence_dataset_status") == "FAIL":
        add_stage = stage("add", "Add · 写入", "fail", "数据集中的 Evidence Session 不完整")
    elif add_status == "PASS":
        added = add.get("successfully_added_session_count", NOT_RECORDED)
        expected = add.get("expected_session_count", NOT_RECORDED)
        add_stage = stage("add", "Add · 写入", "pass", f"写入完成：{added}/{expected} 个 Session")
    elif add_status in {"FAIL", "ERROR"}:
        reason = _timeline_failure_text(add.get("errors")) or "写入阶段报告失败"
        add_stage = stage("add", "Add · 写入", "fail", f"写入失败：{reason}")
    elif add:
        add_stage = stage("add", "Add · 写入", "unknown", "写入结果未明确记录")
    else:
        add_stage = stage("add", "Add · 写入", "unknown", "未记录写入结果")

    index_status = str(add.get("index_status", "")).upper()
    if index_status == "PASS":
        chunks = add.get("indexed_chunk_count", NOT_RECORDED)
        index_stage = stage("index", "Index · 索引", "pass", f"索引完成：{chunks} 个 Chunk")
    elif index_status in {"FAIL", "ERROR"}:
        reason = _timeline_failure_text(add.get("errors")) or "索引阶段报告失败"
        index_stage = stage("index", "Index · 索引", "fail", f"索引失败：{reason}")
    elif add:
        index_stage = stage("index", "Index · 索引", "unknown", "索引结果未明确记录")
    else:
        index_stage = stage("index", "Index · 索引", "unknown", "未记录索引结果")

    retrieval_root = str(final.get("root_cause", ""))
    if isinstance(final.get("retrieval_pass"), bool):
        if final.get("retrieval_pass") is True:
            retrieved = retrieval.get("retrieved_evidence_count", NOT_RECORDED)
            gold = retrieval.get("gold_evidence_count", NOT_RECORDED)
            retrieval_stage = stage("retrieval", "Retrieval · 检索", "pass", f"检索通过：召回 {retrieved}/{gold} 个 Evidence")
        else:
            retrieval_reasons = {
                "RETRIEVAL_MISS": "未召回 Gold Evidence",
                "RETRIEVAL_PARTIAL": "只召回部分 Gold Evidence",
                "RETRIEVAL_LOW_RANK": "Evidence 未进入 TopK",
                "RETRIEVAL_WRONG_CHUNK": "命中 Session，但 Evidence 内容不完整",
                "PIPELINE_FAILURE": "Evidence 内容无法验证",
            }
            reason = retrieval_reasons.get(retrieval_root) or _timeline_text(final.get("explanation")) or "检索质量未通过"
            retrieval_stage = stage("retrieval", "Retrieval · 检索", "fail", reason)
    elif retrieval.get("recorded") is True:
        retrieval_stage = stage("retrieval", "Retrieval · 检索", "unknown", "检索请求已完成，但质量结论未记录")
    else:
        retrieval_stage = stage("retrieval", "Retrieval · 检索", "unknown", "未记录检索结果")

    context_status = str(answer.get("evidence_in_retrieved_context", ""))
    prompt_status = str(answer.get("evidence_in_prompt", ""))
    if context_status == "YES":
        context_reason = "Evidence 已进入 Answer context"
        if prompt_status == "YES":
            context_reason = "Evidence 已进入最终 Answer Prompt"
        elif prompt_status == NOT_RECORDED:
            context_reason += "；最终 Prompt 到达状态未记录"
        context_stage = stage("context", "Context · 上下文", "pass", context_reason)
    elif context_status in {"NO", "PARTIAL"}:
        context_stage = stage("context", "Context · 上下文", "fail", f"Evidence 上下文状态：{context_status}")
    elif answer.get("recorded") is True:
        context_stage = stage("context", "Context · 上下文", "unknown", "Answer 已执行，但 Evidence 上下文未记录")
    else:
        context_stage = stage("context", "Context · 上下文", "unknown", "未到达 Answer 上下文阶段")

    generated = answer.get("generated_answer")
    if answer.get("recorded") is not True:
        answer_stage = stage("answer", "Answer · 回答", "fail" if answer.get("failure") else "unknown", "回答调用失败" if answer.get("failure") else "未到达回答阶段")
    elif answer.get("failure"):
        answer_stage = stage("answer", "Answer · 回答", "fail", f"回答生成失败：{_timeline_failure_text(answer.get('failure'))}")
    elif not isinstance(generated, str) or not generated.strip():
        answer_stage = stage("answer", "Answer · 回答", "fail", "未生成可用回答")
    elif isinstance(final.get("answer_pass"), bool) and final.get("answer_pass") is False:
        answer_stage = stage("answer", "Answer · 回答", "fail", "回答已生成，但 Judge 判定错误")
    elif isinstance(final.get("answer_pass"), bool) and final.get("answer_pass") is True:
        answer_stage = stage("answer", "Answer · 回答", "pass", "回答已生成，Judge 判定正确")
    else:
        answer_stage = stage("answer", "Answer · 回答", "pass", "回答已生成")

    if judge.get("recorded") is not True:
        judge_stage = stage("judge", "Judge · 判分", "fail" if judge.get("failure") else "unknown", "判分调用失败" if judge.get("failure") else "未到达判分阶段")
    elif judge.get("failure"):
        judge_stage = stage("judge", "Judge · 判分", "fail", f"判分失败：{_timeline_failure_text(judge.get('failure'))}")
    elif judge.get("suspect_reasons"):
        judge_stage = stage("judge", "Judge · 判分", "fail", f"判分完成，但需人工复核：{_timeline_text(judge.get('suspect_reasons')[0])}")
    else:
        label = judge.get("parsed_label") or "已记录"
        judge_stage = stage("judge", "Judge · 判分", "pass", f"判分完成：{label}")

    root_cause = str(final.get("root_cause", ""))
    if root_cause == "PASS":
        final_stage = stage("final", "Final · 结论", "pass", "Case 完成且通过")
    elif final.get("pipeline_complete") is True:
        final_stage = stage("final", "Final · 结论", "fail", f"流程完成，但最终失败：{_timeline_text(final.get('explanation')) or root_cause}")
    else:
        final_stage = stage("final", "Final · 结论", "unknown", "最终结论未完整记录")

    stages = [add_stage, index_stage, retrieval_stage, context_stage, answer_stage, judge_stage, final_stage]
    status_labels = {"pass": "成功", "fail": "失败", "unknown": "未记录"}
    items = []
    for index, current in enumerate(stages):
        status = current["status"]
        reason = _timeline_text(current["reason"])
        aria = _escape(f"{current['label']}：{status_labels[status]}。{reason}")
        items.append(
            f'<div class="timeline-stage timeline-{status}" tabindex="0" role="img" aria-label="{aria}" title="{aria}">'
            f'<span class="timeline-node">{"✓" if status == "pass" else ("×" if status == "fail" else "—")}</span>'
            f'<strong>{_escape(current["label"])}</strong><small>{status_labels[status]}</small>'
            f'<span class="timeline-reason" role="tooltip">{_escape(reason)}</span></div>'
        )
        if index < len(stages) - 1:
            items.append(f'<span class="timeline-link timeline-{status}" aria-hidden="true"></span>')

    return (
        '<section class="panel case-timeline-panel"><div class="section-heading"><div><p class="eyebrow">CASE PROGRESS</p>'
        '<h2>阶段进度</h2></div><div class="timeline-legend"><span><i class="timeline-legend-pass"></i>阶段通过</span>'
        '<span><i class="timeline-legend-muted"></i>阶段失败或未到达</span></div></div>'
        '<p class="timeline-caption">绿色节点表示该阶段已满足当前评测条件；灰色节点表示阶段失败、未到达或缺少记录。悬停节点可查看原因。</p>'
        f'<div class="case-timeline" aria-label="Case 阶段进度">{"".join(items)}</div></section>'
    )


def _case_detail(summary: dict[str, Any], detail: dict[str, Any]) -> str:
    basic = detail.get("case", {})
    add = detail.get("add", {})
    retrieval = detail.get("retrieval", {})
    answer = detail.get("answer", {})
    judge = detail.get("judge", {})
    final = detail.get("final", {})
    top_k = int(summary.get("top_k", retrieval.get("top_k", 10) or 10))
    top_results = []
    for item in retrieval.get("top_results", []):
        evidence = bool(item.get("is_evidence"))
        top_results.append(
            f'<article class="result-card {"evidence-result" if evidence else ""}"><header><span class="rank">#{_escape(item.get("rank", NOT_RECORDED))}</span><code>{_escape(item.get("session_id", NOT_RECORDED))}</code>{_status_badge("EVIDENCE" if evidence else "DISTRACTOR")}</header>'
            f'<div class="result-meta"><span>score · {_scalar(item.get("score"))}</span><span>timestamp · {_escape(item.get("timestamp", NOT_RECORDED))}</span></div><details {"open" if evidence else ""}><summary>text</summary><pre>{_escape(item.get("text", item.get("text_excerpt", NOT_RECORDED)))}</pre></details></article>'
        )
    contexts = "".join(f'<details class="context-block"><summary>retrieved_contexts[{index}]</summary><pre>{_escape(text)}</pre></details>' for index, text in enumerate(answer.get("retrieved_contexts", []), start=1))
    raw_json = json.dumps(detail, ensure_ascii=False, indent=2)
    content = _case_tracking_tabs("cases") + _case_stage_timeline(detail) + f"""
<section class="diagnosis-banner {"pass" if final.get('root_cause') == 'PASS' else 'fail'}"><div><p class="eyebrow">问题诊断</p><h2>{_escape(final.get('root_cause', NOT_RECORDED))}</h2><p>{_escape(final.get('explanation', NOT_RECORDED))}</p></div><div><span class="quadrant-detail q-{_quadrant_code(final.get('quadrant')).lower()}">{_escape(final.get('quadrant', NOT_RECORDED))}</span></div></section>
<section class="panel"><div class="section-heading"><h2>数据输入</h2></div>{_field_table(basic)}</section>
<section class="panel"><div class="section-heading"><h2>写入追踪</h2></div>{_field_table(add)}</section>
<section class="panel"><div class="section-heading"><h2>检索追踪</h2></div>{_field_table(retrieval, ("query", "top_k", "hit_at_k", "recall_at_k", "mrr", "first_evidence_rank", "first_evidence_rank_full", "gold_evidence_count", "retrieved_evidence_count", "missing_evidence_ids", "best_evidence_score", "best_non_evidence_score", "evidence_score_gap", "evidence_content_present", "search_latency_ms", "failure"), top_k=top_k)}<h3>top_results</h3><div class="result-list">{''.join(top_results)}</div></section>
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
    summary["_metrics_by_k"] = _aggregate_retrieval_metrics(summary, details)
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
    write("capabilities/index.html", _capabilities_index(summary, summary_cases))
    for question_type in CAPABILITY_LABELS:
        write(f"capabilities/{_slug(question_type)}.html", _capability_page(summary, summary_cases, question_type))
    for stage in ("add", "index", "search", "answer", "judge"):
        write(f"pipeline/{stage}.html", _pipeline_page(summary, stage))
    write("failures/index.html", _failures_index(summary, summary_cases))
    for root_cause in ROOT_CAUSES:
        if root_cause != "PASS":
            write(f"failures/{_slug(root_cause)}.html", _failure_page(summary, summary_cases, root_cause))
    top_k = int(summary.get("top_k", 10))
    case_content = _case_tracking_tabs("cases") + f'<section class="panel">{_case_table(summary_cases, link_prefix="../", top_k=top_k)}</section>'
    write("cases/index.html", _page("Case 追踪", case_content, summary, active="cases", subtitle="默认按失败优先级排序，可组合筛选"))
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
