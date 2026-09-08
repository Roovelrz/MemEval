import json
from types import SimpleNamespace

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
                {"write_event_precision": 0.5, "write_event_recall": 1.0,
                 "written_memory_units": 2, "unexpected_written_event_count": 1},
            ),
            _result("d04", "D04", {}, ["activation_decision"]),
            _result(
                "d08", "D08",
                {"canary_exposure_count": 0, "forbidden_exposure_count": 0,
                 "deleted_exposure_count": 0, "privacy_pass": 1.0},
            ),
        ]
    )

    assert metrics["D01"]["metrics"]["write_precision"] == 0.5
    assert metrics["D01"]["metrics"]["write_recall"] == 1.0
    assert metrics["D04"]["availability"] == "UNSUPPORTED"
    assert metrics["D04"]["metrics"]["utilization_rate"] == "NOT_APPLICABLE"
    assert metrics["D08"]["metrics"]["sensitive_exposure_rate"] == 0.0
    assert metrics["D08"]["metrics"]["cross_user_leakage_rate"] == 0.0
    assert metrics["D08"]["metrics"]["deleted_memory_hit_rate"] == 0.0


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
