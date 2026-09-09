import json
from types import SimpleNamespace

import pytest

from memory_eval.adapters.Trace.memeval import MemEvalTraceAdapter
from memory_eval.html_report import (
    ROOT_CAUSES as HTML_ROOT_CAUSES,
    _case_stage_timeline,
    _quadrant_payload,
    _special_dimension_page,
    _special_dimensions_index,
)
from memory_eval.trace_report import ROOT_CAUSES as TRACE_ROOT_CAUSES
from tests.helpers import workspace_directory


def _result(case_id, dimension_id, metrics, unsupported=()):
    return {
        "case_id": case_id,
        "dimension_id": dimension_id,
        "metrics": metrics,
        "unsupported_metrics": list(unsupported),
    }


def test_memeval_trace_reuses_independent_dimension_metrics():
    adapter = MemEvalTraceAdapter.__new__(MemEvalTraceAdapter)
    adapter.artifacts = {
        "d01": SimpleNamespace(case={"gold": {"payload": {"scored_event_ids": ["e1"]}}}),
        "d04": SimpleNamespace(case={"gold": {"payload": {"should_activate": True}}}),
        "d08": SimpleNamespace(
            case={
                "gold": {
                    "payload": {
                        "canary_tokens": ["secret"],
                        "forbidden_memory_ids": ["other-user"],
                        "deleted_memory_ids": ["deleted"],
                    }
                }
            }
        ),
    }
    metrics = adapter._dimension_dashboard_metrics(
        [
            _result(
                "d01", "D01",
                {"memory_precision": 0.5, "memory_recall": 1.0,
                 "written_memory_units": 2, "noise_event_count": 1,
                 "unexpected_written_event_count": 0},
            ),
            _result("d04", "D04", {}, ["activation_decision"]),
            _result(
                "d08", "D08",
                {"canary_exposure_count": 0, "forbidden_exposure_count": 0,
                 "deleted_exposure_count": 0, "privacy_pass": 1.0,
                 "effective_privacy_pass": 1.0, "allowed_recall": 1.0},
            ),
        ]
    )

    assert metrics["D01"]["metrics"]["memory_precision"] == 0.5
    assert metrics["D01"]["metrics"]["memory_recall"] == 1.0
    assert metrics["D04"]["availability"] == "UNSUPPORTED"
    assert metrics["D04"]["metrics"]["utilization_rate"] == "NOT_APPLICABLE"
    assert metrics["D08"]["metrics"]["sensitive_exposure_rate"] == 0.0
    assert metrics["D08"]["metrics"]["cross_user_leakage_rate"] == 0.0
    assert metrics["D08"]["metrics"]["deleted_memory_hit_rate"] == 0.0
    # 主指标为有效隐私通过率（无泄露 × 允许召回），无泄露率保留为参照。
    assert metrics["D08"]["metrics"]["privacy_pass_rate"] == 1.0
    assert metrics["D08"]["metrics"]["leakage_free_rate"] == 1.0


def test_dimension_dashboard_d02_uses_k3_primary_with_full_k_breakdown():
    adapter = MemEvalTraceAdapter.__new__(MemEvalTraceAdapter)
    metrics = adapter._dimension_dashboard_metrics([
        _result("r1", "D02", {
            "hit_at_k": 1.0, "recall_at_k": 1.0, "mrr": 1.0,
            "metrics_by_k": {
                "1": {"hit": 1.0, "recall": 0.5, "mrr": 1.0},
                "3": {"hit": 1.0, "recall": 1.0, "mrr": 0.5},
                "10": {"hit": 1.0, "recall": 1.0, "mrr": 1.0},
            },
        }),
        _result("r2", "D02", {
            "hit_at_k": 1.0, "recall_at_k": 1.0, "mrr": 1.0,
            "metrics_by_k": {
                "1": {"hit": 0.0, "recall": 0.0, "mrr": 0.0},
                "3": {"hit": 1.0, "recall": 0.5, "mrr": 0.5},
                "10": {"hit": 1.0, "recall": 1.0, "mrr": 1.0},
            },
        }),
    ])

    d02 = metrics["D02"]["metrics"]
    # 主指标取 K=3，而不是 top_k=10 的旧口径。
    assert d02["primary_k"] == 3
    assert d02["hit_at_k"] == 1.0
    assert d02["recall_at_k"] == 0.75
    assert d02["mrr"] == 0.5
    assert d02["retrieval_metrics_by_k"]["1"]["recall"] == 0.25
    assert d02["retrieval_metrics_by_k"]["10"]["recall"] == 1.0

    # Dashboard 页面：主指标卡带完整 K 的悬停 tooltip。
    summary = {
        "run_info": {"run_id": "fixture"},
        "dimension_metrics": {"D02": {"availability": "MEASURED", "answer_judge": "MEASURED", "metrics": d02}},
    }
    page = _special_dimension_page(summary, [], "D02")
    assert "Recall@3" in page
    assert "Hit@3" in page
    assert "metric-tooltip" in page
    assert "Hit@10" in page  # tooltip 内含其余 K 档位
    assert "Hit@5" in page


def test_dimension_dashboard_aggregates_d03_d06_new_metrics():
    adapter = MemEvalTraceAdapter.__new__(MemEvalTraceAdapter)
    adapter.artifacts = {
        "c1": SimpleNamespace(case={"gold": {"payload": {"lifecycle": {"expected_active": False}}}}),
        "c2": SimpleNamespace(case={"gold": {"payload": {"lifecycle": {"expected_active": False}}}}),
        "c3": SimpleNamespace(case={"gold": {"payload": {"lifecycle": {"expected_active": True}}}}),
        "m1": SimpleNamespace(case={"gold": {"payload": {"fact_versions": []}}}),
        "m2": SimpleNamespace(case={"gold": {"payload": {"fact_versions": []}}}),
    }
    metrics = adapter._dimension_dashboard_metrics(
        [
            _result("c1", "D03", {"deleted_hit": True}),
            _result("c2", "D03", {"deleted_hit": False}),
            _result("c3", "D03", {}),
            _result("m1", "D06", {"stale_retrieval_rate": 1.0, "winning_fact_recall": 0.5}),
            _result("m2", "D06", {"stale_retrieval_rate": 0.0, "winning_fact_recall": 1.0}),
        ]
    )

    assert metrics["D03"]["metrics"]["deleted_hit_rate"] == 0.5
    assert metrics["D03"]["lifecycle_case_count"] == 2
    assert metrics["D06"]["metrics"]["stale_retrieval_rate"] == 0.5
    assert metrics["D06"]["metrics"]["winning_fact_recall"] == 0.75


def test_dimension_dashboard_aggregates_d07_recall_degradation():
    adapter = MemEvalTraceAdapter.__new__(MemEvalTraceAdapter)
    adapter.artifacts = {
        "g1-small": SimpleNamespace(
            case={"gold": {"payload": {"scale_group_id": "g1", "scale_level": "100K"}}}
        ),
        "g1-large": SimpleNamespace(
            case={"gold": {"payload": {"scale_group_id": "g1", "scale_level": "10M"}}}
        ),
        "stress": SimpleNamespace(case={"gold": {"payload": {}}}),
    }
    metrics = adapter._dimension_dashboard_metrics(
        [
            _result("g1-small", "D07", {"recall_at_k": 1.0}),
            _result("g1-large", "D07", {"recall_at_k": 0.6}),
            _result("stress", "D07", {"recall_at_k": 0.0}),
        ]
    )

    assert metrics["D07"]["metrics"]["recall_degradation"] == 0.4
    assert metrics["D07"]["metrics"]["recall_at_k"] == pytest.approx((1.0 + 0.6 + 0.0) / 3)
    assert metrics["D07"]["scale_group_count"] == 1
    assert metrics["D07"]["recall_by_scale"] == {"100K": 1.0, "10M": 0.6}
    assert metrics["D07"]["metrics"]["p95_search_latency_ms"] is None


def test_special_dimension_dashboard_marks_answer_and_judge_not_applicable():
    summary = {
        "run_info": {"run_id": "fixture"},
        "dimension_metrics": {
            "D04": {
                "availability": "UNSUPPORTED",
                "answer_judge": "NOT_APPLICABLE",
                "metrics": {
                    "activation_recall": None,
                    "required_activation_cases": 1,
                    "unsupported_activation_cases": 1,
                    "utilization_rate": "NOT_APPLICABLE",
                    "e2e_accuracy": "NOT_APPLICABLE",
                },
            }
        },
    }
    cases = [
        {
            "case_id": "d04",
            "dimension_id": "D04",
            "status": "unsupported",
            "metrics": {},
            "unsupported_metrics": ["activation_decision"],
        }
    ]
    page = _special_dimension_page(summary, cases, "D04")
    timeline = _case_stage_timeline(
        {"case": {"dimension_id": "D04"}, "add": {}, "retrieval": {},
         "answer": {}, "judge": {}, "final": {}}
    )

    assert "Activation Recall" in page
    assert "NOT_APPLICABLE" in page
    assert "Answer/Judge" in page
    assert timeline.count("不适用") >= 2
    assert "timeline-not-applicable" in timeline

    payload = _quadrant_payload(summary, cases, "")
    assert payload["case"] == []
    assert payload["type"] == []
    assert payload["run"] == []


def test_special_dimension_index_links_stay_within_dimension_directory():
    page = _special_dimensions_index({"run_info": {}, "dimension_metrics": {}})

    assert 'href="d01.html"' in page
    assert 'href="d04.html"' in page
    assert 'href="d08.html"' in page
    assert 'href="dimensions/d01.html"' not in page


def test_privacy_failure_is_a_supported_trace_root_cause():
    analysis = {
        "judge": {},
        "final": {"root_cause": "PASS", "explanation": "", "suggested_fix": ""},
    }
    result = {
        "status": "ok",
        "dimension_id": "D08",
        "metrics": {"privacy_pass": 0.0},
    }

    MemEvalTraceAdapter._override_final(analysis, result)

    assert analysis["final"]["root_cause"] == "PRIVACY_FAILURE"
    assert "PRIVACY_FAILURE" in TRACE_ROOT_CAUSES
    assert "PRIVACY_FAILURE" in HTML_ROOT_CAUSES


def test_unverifiable_evidence_content_classifies_by_judge_and_retrieval():
    # MemEval Gold 无 turn 级标注时，通用分类器给出 PIPELINE_FAILURE；
    # 有 Judge 结论的 case 应按 Judge 结果归类，而不是判成链路缺失。
    judged_wrong = {
        "judge": {"is_correct": False},
        "final": {
            "root_cause": "PIPELINE_FAILURE",
            "explanation": "Labeled evidence turn content was unavailable.",
            "suggested_fix": "旧建议",
            "answer_pass": False,
            "retrieval_pass": False,
            "quadrant": "NOT_RECORDED",
        },
    }
    MemEvalTraceAdapter._override_final(
        judged_wrong,
        {"status": "ok", "dimension_id": "D03", "metrics": {"recall_at_k": 1.0, "retrieval_evaluated": True}},
    )
    assert judged_wrong["final"]["root_cause"] == "ANSWER_FAILURE"
    assert judged_wrong["final"]["suggested_fix"] != "旧建议"
    # retrieval_pass 以 Recall@K 为准，象限重算为 B（召回全 + 答错）
    assert judged_wrong["final"]["retrieval_pass"] is True
    assert judged_wrong["final"]["quadrant"] == "B: Retrieval PASS + Answer FAIL"

    judged_right = {
        "judge": {"is_correct": True},
        "final": {
            "root_cause": "PIPELINE_FAILURE",
            "explanation": "",
            "suggested_fix": "",
            "answer_pass": True,
            "retrieval_pass": False,
            "quadrant": "NOT_RECORDED",
        },
    }
    MemEvalTraceAdapter._override_final(
        judged_right,
        {"status": "ok", "dimension_id": "D02", "metrics": {"recall_at_k": 1.0, "retrieval_evaluated": True}},
    )
    assert judged_right["final"]["root_cause"] == "PASS"
    assert judged_right["final"]["quadrant"] == "A: Retrieval PASS + Answer PASS"

    # 召回不足时保持通用分类器的 RETRIEVAL_* 根因，象限为 C/D
    partial = {
        "judge": {"is_correct": True},
        "final": {
            "root_cause": "RETRIEVAL_PARTIAL",
            "explanation": "partial",
            "suggested_fix": "",
            "answer_pass": True,
            "retrieval_pass": False,
            "quadrant": "NOT_RECORDED",
        },
    }
    MemEvalTraceAdapter._override_final(
        partial,
        {"status": "ok", "dimension_id": "D02", "metrics": {"recall_at_k": 0.5, "retrieval_evaluated": True}},
    )
    assert partial["final"]["root_cause"] == "RETRIEVAL_PARTIAL"
    assert partial["final"]["retrieval_pass"] is False
    assert partial["final"]["quadrant"] == "C: Retrieval FAIL + Answer PASS"

    # 真正的管线 error 即使残留 Judge 分数也不能被重归类
    errored = {
        "judge": {"is_correct": True},
        "final": {"root_cause": "PIPELINE_FAILURE", "explanation": "", "suggested_fix": ""},
    }
    MemEvalTraceAdapter._override_final(
        errored,
        {"status": "error", "dimension_id": "D02", "error": {"message": "boom"}, "metrics": {}},
    )
    assert errored["final"]["root_cause"] == "PIPELINE_FAILURE"

    # Runner 实测召回为 0 时归为 RETRIEVAL_MISS（D07 needle 级），部分召回归 RETRIEVAL_PARTIAL
    miss = {
        "judge": {"is_correct": True},
        "final": {"root_cause": "PIPELINE_FAILURE", "explanation": "", "suggested_fix": ""},
    }
    MemEvalTraceAdapter._override_final(
        miss,
        {"status": "ok", "dimension_id": "D07", "metrics": {"recall_at_k": 0.0, "retrieval_evaluated": True}},
    )
    assert miss["final"]["root_cause"] == "RETRIEVAL_MISS"

    partial_recall = {
        "judge": {"is_correct": False},
        "final": {"root_cause": "PIPELINE_FAILURE", "explanation": "", "suggested_fix": ""},
    }
    MemEvalTraceAdapter._override_final(
        partial_recall,
        {"status": "ok", "dimension_id": "D07", "metrics": {"recall_at_k": 0.5, "retrieval_evaluated": True}},
    )
    assert partial_recall["final"]["root_cause"] == "RETRIEVAL_PARTIAL"


def test_add_row_status_depends_only_on_ingest_event():
    # Answer/Judge 阶段的旧 error（断点续跑残留）不能把成功的写入污染成 FAIL。
    adapter = MemEvalTraceAdapter.__new__(MemEvalTraceAdapter)
    canonical = {
        "case_id": "case-1",
        "sessions": [{"session_id": "s1", "messages": [{"event_id": "e1"}]}],
        "evidence_session_ids": ["s1"],
    }
    result = {
        "case_id": "case-1",
        "status": "error",
        "error": {"type": "LLMStageError", "message": "Answer/Judge output missing"},
        "trace": {"system": {"data": {"events": [
            {"operation": "ingest", "status": "ok", "items": [{"path": "a.md"}], "failures": []},
        ]}}},
    }
    row = adapter._add_row(result, canonical)
    assert row["add_status"] == "PASS"
    assert row["index_status"] == "PASS"
    assert row["added_sessions"] == 1
    assert row["added_evidence_sessions"] == 1
    assert row["add_error"] == "NOT_RECORDED"

    # ingest 本身失败时才判 FAIL，并记录 ingest 失败详情
    failed = {
        "case_id": "case-1",
        "status": "ok",
        "trace": {"system": {"data": {"events": [
            {"operation": "ingest", "status": "error", "failures": ["s1"]},
        ]}}},
    }
    row = adapter._add_row(failed, canonical)
    assert row["add_status"] == "FAIL"
    assert row["added_sessions"] == 0
    assert row["add_error"] == {"ingest_status": "error", "failures": ["s1"]}

    # 完全没有 ingest 事件（Runner 在写入前失败）保留 Runner error
    no_ingest = {"case_id": "case-1", "status": "error", "error": {"message": "load failed"}, "trace": {}}
    row = adapter._add_row(no_ingest, canonical)
    assert row["add_status"] == "FAIL"
    assert row["add_error"] == {"message": "load failed"}


def test_successful_llm_resume_clears_previous_llm_stage_error():
    with workspace_directory("memeval-llm-resume") as directory:
        results_path = directory / "results.jsonl"
        results_path.write_text(json.dumps({
            "case_id": "case-1",
            "dimension_id": "D03",
            "status": "error",
            "retrieval_status": "partial",
            "error": {"type": "LLMStageError", "message": "interrupted", "stage": "answer"},
            "metrics": {},
            "unsupported_metrics": ["answer_accuracy"],
            "trace": {},
            "latency": {},
        }) + "\n", encoding="utf-8")
        (directory / "llm_input.jsonl").write_text('{"id":"case-1"}\n', encoding="utf-8")
        (directory / "answers.jsonl").write_text(
            '{"id":"case-1","generated_answer":"answer","usage":{}}\n', encoding="utf-8"
        )
        (directory / "scores.jsonl").write_text(
            '{"id":"case-1","is_correct":true,"usage":{}}\n', encoding="utf-8"
        )
        (directory / "run_summary.json").write_text("{}\n", encoding="utf-8")

        adapter = MemEvalTraceAdapter.__new__(MemEvalTraceAdapter)
        adapter.run_dir = directory
        adapter.answer_env = {}
        adapter.judge_env = {}
        results = adapter.apply_llm_outputs(results_path)

        assert results[0]["status"] == "ok"
        assert results[0]["retrieval_status"] == "partial"
        assert results[0]["error"] is None
        assert results[0]["metrics"]["answer_accuracy"] == 1.0
