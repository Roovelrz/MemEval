"""Build human-readable end-to-end traces from existing eval artifacts.

This module is analysis-only: it never runs Retrieval, Answer, or Judge and it
never modifies their source artifacts. Missing observability is reported as
``NOT_RECORDED`` instead of being inferred as fact.
"""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

from memory_eval.dataset_integrity import freeze_dataset_integrity
from scripts.llm_eval_common import resolve_model_pricing, summarize_token_usage


NOT_RECORDED = "NOT_RECORDED"
NOT_APPLICABLE = "NOT_APPLICABLE"
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
    "PIPELINE_FAILURE": 0,
    "DATA_ERROR": 1,
    "ADD_FAILURE": 2,
    "INDEX_FAILURE": 3,
    "RETRIEVAL_MISS": 4,
    "RETRIEVAL_PARTIAL": 4,
    "RETRIEVAL_LOW_RANK": 4,
    "RETRIEVAL_WRONG_CHUNK": 5,
    "CONTEXT_LOSS": 6,
    "CONTEXT_TRUNCATION": 6,
    "ANSWER_FAILURE": 7,
    "JUDGE_SUSPECT": 8,
    "API_FAILURE": 9,
    "TIMEOUT": 9,
    "PASS": 10,
}


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"{path}:{line_number} must contain a JSON object")
        rows.append(value)
    return rows


def _row_id(row: dict[str, Any]) -> str:
    value = row.get("id", row.get("case_id"))
    return "" if value is None else str(value)


def _index_rows(rows: Iterable[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    output: dict[str, dict[str, Any]] = {}
    for row in rows:
        ident = _row_id(row)
        if ident:
            output[ident] = row
    return output


def _load_dataset(path: Path | None) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    if path is None or not path.is_file():
        return {}, {}
    if path.suffix.lower() == ".jsonl":
        cases = _read_jsonl(path)
        metadata: dict[str, Any] = {}
    else:
        payload = _read_json(path)
        if isinstance(payload, list):
            cases = payload
            metadata = {}
        elif isinstance(payload, dict):
            for key in ("cases", "items", "data", "samples"):
                if isinstance(payload.get(key), list):
                    cases = payload[key]
                    break
            else:
                cases = []
            metadata = {key: value for key, value in payload.items() if key != "cases"}
        else:
            cases = []
            metadata = {}
    return {
        str(case.get("case_id", case.get("question_id", case.get("id", "")))): case
        for case in cases
        if isinstance(case, dict)
    }, metadata


def _dataset_sessions(case: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not case:
        return []
    sessions = case.get("sessions")
    if isinstance(sessions, list):
        return [session for session in sessions if isinstance(session, dict)]
    histories = case.get("haystack_sessions")
    if not isinstance(histories, list):
        return []
    ids = case.get("haystack_session_ids", [])
    dates = case.get("haystack_dates", [])
    evidence = {str(value) for value in case.get("answer_session_ids", [])}
    return [
        {
            "session_id": str(ids[index]) if index < len(ids) else f"session_{index:04d}",
            "timestamp": str(dates[index]) if index < len(dates) else "",
            "turns": history,
            "is_evidence_session": str(ids[index]) in evidence if index < len(ids) else False,
        }
        for index, history in enumerate(histories)
    ]


def _session_id(session: dict[str, Any]) -> str:
    return str(session.get("session_id", session.get("id", "")))


def _session_turns(session: dict[str, Any]) -> list[dict[str, Any]]:
    turns = session.get("turns", session.get("messages", []))
    return [turn for turn in turns if isinstance(turn, dict)] if isinstance(turns, list) else []


def _is_answer_turn(turn: dict[str, Any]) -> bool:
    value = turn.get("has_answer")
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() == "true"


def _evidence_turn_texts(session: dict[str, Any]) -> list[str]:
    return [str(turn.get("content", turn.get("text", ""))) for turn in _session_turns(session) if _is_answer_turn(turn)]


def _normalize_text(value: object) -> str:
    return re.sub(r"\s+", "", str(value or "")).lower()


def _normalize_answer(value: object) -> str:
    """Normalize spacing and punctuation for a conservative surface comparison."""
    return re.sub(r"[\W_]+", "", str(value or ""), flags=re.UNICODE).lower()


def _safe_name(value: str) -> str:
    cleaned = "".join(char if char.isalnum() or char in "._-" else "_" for char in value)
    return cleaned.strip("._") or "unnamed"


def _display(value: Any, digits: int = 4) -> str:
    if value is None:
        return NOT_RECORDED
    if isinstance(value, bool):
        return "YES" if value else "NO"
    if isinstance(value, float):
        return f"{value:.{digits}f}"
    return str(value)


def _pct(value: float | None) -> str:
    return NOT_RECORDED if value is None else f"{value * 100:.1f}%"


def _pp(value: float | None) -> str:
    return NOT_RECORDED if value is None else f"{value * 100:+.1f} pp"


def _mean(values: Iterable[Any]) -> float | None:
    usable = [float(value) for value in values if isinstance(value, (int, float))]
    return sum(usable) / len(usable) if usable else None


def _percentile(values: Iterable[Any], quantile: float) -> float | None:
    usable = sorted(float(value) for value in values if isinstance(value, (int, float)))
    if not usable:
        return None
    position = (len(usable) - 1) * quantile
    lower = int(position)
    upper = min(lower + 1, len(usable) - 1)
    fraction = position - lower
    return usable[lower] + (usable[upper] - usable[lower]) * fraction


def _read_text_artifact(run_dir: Path, value: object) -> str | None:
    if not value:
        return None
    path = Path(str(value))
    if not path.is_file():
        path = run_dir / path.name
    return path.read_text(encoding="utf-8") if path.is_file() else None


def _failure_category(failure: dict[str, Any] | None) -> str | None:
    if not failure:
        return None
    category = str(failure.get("api_category", "")).lower()
    error = f"{failure.get('error_type', '')} {failure.get('error', '')}".lower()
    if category == "timeout" or "timeout" in error or "timed out" in error:
        return "TIMEOUT"
    if category or "http" in error or "connection" in error or "rate limit" in error:
        return "API_FAILURE"
    return None


def _suggestion(root_cause: str) -> str:
    return {
        "PASS": "无需修复；保留为回归样例。",
        "DATA_ERROR": "修复数据集缺失字段或 Evidence 引用后重新冻结版本。",
        "ADD_FAILURE": "检查失败 session 的写入路径、空内容和重复 ID。",
        "INDEX_FAILURE": "检查 raw_reindex 回执、失败路径和 ReMe service log。",
        "RETRIEVAL_MISS": "调整 query、BM25 分词或扩大候选集，先保证召回。",
        "RETRIEVAL_PARTIAL": "针对多 Evidence case 扩大召回并检查分散证据的关键词覆盖。",
        "RETRIEVAL_LOW_RANK": "优化排序或提高 TopK，观察 Evidence 与 distractor 的分差。",
        "RETRIEVAL_WRONG_CHUNK": "调整 chunk 策略，确保命中 session 时返回含答案的片段。",
        "CONTEXT_LOSS": "检查 retrieval 到 prepared/prompt 的序列化与字段映射。",
        "CONTEXT_TRUNCATION": "缩短 distractor 或提高上下文预算，并保留 Evidence。",
        "ANSWER_FAILURE": "在 Evidence 已完整到达后，检查 Answer prompt 的推理和格式约束。",
        "JUDGE_SUSPECT": "人工复核 Judge 原始响应，必要时校准 Judge prompt。",
        "API_FAILURE": "检查 API 状态码、重试与服务端错误记录。",
        "TIMEOUT": "检查超时层级并调整 timeout/retry，确认是否存在异常长输入。",
        "PIPELINE_FAILURE": "按缺失产物对应的阶段日志恢复链路。",
    }[root_cause]


def _markdown(value: object) -> str:
    return str(value if value is not None else NOT_RECORDED).replace("|", "\\|").replace("\n", " ")


def _excerpt(value: object, limit: int = 180) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    return text if len(text) <= limit else text[: limit - 1] + "…"


def _fenced_text(value: object) -> list[str]:
    """Return a Markdown fence longer than any backtick run in the content."""
    text = str(value or NOT_RECORDED)
    longest = max((len(match.group(0)) for match in re.finditer(r"`+", text)), default=0)
    fence = "`" * max(3, longest + 1)
    return [f"{fence}text", text, fence]


def _find_results(node: Any) -> list[dict[str, Any]] | None:
    if isinstance(node, dict):
        results = node.get("results")
        if isinstance(results, list):
            return [item for item in results if isinstance(item, dict)]
        for value in node.values():
            found = _find_results(value)
            if found is not None:
                return found
    elif isinstance(node, list):
        for value in node:
            found = _find_results(value)
            if found is not None:
                return found
    return None


def _raw_result_path(result: dict[str, Any]) -> str:
    for source in (result, result.get("metadata", {})):
        if isinstance(source, dict):
            for key in ("path", "source", "file"):
                if source.get(key):
                    return str(source[key])
    return ""


def _raw_ranked_sessions(
    retrieval: dict[str, Any],
    run_dir: Path,
    sessions: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    raw_path_value = retrieval.get("raw_search_file")
    if not raw_path_value:
        return []
    raw_path = Path(str(raw_path_value))
    if not raw_path.is_file():
        candidate = run_dir / "raw_search" / raw_path.name
        raw_path = candidate if candidate.is_file() else raw_path
    if not raw_path.is_file():
        return []
    results = _find_results(_read_json(raw_path)) or []
    stem_map = {_safe_name(_session_id(session)): _session_id(session) for session in sessions}
    seen: set[str] = set()
    output: list[dict[str, Any]] = []
    for raw_rank, result in enumerate(results, start=1):
        path = _raw_result_path(result).replace("\\", "/")
        stem = Path(path).stem
        ident = stem_map.get(stem, stem)
        if not ident or ident in seen:
            continue
        seen.add(ident)
        output.append({"rank": len(output) + 1, "raw_rank": raw_rank, "session_id": ident})
    return output


def _content_status(
    evidence_ids: list[str],
    session_map: dict[str, dict[str, Any]],
    texts_by_session: dict[str, list[str]],
) -> tuple[str, dict[str, str]]:
    per_session: dict[str, str] = {}
    recorded = 0
    present = 0
    for ident in evidence_ids:
        session = session_map.get(ident)
        evidence_texts = _evidence_turn_texts(session) if session else []
        candidate_texts = texts_by_session.get(ident, [])
        if not evidence_texts:
            per_session[ident] = NOT_RECORDED
            continue
        recorded += 1
        normalized_candidates = [_normalize_text(text) for text in candidate_texts]
        matched = any(
            _normalize_text(evidence_text) in candidate
            for evidence_text in evidence_texts
            for candidate in normalized_candidates
            if evidence_text and candidate
        )
        per_session[ident] = "YES" if matched else "NO"
        present += int(matched)
    if recorded == 0:
        return NOT_RECORDED, per_session
    if present == recorded == len(evidence_ids):
        return "YES", per_session
    if present:
        return "PARTIAL", per_session
    return "NO", per_session


def _judge_suspicions(
    score: dict[str, Any] | None,
    generated_answer: str | None,
    gold_answer: str,
    judge_failure: dict[str, Any] | None,
) -> list[str]:
    reasons: list[str] = []
    if judge_failure:
        reasons.append(f"Judge pipeline failure: {judge_failure.get('error', 'unknown error')}")
    if not score:
        return reasons
    label = str(score.get("label", "")).upper()
    is_correct = score.get("is_correct")
    if label in {"CORRECT", "WRONG"} and isinstance(is_correct, bool):
        if (label == "CORRECT") != is_correct:
            reasons.append("Parsed label and is_correct disagree")
    raw = str(score.get("judge_response", ""))
    raw_labels = set(re.findall(r"\b(CORRECT|WRONG)\b", raw.upper()))
    if label and len(raw_labels) == 1 and label not in raw_labels:
        reasons.append("Raw response label and parsed label disagree")
    if label == "WRONG" and generated_answer is not None:
        if _normalize_answer(generated_answer) == _normalize_answer(gold_answer):
            reasons.append("Generated answer exactly matches gold after whitespace normalization")
    return reasons


def _classify(case: dict[str, Any]) -> tuple[str, str]:
    add = case["add"]
    retrieval = case["retrieval"]
    answer = case["answer"]
    judge = case["judge"]
    if add["evidence_dataset_status"] == "FAIL":
        return "DATA_ERROR", "Gold evidence session IDs are missing from the dataset input."
    if add["add_status"] == "FAIL":
        return "ADD_FAILURE", "One or more expected sessions failed during Memory input writing."
    if add["index_status"] == "FAIL":
        return "INDEX_FAILURE", "ReMe indexing failed or reported failed paths for this case."
    if not retrieval["recorded"]:
        failure_type = _failure_category(retrieval.get("failure"))
        if failure_type:
            return failure_type, "Retrieval did not complete because its API call failed."
        return "PIPELINE_FAILURE", "No successful Retrieval artifact was recorded for this case."
    total_evidence = retrieval["gold_evidence_count"]
    retrieved_evidence = retrieval["retrieved_evidence_count"]
    if total_evidence:
        if retrieved_evidence == 0:
            if retrieval["first_evidence_rank_full"] is not None:
                return (
                    "RETRIEVAL_LOW_RANK",
                    f"Evidence was found only at candidate rank {retrieval['first_evidence_rank_full']}, outside TopK.",
                )
            return "RETRIEVAL_MISS", "No gold evidence session appeared in TopK or the recorded candidate list."
        if retrieved_evidence < total_evidence:
            return (
                "RETRIEVAL_PARTIAL",
                f"Only {retrieved_evidence}/{total_evidence} gold evidence sessions appeared in TopK.",
            )
        if retrieval["evidence_content_present"] in {"NO", "PARTIAL"}:
            return "RETRIEVAL_WRONG_CHUNK", "Evidence session IDs were retrieved, but labeled evidence turn content was incomplete."
        if retrieval["evidence_content_present"] == NOT_RECORDED:
            return "PIPELINE_FAILURE", "Labeled evidence turn content was unavailable, so Retrieval content could not be verified."
        if answer["evidence_in_retrieved_context"] in {"NO", "PARTIAL"}:
            return "CONTEXT_LOSS", "Retrieved evidence did not fully survive into prepared retrieved_context."
        if answer["evidence_in_retrieved_context"] == NOT_RECORDED:
            return "PIPELINE_FAILURE", "Answer-context evidence could not be verified from the recorded dataset and prepared input."
        if answer["truncation_occurred"] is True:
            return "CONTEXT_TRUNCATION", "The Answer client truncated the prompt before sending it."
        if answer["evidence_in_prompt"] in {"NO", "PARTIAL"}:
            return "CONTEXT_LOSS", "Evidence existed in prepared context but did not fully reach the persisted Answer prompt."
    if not answer["recorded"]:
        if answer["failure"]:
            failure_type = _failure_category(answer["failure"])
            if failure_type:
                return failure_type, "Answer generation failed at the LLM API layer."
            return "ANSWER_FAILURE", "Answer generation failed before producing a usable answer."
        return "PIPELINE_FAILURE", "Answer output is missing or Answer generation failed."
    if not judge["recorded"]:
        if judge["failure"]:
            failure_type = _failure_category(judge["failure"])
            if failure_type:
                return failure_type, "Judge failed at the LLM API layer."
            return "JUDGE_SUSPECT", "Judge failed before producing a usable score; manual review is required."
        return "PIPELINE_FAILURE", "Judge score is missing without a recorded Judge failure."
    if judge["suspect_reasons"]:
        return "JUDGE_SUSPECT", judge["suspect_reasons"][0]
    if judge["is_correct"] is False:
        return "ANSWER_FAILURE", "All evidence reached the Answer context, but Judge marked the generated answer WRONG."
    return "PASS", "Retrieval found all evidence, the evidence content reached Answer context, and Judge marked the answer CORRECT."


def _case_analysis(
    ident: str,
    run_dir: Path,
    dataset_case: dict[str, Any] | None,
    prepared: dict[str, Any] | None,
    retrieval: dict[str, Any] | None,
    answer: dict[str, Any] | None,
    score: dict[str, Any] | None,
    add_trace: dict[str, Any] | None,
    retrieval_failure: dict[str, Any] | None,
    answer_failure: dict[str, Any] | None,
    judge_failure: dict[str, Any] | None,
    top_k: int,
) -> dict[str, Any]:
    sessions = _dataset_sessions(dataset_case)
    session_map = {_session_id(session): session for session in sessions}
    evidence_ids = [
        str(value)
        for value in (
            (dataset_case or {}).get("answer_session_ids")
            or (dataset_case or {}).get("evidence_session_ids")
            or (retrieval or {}).get("evidence_session_ids")
            or []
        )
    ]
    question = str(
        (prepared or {}).get("question")
        or (retrieval or {}).get("question")
        or (dataset_case or {}).get("question")
        or ""
    )
    gold = str(
        (prepared or {}).get("gold_answer")
        or (retrieval or {}).get("gold_answer")
        or (dataset_case or {}).get("gold_answer")
        or (dataset_case or {}).get("answer")
        or ""
    )
    question_type = str(
        (prepared or {}).get("question_type")
        or (retrieval or {}).get("question_type")
        or (dataset_case or {}).get("question_type")
        or ""
    )
    question_date = str(
        (prepared or {}).get("question_date")
        or (retrieval or {}).get("question_date")
        or (dataset_case or {}).get("question_date")
        or ""
    )
    session_ids = [_session_id(session) for session in sessions]
    duplicates = len(session_ids) - len(set(session_ids))
    missing_dataset_evidence = sorted(set(evidence_ids) - set(session_ids)) if sessions else []

    top_results: list[dict[str, Any]] = []
    retrieved_by_session: dict[str, list[str]] = {}
    if retrieval:
        for item in retrieval.get("retrieved", []):
            session_id = str(item.get("session_id", ""))
            text = str(item.get("text", ""))
            retrieved_by_session.setdefault(session_id, []).append(text)
            session = session_map.get(session_id, {})
            top_results.append(
                {
                    "rank": item.get("rank"),
                    "raw_rank": item.get("raw_rank"),
                    "session_id": session_id,
                    "score": item.get("score"),
                    "is_evidence": session_id in evidence_ids,
                    "timestamp": session.get("timestamp", NOT_RECORDED),
                    "text": text,
                    "text_excerpt": _excerpt(text),
                }
            )
    retrieved_evidence_ids = [
        item["session_id"] for item in top_results if item["is_evidence"]
    ]
    missing_evidence_ids = sorted(set(evidence_ids) - set(retrieved_evidence_ids))
    evidence_scores = [float(item["score"]) for item in top_results if item["is_evidence"] and item["score"] is not None]
    non_evidence_scores = [
        float(item["score"]) for item in top_results if not item["is_evidence"] and item["score"] is not None
    ]
    best_evidence_score = max(evidence_scores) if evidence_scores else None
    best_non_evidence_score = max(non_evidence_scores) if non_evidence_scores else None
    score_gap = (
        best_evidence_score - best_non_evidence_score
        if best_evidence_score is not None and best_non_evidence_score is not None
        else None
    )
    first_evidence_rank = next((item["rank"] for item in top_results if item["is_evidence"]), None)
    raw_ranked = _raw_ranked_sessions(retrieval or {}, run_dir, sessions)
    first_evidence_rank_full = next(
        (item["rank"] for item in raw_ranked if item["session_id"] in evidence_ids), None
    )
    evidence_content_status, evidence_content_by_session = _content_status(
        evidence_ids, session_map, retrieved_by_session
    )

    contexts = (prepared or {}).get("retrieved_context", [])
    if isinstance(contexts, str):
        contexts = [contexts]
    contexts = [str(value) for value in contexts] if isinstance(contexts, list) else []
    prepared_texts_by_session = {ident: contexts for ident in evidence_ids}
    prepared_content_status, prepared_content_by_session = _content_status(
        evidence_ids, session_map, prepared_texts_by_session
    )
    answer_prompt = _read_text_artifact(run_dir, (answer or {}).get("prompt_file"))
    if answer_prompt is None:
        answer_prompt_status = NOT_RECORDED
        answer_prompt_by_session = {ident: NOT_RECORDED for ident in evidence_ids}
    else:
        answer_prompt_status, answer_prompt_by_session = _content_status(
            evidence_ids,
            session_map,
            {ident: [answer_prompt] for ident in evidence_ids},
        )
    judge_prompt = _read_text_artifact(run_dir, (score or {}).get("prompt_file"))
    generated = str(answer.get("generated_answer")) if answer and answer.get("generated_answer") is not None else None
    if generated is None:
        difference = "Generated answer is missing."
    elif _normalize_answer(generated) == _normalize_answer(gold):
        difference = "Equivalent after whitespace and punctuation normalization."
    elif _normalize_text(gold) and _normalize_text(gold) in _normalize_text(generated):
        difference = "Generated answer contains the normalized gold answer plus additional text."
    elif _normalize_text(generated) and _normalize_text(generated) in _normalize_text(gold):
        difference = "Generated answer is shorter than the gold answer and may be partial."
    else:
        difference = "Surface forms differ; semantic equivalence requires Judge or human review."

    suspect_reasons = _judge_suspicions(score, generated, gold, judge_failure)
    analysis: dict[str, Any] = {
        "case": {
            "case_id": ident,
            "question_type": question_type,
            "question": question,
            "question_date": question_date,
            "gold_answer": gold,
            "evidence_session_ids": evidence_ids,
            "total_sessions": len(sessions) if sessions else (retrieval or {}).get("session_count"),
            "total_turns": sum(len(_session_turns(session)) for session in sessions) if sessions else None,
        },
        "add": {
            "expected_session_count": (add_trace or {}).get("expected_sessions", len(sessions) if sessions else (retrieval or {}).get("session_count")),
            "successfully_added_session_count": (add_trace or {}).get("added_sessions", NOT_RECORDED),
            "expected_turn_count": (add_trace or {}).get("expected_turns", sum(len(_session_turns(session)) for session in sessions) if sessions else NOT_RECORDED),
            "successfully_added_turn_count": (add_trace or {}).get("added_turns", NOT_RECORDED),
            "expected_evidence_session_count": (add_trace or {}).get("expected_evidence_sessions", len(evidence_ids)),
            "successfully_added_evidence_count": (add_trace or {}).get("added_evidence_sessions", NOT_RECORDED),
            "missing_evidence_in_dataset": missing_dataset_evidence,
            "evidence_dataset_status": "FAIL" if missing_dataset_evidence else ("PASS" if sessions else NOT_RECORDED),
            "evidence_add_status": (
                "PASS"
                if add_trace and add_trace.get("added_evidence_sessions") == add_trace.get("expected_evidence_sessions")
                else ((add_trace or {}).get("add_status", NOT_RECORDED))
            ),
            "add_latency_ms": (add_trace or {}).get("add_latency_ms", NOT_RECORDED),
            "reindex_latency_ms": (add_trace or {}).get("index_latency_ms", (retrieval or {}).get("index_latency_ms")),
            "workspace": (add_trace or {}).get("workspace", NOT_RECORDED),
            "namespace": (add_trace or {}).get("namespace", NOT_APPLICABLE),
            "user_id": (add_trace or {}).get("user_id", NOT_APPLICABLE),
            "duplicate_session_ids_in_dataset": (add_trace or {}).get("duplicate_session_ids", duplicates if sessions else NOT_RECORDED),
            "failed_session_ids": (add_trace or {}).get("failed_session_ids", NOT_RECORDED),
            "add_status": (add_trace or {}).get("add_status", NOT_RECORDED),
            "index_status": (add_trace or {}).get("index_status", NOT_RECORDED),
            "indexed_document_count": (add_trace or {}).get("indexed_document_count", NOT_RECORDED),
            "indexed_chunk_count": (add_trace or {}).get("indexed_chunk_count", NOT_RECORDED),
            "chunks_with_embedding": (add_trace or {}).get("chunks_with_embedding", NOT_RECORDED),
            "embedding_status": (add_trace or {}).get("embedding_status", NOT_RECORDED),
            "embedding_call_count": (add_trace or {}).get("embedding_call_count", NOT_RECORDED),
            "embedding_failure_count": (add_trace or {}).get("embedding_failure_count", NOT_RECORDED),
            "extraction_status": (add_trace or {}).get("extraction_status", NOT_RECORDED),
            "extraction_call_count": (add_trace or {}).get("extraction_call_count", NOT_RECORDED),
            "extraction_failure_count": (add_trace or {}).get("extraction_failure_count", NOT_RECORDED),
            "errors": (add_trace or {}).get("add_error") or (add_trace or {}).get("index_error") or NOT_RECORDED,
        },
        "retrieval": {
            "recorded": retrieval is not None,
            "query": question,
            "top_k": top_k,
            "hit_at_k": (retrieval or {}).get("hit_at_k"),
            "recall_at_k": (retrieval or {}).get("recall_at_k"),
            "mrr": (retrieval or {}).get("mrr"),
            "first_evidence_rank": first_evidence_rank,
            "first_evidence_rank_full": first_evidence_rank_full,
            "gold_evidence_count": len(evidence_ids),
            "retrieved_evidence_count": len(set(retrieved_evidence_ids)),
            "missing_evidence_ids": missing_evidence_ids,
            "best_evidence_score": best_evidence_score,
            "best_non_evidence_score": best_non_evidence_score,
            "evidence_score_gap": score_gap,
            "evidence_content_present": evidence_content_status,
            "evidence_content_by_session": evidence_content_by_session,
            "search_latency_ms": (retrieval or {}).get("search_latency_ms"),
            "raw_result_count": (retrieval or {}).get("raw_result_count"),
            "returned_session_count": (retrieval or {}).get("returned_session_count", len(top_results)),
            "search_status": (retrieval or {}).get("search_status", "PASS" if retrieval else NOT_RECORDED),
            "search_retry_count": (retrieval or {}).get("search_retry_count", NOT_RECORDED),
            "metrics_by_k": (retrieval or {}).get("metrics_by_k", {}),
            "mean_evidence_rank": (retrieval or {}).get("mean_evidence_rank"),
            "top_results": top_results,
            "failure": retrieval_failure,
        },
        "answer": {
            "recorded": answer is not None,
            "question": question,
            "context_count": len(contexts),
            "context_characters": sum(len(value) for value in contexts),
            "context_token_estimate": (answer or {}).get("context_token_estimate", (sum(len(value) for value in contexts) + 3) // 4),
            "context_order": [str(item.get("session_id", "")) for item in (retrieval or {}).get("retrieved", [])],
            "context_timestamps": [str(item.get("timestamp", "")) for item in (prepared or {}).get("retrieved_context_metadata", [])],
            "evidence_context_positions": [
                index + 1
                for index, item in enumerate((retrieval or {}).get("retrieved", []))
                if str(item.get("session_id", "")) in evidence_ids
            ],
            "distractor_count": sum(
                str(item.get("session_id", "")) not in evidence_ids
                for item in (retrieval or {}).get("retrieved", [])
            ),
            "retrieved_contexts": contexts,
            "retrieved_context_excerpts": [_excerpt(value, 240) for value in contexts],
            "evidence_in_retrieved_context": prepared_content_status,
            "evidence_in_context_by_session": prepared_content_by_session,
            "evidence_in_prompt": answer_prompt_status,
            "evidence_in_prompt_by_session": answer_prompt_by_session,
            "answer_prompt": (answer or {}).get("prompt_file", NOT_RECORDED),
            "answer_prompt_version": (answer or {}).get("prompt_version", NOT_RECORDED),
            "answer_prompt_sha256": (answer or {}).get("prompt_sha256", NOT_RECORDED),
            "answer_prompt_note": "Exact sent prompt is persisted and referenced above." if answer_prompt is not None else "Exact sent prompt was not available.",
            "truncation_occurred": (answer or {}).get("client_truncation_occurred", NOT_RECORDED),
            "evidence_before_truncation": prepared_content_status,
            "evidence_after_truncation": answer_prompt_status,
            "generated_answer": generated,
            "gold_answer": gold,
            "answer_difference": difference,
            "model": (answer or {}).get("model"),
            "latency_ms": (answer or {}).get("latency_ms"),
            "usage": (answer or {}).get("usage"),
            "failure": answer_failure,
        },
        "judge": {
            "recorded": score is not None,
            "judge_prompt": (score or {}).get("prompt_file", NOT_RECORDED),
            "judge_prompt_version": (score or {}).get("prompt_version", NOT_RECORDED),
            "judge_prompt_sha256": (score or {}).get("prompt_sha256", NOT_RECORDED),
            "judge_prompt_persisted": judge_prompt is not None,
            "generated_answer": generated,
            "gold_answer": gold,
            "raw_response": (score or {}).get("judge_response", (judge_failure or {}).get("judge_response")),
            "parsed_label": (score or {}).get("label"),
            "is_correct": (score or {}).get("is_correct"),
            "model": (score or {}).get("model"),
            "latency_ms": (score or {}).get("latency_ms"),
            "usage": (score or {}).get("usage"),
            "human_review": NOT_RECORDED,
            "suspect_reasons": suspect_reasons,
            "failure": judge_failure,
        },
    }
    root_cause, explanation = _classify(analysis)
    retrieval_pass = (
        len(evidence_ids) > 0
        and len(set(retrieved_evidence_ids)) == len(set(evidence_ids))
        and analysis["retrieval"]["evidence_content_present"] == "YES"
    )
    answer_pass = analysis["judge"]["is_correct"] if isinstance(analysis["judge"]["is_correct"], bool) else None
    if answer_pass is None:
        quadrant = NOT_RECORDED
    elif retrieval_pass and answer_pass:
        quadrant = "A: Retrieval PASS + Answer PASS"
    elif retrieval_pass and not answer_pass:
        quadrant = "B: Retrieval PASS + Answer FAIL"
    elif not retrieval_pass and answer_pass:
        quadrant = "C: Retrieval FAIL + Answer PASS"
    else:
        quadrant = "D: Retrieval FAIL + Answer FAIL"
    analysis["final"] = {
        "retrieval_pass": retrieval_pass,
        "answer_pass": answer_pass,
        "quadrant": quadrant,
        "root_cause": root_cause,
        "explanation": explanation,
        "suggested_fix": _suggestion(root_cause),
        "pipeline_complete": retrieval is not None and answer is not None and score is not None,
    }
    return analysis


def _render_case(case: dict[str, Any]) -> str:
    basic, add, retrieval, answer, judge, final = (
        case["case"], case["add"], case["retrieval"], case["answer"], case["judge"], case["final"]
    )
    lines = [
        f"# Case Trace: {basic['case_id']}",
        "",
        f"> **Root Cause:** `{final['root_cause']}`  ",
        f"> **Quadrant:** {final['quadrant']}  ",
        f"> {final['explanation']}",
        "",
        "## 1. Case",
        "",
        "| Field | Value |",
        "| --- | --- |",
        f"| case_id | `{_markdown(basic['case_id'])}` |",
        f"| question_type | {_markdown(basic['question_type'])} |",
        f"| question_date | {_markdown(basic['question_date'])} |",
        f"| question | {_markdown(basic['question'])} |",
        f"| gold_answer | {_markdown(basic['gold_answer'])} |",
        f"| evidence_session_ids | {_markdown(', '.join(basic['evidence_session_ids']) or '[]')} |",
        f"| total_sessions | {_display(basic['total_sessions'])} |",
        f"| total_turns | {_display(basic['total_turns'])} |",
        "",
        "## 2. Add Trace",
        "",
        "| Field | Value |",
        "| --- | --- |",
        f"| Expected sessions | {_display(add['expected_session_count'])} |",
        f"| Successfully added sessions | {_display(add['successfully_added_session_count'])} |",
        f"| Expected turns | {_display(add['expected_turn_count'])} |",
        f"| Successfully added turns | {_display(add['successfully_added_turn_count'])} |",
        f"| Expected evidence sessions | {_display(add['expected_evidence_session_count'])} |",
        f"| Successfully added evidence sessions | {_display(add['successfully_added_evidence_count'])} |",
        f"| Evidence exists in dataset | {add['evidence_dataset_status']} |",
        f"| Evidence Add Status | {add['evidence_add_status']} |",
        f"| Add Status | {add['add_status']} |",
        f"| Index Status | {add['index_status']} |",
        f"| Indexed documents | {_display(add['indexed_document_count'])} |",
        f"| Indexed chunks | {_display(add['indexed_chunk_count'])} |",
        f"| Chunks with embedding | {_display(add['chunks_with_embedding'])} |",
        f"| Embedding status / calls / failures | {_display(add['embedding_status'])} / {_display(add['embedding_call_count'])} / {_display(add['embedding_failure_count'])} |",
        f"| Extraction status / calls / failures | {_display(add['extraction_status'])} / {_display(add['extraction_call_count'])} / {_display(add['extraction_failure_count'])} |",
        f"| Add latency | {_display(add['add_latency_ms'])} |",
        f"| Reindex latency | {_display(add['reindex_latency_ms'])} ms |",
        f"| Workspace | {_markdown(add['workspace'])} |",
        f"| Namespace | {_markdown(add['namespace'])} |",
        f"| User ID | {_markdown(add['user_id'])} |",
        f"| Failed session IDs | {_markdown(add['failed_session_ids'])} |",
        f"| Duplicate session IDs in dataset | {_display(add['duplicate_session_ids_in_dataset'])} |",
        f"| Errors | {_markdown(add['errors'])} |",
        "",
        "## 3. Retrieval Trace",
        "",
        "| Metric | Value |",
        "| --- | ---: |",
        f"| Query | {_markdown(retrieval['query'])} |",
        f"| TopK | {retrieval['top_k']} |",
        f"| Hit@K | {_display(retrieval['hit_at_k'])} |",
        f"| Recall@K | {_display(retrieval['recall_at_k'])} |",
        f"| MRR | {_display(retrieval['mrr'])} |",
        f"| First evidence rank in TopK | {_display(retrieval['first_evidence_rank'])} |",
        f"| First evidence rank in recorded candidates | {_display(retrieval['first_evidence_rank_full'])} |",
        f"| Retrieved evidence | {retrieval['retrieved_evidence_count']} / {retrieval['gold_evidence_count']} |",
        f"| Missing evidence IDs | {_markdown(', '.join(retrieval['missing_evidence_ids']) or 'None')} |",
        f"| Best evidence score | {_display(retrieval['best_evidence_score'])} |",
        f"| Best non-evidence score | {_display(retrieval['best_non_evidence_score'])} |",
        f"| Evidence score gap | {_display(retrieval['evidence_score_gap'])} |",
        f"| Evidence content present | {retrieval['evidence_content_present']} |",
        f"| Raw result count | {_display(retrieval['raw_result_count'])} |",
        f"| Returned session count | {_display(retrieval['returned_session_count'])} |",
        f"| Search status | {_display(retrieval['search_status'])} |",
        f"| Search retries | {_display(retrieval['search_retry_count'])} |",
        f"| Mean evidence rank | {_display(retrieval['mean_evidence_rank'])} |",
        f"| Search latency | {_display(retrieval['search_latency_ms'])} ms |",
        f"| Retrieval failure | {_markdown(json.dumps(retrieval['failure'], ensure_ascii=False) if retrieval['failure'] else 'None')} |",
        "",
        "### Top Results",
        "",
        "| Rank | Session ID | Score | Evidence | Timestamp | Text excerpt |",
        "| ---: | --- | ---: | :---: | --- | --- |",
    ]
    for item in retrieval["top_results"]:
        marker = "✓" if item["is_evidence"] else ""
        lines.append(
            f"| {item['rank']} | `{_markdown(item['session_id'])}` | {_display(item['score'])} | {marker} | "
            f"{_markdown(item['timestamp'])} | {_markdown(item['text_excerpt'])} |"
        )
    if not retrieval["top_results"]:
        lines.append("| - | - | - | - | - | No successful retrieval results recorded |")
    lines.extend(["", "### Evidence content verification", ""])
    for ident, status in retrieval["evidence_content_by_session"].items():
        lines.append(f"- `{ident}`: **{status}**")
    if not retrieval["evidence_content_by_session"]:
        lines.append(f"- {NOT_RECORDED}")
    lines.extend(
        [
            "",
            "## 4. Answer Trace",
            "",
            "| Field | Value |",
            "| --- | --- |",
            f"| Context count | {answer['context_count']} |",
            f"| Context characters | {answer['context_characters']} |",
            f"| Context token estimate | {answer['context_token_estimate']} |",
            f"| Context order | {_markdown(' → '.join(answer['context_order']) or '[]')} |",
            f"| Context timestamps | {_markdown(' → '.join(answer['context_timestamps']) or '[]')} |",
            f"| Evidence context positions | {_markdown(answer['evidence_context_positions'])} |",
            f"| Distractor count | {answer['distractor_count']} |",
            f"| Evidence in retrieved_context | {answer['evidence_in_retrieved_context']} |",
            f"| Evidence in final prompt | {answer['evidence_in_prompt']} |",
            f"| Answer Prompt | {_markdown(answer['answer_prompt'])} |",
            f"| Answer Prompt Version | {_markdown(answer['answer_prompt_version'])} |",
            f"| Answer Prompt SHA256 | {_markdown(answer['answer_prompt_sha256'])} |",
            f"| Truncation occurred | {answer['truncation_occurred']} |",
            f"| Evidence before truncation | {answer['evidence_before_truncation']} |",
            f"| Evidence after truncation | {answer['evidence_after_truncation']} |",
            f"| Generated answer | {_markdown(answer['generated_answer'])} |",
            f"| Gold answer | {_markdown(answer['gold_answer'])} |",
            f"| Main difference | {_markdown(answer['answer_difference'])} |",
            f"| Model | {_markdown(answer['model'])} |",
            f"| Answer latency | {_display(answer['latency_ms'])} ms |",
            f"| Failure | {_markdown(json.dumps(answer['failure'], ensure_ascii=False) if answer['failure'] else 'None')} |",
            "",
            f"> {answer['answer_prompt_note']}",
            "",
            "### Retrieved context excerpts",
            "",
        ]
    )
    for index, excerpt in enumerate(answer["retrieved_context_excerpts"], start=1):
        session_id = answer["context_order"][index - 1] if index <= len(answer["context_order"]) else NOT_RECORDED
        lines.append(f"{index}. `{session_id}` — {_markdown(excerpt)}")
    if not answer["retrieved_context_excerpts"]:
        lines.append(f"- {NOT_RECORDED}")
    lines.extend(["", "<details>", "<summary>Full retrieved_context (expand for provenance)</summary>", ""])
    for index, context in enumerate(answer["retrieved_contexts"], start=1):
        session_id = answer["context_order"][index - 1] if index <= len(answer["context_order"]) else NOT_RECORDED
        lines.extend([f"### Context {index}: `{session_id}`", "", *_fenced_text(context), ""])
    if not answer["retrieved_contexts"]:
        lines.extend([NOT_RECORDED, ""])
    lines.extend(["</details>"])
    lines.extend(
        [
            "",
            "## 5. Judge Trace",
            "",
            "| Field | Value |",
            "| --- | --- |",
            f"| Judge Prompt | {_markdown(judge['judge_prompt'])} |",
            f"| Judge Prompt Version | {_markdown(judge['judge_prompt_version'])} |",
            f"| Judge Prompt SHA256 | {_markdown(judge['judge_prompt_sha256'])} |",
            f"| Judge Prompt persisted | {_display(judge['judge_prompt_persisted'])} |",
            f"| Parsed label | {_markdown(judge['parsed_label'])} |",
            f"| is_correct | {_display(judge['is_correct'])} |",
            f"| Human review | {judge['human_review']} |",
            f"| Model | {_markdown(judge['model'])} |",
            f"| Judge latency | {_display(judge['latency_ms'])} ms |",
            f"| Suspect reasons | {_markdown('; '.join(judge['suspect_reasons']) or 'None')} |",
            f"| Failure | {_markdown(json.dumps(judge['failure'], ensure_ascii=False) if judge['failure'] else 'None')} |",
            "",
            "### Judge raw response",
            "",
            *_fenced_text(judge["raw_response"]),
            "",
            "## 6. Root Cause",
            "",
            f"**`{final['root_cause']}`**",
            "",
            final["explanation"],
            "",
            f"**修复建议：** {final['suggested_fix']}",
            "",
            "## Source artifacts",
            "",
            "- [retrieval.jsonl](../../retrieval.jsonl)",
            "- [prepared.jsonl](../../prepared.jsonl)",
            "- [answers.jsonl](../../answers.jsonl)",
            "- [scores.jsonl](../../scores.jsonl)",
            "- [end_to_end_summary.json](../../end_to_end_summary.json)",
            "",
        ]
    )
    return "\n".join(lines)


def _render_index(cases: list[dict[str, Any]]) -> str:
    ordered = sorted(cases, key=lambda case: (ROOT_PRIORITY[case["final"]["root_cause"]], case["case"]["case_id"]))
    lines = [
        "# Trace Index",
        "",
        "Cases are ordered by failure priority: pipeline → add → retrieval → context → answer → judge → pass.",
        "",
        "| Case | Question type | Hit@K | Recall@K | First evidence rank | Answer correct | Judge label | Root Cause |",
        "| --- | --- | ---: | ---: | ---: | :---: | --- | --- |",
    ]
    for case in ordered:
        basic, retrieval, judge, final = case["case"], case["retrieval"], case["judge"], case["final"]
        file_name = _safe_name(basic["case_id"]) + ".md"
        lines.append(
            f"| [{_markdown(basic['case_id'])}](cases/{file_name}) | {_markdown(basic['question_type'])} | "
            f"{_display(retrieval['hit_at_k'])} | {_display(retrieval['recall_at_k'])} | "
            f"{_display(retrieval['first_evidence_rank'])} | {_display(judge['is_correct'])} | "
            f"{_markdown(judge['parsed_label'])} | `{final['root_cause']}` |"
        )
    return "\n".join(lines) + "\n"


def _render_judge_review(cases: list[dict[str, Any]]) -> str:
    review = [
        case
        for case in cases
        if case["judge"]["is_correct"] is False
        or case["judge"]["failure"]
        or case["judge"]["suspect_reasons"]
    ]
    lines = [
        "# Judge Review",
        "",
        "This file lists every Judge=WRONG case plus Judge failures or automatic suspicion flags. Human review is not automated.",
        "",
    ]
    if not review:
        lines.append("No Judge=WRONG, Judge failure, or automatic Judge suspicion was recorded in this run.")
        return "\n".join(lines) + "\n"
    for case in review:
        basic, answer, judge, final = case["case"], case["answer"], case["judge"], case["final"]
        file_name = _safe_name(basic["case_id"]) + ".md"
        lines.extend(
            [
                f"## [{basic['case_id']}](cases/{file_name})",
                "",
                f"- Question: {basic['question']}",
                f"- Gold: {basic['gold_answer']}",
                f"- Generated: {answer['generated_answer'] or NOT_RECORDED}",
                f"- Parsed label: {judge['parsed_label'] or NOT_RECORDED}",
                f"- Root cause: `{final['root_cause']}`",
                f"- Automatic suspicion: {'; '.join(judge['suspect_reasons']) or 'None'}",
                f"- Human review: {judge['human_review']}",
                "",
                *_fenced_text(judge["raw_response"]),
                "",
            ]
        )
    return "\n".join(lines)


def _summary(cases: list[dict[str, Any]], run_dir: Path, top_k: int) -> dict[str, Any]:
    retrieval_rows = [case["retrieval"] for case in cases if case["retrieval"]["recorded"]]
    scored = [case for case in cases if isinstance(case["judge"]["is_correct"], bool)]
    root_counts = Counter(case["final"]["root_cause"] for case in cases)
    quadrant_counts = Counter(case["final"]["quadrant"] for case in cases if case["final"]["quadrant"] != NOT_RECORDED)
    retrieval_summary = _read_json(run_dir / "summary.json") if (run_dir / "summary.json").is_file() else {}
    answer_summary = _read_json(run_dir / "answer_summary.json") if (run_dir / "answer_summary.json").is_file() else {}
    judge_summary = _read_json(run_dir / "judge_summary.json") if (run_dir / "judge_summary.json").is_file() else {}
    run_config = _read_json(run_dir / "run_config.json") if (run_dir / "run_config.json").is_file() else {}
    run_metadata = _read_json(run_dir / "run_metadata.json") if (run_dir / "run_metadata.json").is_file() else {}
    manifest = _read_json(run_dir / "dataset_manifest.json") if (run_dir / "dataset_manifest.json").is_file() else {}
    dataset_validation = _read_json(run_dir / "dataset_validation.json") if (run_dir / "dataset_validation.json").is_file() else {}
    api_errors = _read_jsonl(run_dir / "api_errors.jsonl")

    answer_summary = dict(answer_summary)
    judge_summary = dict(judge_summary)
    for stage_summary, stage_name in ((answer_summary, "answer"), (judge_summary, "judge")):
        stage_cases = [case for case in cases if isinstance(case[stage_name].get("usage"), dict)]
        pricing = stage_summary.get("pricing")
        if not isinstance(pricing, dict):
            stage_model = stage_summary.get("model")
            if not stage_model and stage_cases:
                stage_model = stage_cases[0][stage_name].get("model")
            pricing = resolve_model_pricing(str(stage_model or ""))
        stage_summary["pricing"] = pricing or NOT_RECORDED
        stage_summary["token_usage"] = summarize_token_usage(
            [case[stage_name]["usage"] for case in stage_cases],
            pricing,
        )

    question_types: dict[str, Any] = {}
    for question_type in sorted({case["case"]["question_type"] for case in cases}):
        group = [case for case in cases if case["case"]["question_type"] == question_type]
        judged = [case for case in group if isinstance(case["judge"]["is_correct"], bool)]
        question_types[question_type] = {
            "case_count": len(group),
            f"hit_at_{top_k}": _mean(case["retrieval"]["hit_at_k"] for case in group),
            f"recall_at_{top_k}": _mean(case["retrieval"]["recall_at_k"] for case in group),
            "mrr": _mean(case["retrieval"]["mrr"] for case in group),
            "accuracy": _mean(case["judge"]["is_correct"] for case in judged),
            "avg_search_latency_ms": _mean(case["retrieval"]["search_latency_ms"] for case in group),
        }

    evidence_groups: dict[str, Any] = {}
    for label, predicate in (
        ("single_evidence", lambda count: count == 1),
        ("multiple_evidence", lambda count: count > 1),
    ):
        group = [case for case in cases if predicate(case["retrieval"]["gold_evidence_count"])]
        evidence_groups[label] = {
            "case_count": len(group),
            f"recall_at_{top_k}": _mean(case["retrieval"]["recall_at_k"] for case in group),
            "accuracy": _mean(case["judge"]["is_correct"] for case in group),
        }

    conditional_accuracy: dict[str, Any] = {}
    recall_groups = {
        "full_evidence_recall": lambda value: value == 1.0,
        "partial_evidence_recall": lambda value: isinstance(value, (int, float)) and 0 < value < 1,
        "zero_evidence_recall": lambda value: value == 0.0,
        "evidence_found": lambda value: isinstance(value, (int, float)) and value > 0,
    }
    for label, predicate in recall_groups.items():
        group = [case for case in cases if predicate(case["retrieval"]["recall_at_k"])]
        judged = [case for case in group if isinstance(case["judge"]["is_correct"], bool)]
        conditional_accuracy[label] = {
            "case_count": len(group),
            "judged_case_count": len(judged),
            "correct_count": sum(case["judge"]["is_correct"] is True for case in judged),
            "accuracy": _mean(case["judge"]["is_correct"] for case in judged),
        }
    for label, predicate in (
        ("has_gold_evidence", lambda count: count > 0),
        ("no_gold_evidence", lambda count: count == 0),
    ):
        group = [case for case in cases if predicate(case["retrieval"]["gold_evidence_count"])]
        judged = [case for case in group if isinstance(case["judge"]["is_correct"], bool)]
        conditional_accuracy[label] = {
            "case_count": len(group),
            "judged_case_count": len(judged),
            "correct_count": sum(case["judge"]["is_correct"] is True for case in judged),
            "accuracy": _mean(case["judge"]["is_correct"] for case in judged),
        }

    latency_sources = {
        "Add": [case["add"]["add_latency_ms"] for case in cases],
        "Index": [case["add"]["reindex_latency_ms"] for case in cases],
        "Search": [case["retrieval"]["search_latency_ms"] for case in cases],
        "Answer": [case["answer"]["latency_ms"] for case in cases],
        "Judge": [case["judge"]["latency_ms"] for case in cases],
    }
    latency_breakdown = {
        stage: {
            "avg": _mean(values),
            "p50": _percentile(values, 0.50),
            "p95": _percentile(values, 0.95),
            "p99": _percentile(values, 0.99),
        }
        for stage, values in latency_sources.items()
    }
    max_latency_stage = max(
        latency_breakdown,
        key=lambda stage: latency_breakdown[stage]["avg"] if latency_breakdown[stage]["avg"] is not None else -1,
    )
    end_to_end_latencies: list[float] = []
    for case in cases:
        values = (
            case["add"]["add_latency_ms"],
            case["add"]["reindex_latency_ms"],
            case["retrieval"]["search_latency_ms"],
            case["answer"]["latency_ms"],
            case["judge"]["latency_ms"],
        )
        if all(isinstance(value, (int, float)) for value in values):
            end_to_end_latencies.append(sum(float(value) for value in values))
    latency_breakdown["End-to-End"] = {
        "avg": _mean(end_to_end_latencies),
        "p50": _percentile(end_to_end_latencies, 0.50),
        "p95": _percentile(end_to_end_latencies, 0.95),
        "p99": _percentile(end_to_end_latencies, 0.99),
        "case_count": len(end_to_end_latencies),
        "method": "Per-case sum of Add, Index, Search, Answer, and Judge; excludes service startup and orchestration overhead.",
    }
    pipeline_success_rate = (
        sum(case["final"]["pipeline_complete"] for case in cases) / len(cases) if cases else None
    )
    grounded_success_rate = (
        sum(
            case["final"]["retrieval_pass"] and case["final"]["answer_pass"] is True
            for case in cases
        )
        / len(cases)
        if cases
        else None
    )
    overall_accuracy = _mean(case["judge"]["is_correct"] for case in scored)
    single_accuracy = evidence_groups["single_evidence"]["accuracy"]
    multiple_accuracy = evidence_groups["multiple_evidence"]["accuracy"]
    temporal_accuracy = question_types.get("temporal-reasoning", {}).get("accuracy")
    knowledge_update_accuracy = question_types.get("knowledge-update", {}).get("accuracy")

    def accuracy_delta(value: Any) -> float | None:
        if not isinstance(value, (int, float)) or not isinstance(overall_accuracy, (int, float)):
            return None
        return float(value) - float(overall_accuracy)

    scenario_findings = {
        "single_evidence_accuracy": single_accuracy,
        "multiple_evidence_accuracy": multiple_accuracy,
        "multiple_minus_single_accuracy": (
            float(multiple_accuracy) - float(single_accuracy)
            if isinstance(single_accuracy, (int, float)) and isinstance(multiple_accuracy, (int, float))
            else None
        ),
        "temporal_accuracy": temporal_accuracy,
        "temporal_minus_overall_accuracy": accuracy_delta(temporal_accuracy),
        "knowledge_update_accuracy": knowledge_update_accuracy,
        "knowledge_update_minus_overall_accuracy": accuracy_delta(knowledge_update_accuracy),
        "evidence_found_answer_accuracy": conditional_accuracy["evidence_found"]["accuracy"],
    }
    answer_cost = answer_summary.get("token_usage", {}).get("cost_usd", NOT_RECORDED)
    judge_cost = judge_summary.get("token_usage", {}).get("cost_usd", NOT_RECORDED)
    llm_cost = {
        "currency": "USD",
        "answer_cost_usd": answer_cost,
        "judge_cost_usd": judge_cost,
        "total_cost_usd": (
            float(answer_cost) + float(judge_cost)
            if isinstance(answer_cost, (int, float)) and isinstance(judge_cost, (int, float))
            else NOT_RECORDED
        ),
        "answer_pricing": answer_summary.get("pricing", NOT_RECORDED),
        "judge_pricing": judge_summary.get("pricing", NOT_RECORDED),
    }
    code_snapshot = run_config.get("eval_code_snapshot")
    if run_config.get("eval_code_dirty") is False:
        reproducibility_status = "PASS_CLEAN_COMMIT"
    elif isinstance(code_snapshot, dict) and code_snapshot.get("manifest_sha256"):
        reproducibility_status = "PASS_DIRTY_WITH_SOURCE_SNAPSHOT"
    else:
        reproducibility_status = "PARTIAL_DIRTY_WITHOUT_SOURCE_SNAPSHOT"
    manifest_source = manifest.get("source_dataset")
    manifest_dataset_name = (
        manifest_source.get("name", NOT_RECORDED)
        if isinstance(manifest_source, dict)
        else manifest_source or NOT_RECORDED
    )
    run_info = {
        "run_id": run_metadata.get("run_id", run_dir.name),
        "dataset_id": run_config.get("dataset_id", manifest.get("dataset_id", NOT_RECORDED)),
        "dataset_name": run_config.get("dataset_name", manifest_dataset_name),
        "dataset_version": run_config.get("dataset_version", manifest.get("dataset_id", NOT_RECORDED)),
        "source_dataset": run_config.get("source_dataset", NOT_RECORDED),
        "language": run_config.get("language", NOT_RECORDED),
        "translated": run_config.get("translated", NOT_RECORDED),
        "case_count": len(cases),
        "dataset_case_count": run_config.get("dataset_case_count", NOT_RECORDED),
        "session_count": run_config.get("selected_session_count", manifest.get("counts", {}).get("session_count", NOT_RECORDED)),
        "turn_count": run_config.get("selected_turn_count", manifest.get("counts", {}).get("turn_count", NOT_RECORDED)),
        "evidence_session_count": run_config.get("selected_evidence_session_count", manifest.get("counts", {}).get("evidence_session_count", NOT_RECORDED)),
        "memory_backend": run_config.get("memory_backend", NOT_RECORDED),
        "memory_version": run_config.get("memory_version", NOT_RECORDED),
        "top_k": top_k,
        "answer_model": answer_summary.get("model", NOT_RECORDED),
        "judge_model": judge_summary.get("model", NOT_RECORDED),
        "answer_prompt_version": answer_summary.get("prompt_version", NOT_RECORDED),
        "judge_prompt_version": judge_summary.get("prompt_version", NOT_RECORDED),
        "eval_code_commit": run_config.get("eval_code_commit", NOT_RECORDED),
        "eval_code_dirty": run_config.get("eval_code_dirty", NOT_RECORDED),
        "eval_code_snapshot": code_snapshot or NOT_RECORDED,
        "reproducibility_status": reproducibility_status,
        "start_time": run_config.get("start_time_utc", NOT_RECORDED),
        "end_time": judge_summary.get(
            "end_time_utc",
            answer_summary.get("end_time_utc", run_metadata.get("end_time_utc", NOT_RECORDED)),
        ),
    }
    indexed_chunks = retrieval_summary.get("indexed_chunk_count")
    added_sessions = retrieval_summary.get("added_sessions")
    average_chunks_per_session = retrieval_summary.get("average_chunks_per_session")
    if not isinstance(average_chunks_per_session, (int, float)):
        average_chunks_per_session = (
            float(indexed_chunks) / float(added_sessions)
            if isinstance(indexed_chunks, (int, float)) and isinstance(added_sessions, (int, float)) and added_sessions
            else NOT_RECORDED
        )
    embedding = retrieval_summary.get("embedding")
    if not isinstance(embedding, dict):
        embedding_enabled = bool(run_config.get("embedding_enabled"))
        embedding = {
            "enabled": embedding_enabled,
            "status": NOT_RECORDED if embedding_enabled else NOT_APPLICABLE,
            "call_count": NOT_RECORDED if embedding_enabled else 0,
            "failure_count": NOT_RECORDED if embedding_enabled else 0,
            "chunks_with_embedding": sum(
                int(case["add"]["chunks_with_embedding"])
                for case in cases
                if isinstance(case["add"]["chunks_with_embedding"], (int, float))
            ),
        }
    extraction = retrieval_summary.get("extraction")
    if not isinstance(extraction, dict):
        extraction = {
            "enabled": False,
            "status": NOT_APPLICABLE,
            "call_count": 0,
            "failure_count": 0,
        }
    processing_observability = {
        "indexed_document_count": retrieval_summary.get("indexed_document_count", NOT_RECORDED),
        "indexed_chunk_count": indexed_chunks if indexed_chunks is not None else NOT_RECORDED,
        "average_chunks_per_session": average_chunks_per_session,
        "embedding": embedding,
        "extraction": extraction,
    }
    observability_gaps = [
        "Provider-side prompt truncation is not exposed by the OpenAI-compatible endpoint; client-side truncation is recorded.",
        "Human Judge review remains a manual field and is not auto-filled.",
    ]
    if not isinstance(llm_cost["total_cost_usd"], (int, float)):
        observability_gaps.append(
            "LLM cost is NOT_RECORDED because no price table was configured; token usage is recorded."
        )
    if reproducibility_status == "PARTIAL_DIRTY_WITHOUT_SOURCE_SNAPSHOT":
        observability_gaps.append(
            "The run used a dirty working tree without an eval source snapshot, so the exact code cannot be reconstructed from the commit alone."
        )
    return {
        "run_dir": str(run_dir),
        "total_cases": len(cases),
        "successful_pipeline_cases": sum(case["final"]["pipeline_complete"] for case in cases),
        "failed_pipeline_cases": sum(not case["final"]["pipeline_complete"] for case in cases),
        "retrieval_scored_cases": len(retrieval_rows),
        "top_k": top_k,
        "hit_at_k": _mean(row["hit_at_k"] for row in retrieval_rows),
        "recall_at_k": _mean(row["recall_at_k"] for row in retrieval_rows),
        "mrr": _mean(row["mrr"] for row in retrieval_rows),
        "answer_accuracy": overall_accuracy,
        "answer_scored_cases": len(scored),
        "pipeline_success_rate": pipeline_success_rate,
        "grounded_end_to_end_accuracy": grounded_success_rate,
        "add_failure_count": root_counts["ADD_FAILURE"],
        "retrieval_failure_count": sum(root_counts[key] for key in ("RETRIEVAL_MISS", "RETRIEVAL_PARTIAL", "RETRIEVAL_LOW_RANK")),
        "answer_failure_count": root_counts["ANSWER_FAILURE"],
        "judge_suspect_count": root_counts["JUDGE_SUSPECT"],
        "judge_wrong_count": sum(case["judge"]["is_correct"] is False for case in cases),
        "quadrants": {
            "A_retrieval_pass_answer_pass": quadrant_counts["A: Retrieval PASS + Answer PASS"],
            "B_retrieval_pass_answer_fail": quadrant_counts["B: Retrieval PASS + Answer FAIL"],
            "C_retrieval_fail_answer_pass": quadrant_counts["C: Retrieval FAIL + Answer PASS"],
            "D_retrieval_fail_answer_fail": quadrant_counts["D: Retrieval FAIL + Answer FAIL"],
            "not_scored": sum(case["final"]["quadrant"] == NOT_RECORDED for case in cases),
        },
        "root_cause_distribution": {key: root_counts[key] for key in ROOT_CAUSES},
        "run_info": run_info,
        "retrieval_stage": retrieval_summary,
        "answer_stage": answer_summary,
        "judge_stage": judge_summary,
        "latency_breakdown": latency_breakdown,
        "question_type_breakdown": question_types,
        "evidence_count_breakdown": evidence_groups,
        "conditional_answer_accuracy": conditional_accuracy,
        "scenario_findings": scenario_findings,
        "dataset_integrity": dataset_validation or {"status": NOT_RECORDED},
        "processing_observability": processing_observability,
        "llm_cost": llm_cost,
        "api_stability": {
            "memory": retrieval_summary.get("api_stability", {}),
            "answer_api_requests": answer_summary.get("api_request_count", 0),
            "judge_api_requests": judge_summary.get("api_request_count", 0),
            "answer_retries": answer_summary.get("retry_count", 0),
            "judge_retries": judge_summary.get("retry_count", 0),
            "timeouts": answer_summary.get("timeout_count", 0) + judge_summary.get("timeout_count", 0),
            "api_error_count": len(api_errors),
        },
        "version_fixed_fields": {
            "dataset_version": run_info["dataset_version"],
            "case_selection": run_config.get("selected_case_ids", NOT_RECORDED),
            "top_k": top_k,
            "answer_model": run_info["answer_model"],
            "judge_model": run_info["judge_model"],
            "answer_prompt_version": run_info["answer_prompt_version"],
            "judge_prompt_version": run_info["judge_prompt_version"],
            "eval_code_commit": run_info["eval_code_commit"],
            "eval_code_snapshot_manifest_sha256": (
                code_snapshot.get("manifest_sha256") if isinstance(code_snapshot, dict) else NOT_RECORDED
            ),
            "reproducibility_status": reproducibility_status,
            "memory_config_sha256": run_config.get("reme_config_sha256", NOT_RECORDED),
            "memory_version": run_info["memory_version"],
        },
        "conclusions": {
            "memory_all_written": all(case["add"]["add_status"] == "PASS" for case in cases),
            "all_evidence_written": all(case["add"]["evidence_add_status"] == "PASS" for case in cases),
            "search_stable": retrieval_summary.get("search_success_rate") == 1.0,
            "recall_failure_count": root_counts["RETRIEVAL_MISS"] + root_counts["RETRIEVAL_PARTIAL"],
            "low_rank_failure_count": root_counts["RETRIEVAL_LOW_RANK"],
            "ranking_failure_count": root_counts["RETRIEVAL_LOW_RANK"],
            "wrong_chunk_failure_count": root_counts["RETRIEVAL_WRONG_CHUNK"],
            "context_loss_count": root_counts["CONTEXT_LOSS"] + root_counts["CONTEXT_TRUNCATION"],
            "judge_suspect_count": root_counts["JUDGE_SUSPECT"],
            "max_latency_stage": max_latency_stage,
            "largest_error_source": max(
                (key for key in ROOT_CAUSES if key != "PASS"),
                key=lambda key: root_counts[key],
            ),
            "reproducibility_status": reproducibility_status,
        },
        "observability_gaps": observability_gaps,
        "cases": [
            {
                "case_id": case["case"]["case_id"],
                "question_type": case["case"]["question_type"],
                "hit_at_k": case["retrieval"]["hit_at_k"],
                "recall_at_k": case["retrieval"]["recall_at_k"],
                "mrr": case["retrieval"]["mrr"],
                "best_evidence_score": case["retrieval"]["best_evidence_score"],
                "best_non_evidence_score": case["retrieval"]["best_non_evidence_score"],
                "first_evidence_rank": case["retrieval"]["first_evidence_rank"],
                "answer_correct": case["judge"]["is_correct"],
                "judge_label": case["judge"]["parsed_label"],
                "quadrant": case["final"]["quadrant"],
                "root_cause": case["final"]["root_cause"],
                "explanation": case["final"]["explanation"],
            }
            for case in cases
        ],
    }


def _build_comparison(current: dict[str, Any], baseline_run: Path) -> dict[str, Any]:
    baseline_summary_path = baseline_run / "trace" / "trace_summary.json"
    if not baseline_summary_path.is_file():
        raise FileNotFoundError(f"Baseline trace summary not found: {baseline_summary_path}")
    baseline = _read_json(baseline_summary_path)
    baseline_cases = {
        str(item.get("case_id", "")): item
        for item in baseline.get("cases", [])
        if isinstance(item, dict)
    }
    current_cases = {
        str(item.get("case_id", "")): item
        for item in current.get("cases", [])
        if isinstance(item, dict)
    }
    shared_ids = sorted(set(baseline_cases) & set(current_cases))
    fixed = [
        ident
        for ident in shared_ids
        if baseline_cases[ident].get("answer_correct") is False
        and current_cases[ident].get("answer_correct") is True
    ]
    regressed = [
        ident
        for ident in shared_ids
        if baseline_cases[ident].get("answer_correct") is True
        and current_cases[ident].get("answer_correct") is False
    ]
    baseline_retrieval = _read_jsonl(baseline_run / "retrieval.jsonl")
    baseline_add = _read_jsonl(baseline_run / "add_trace.jsonl")
    baseline_answers = _read_jsonl(baseline_run / "answers.jsonl")
    baseline_scores = _read_jsonl(baseline_run / "scores.jsonl")
    baseline_failure_count = sum(
        len(_read_jsonl(baseline_run / name))
        for name in ("failures.jsonl", "answer_failures.jsonl", "judge_failures.jsonl", "api_errors.jsonl")
    )
    baseline_search_p95 = _percentile((row.get("search_latency_ms") for row in baseline_retrieval), 0.95)
    baseline_add_p95 = _percentile((row.get("add_latency_ms") for row in baseline_add), 0.95)
    baseline_answer_p95 = _percentile((row.get("latency_ms") for row in baseline_answers), 0.95)
    baseline_judge_p95 = _percentile((row.get("latency_ms") for row in baseline_scores), 0.95)
    baseline_tokens = sum(
        int(row.get("usage", {}).get("total_tokens", 0))
        for row in [*baseline_answers, *baseline_scores]
    )
    current_tokens = int(current.get("answer_stage", {}).get("token_usage", {}).get("total_tokens", 0)) + int(
        current.get("judge_stage", {}).get("token_usage", {}).get("total_tokens", 0)
    )

    def rows_cost(rows: list[dict[str, Any]], summary_name: str) -> float | None:
        stage_summary = _read_json(baseline_run / summary_name) if (baseline_run / summary_name).is_file() else {}
        pricing = stage_summary.get("pricing") if isinstance(stage_summary, dict) else None
        if not isinstance(pricing, dict):
            model = stage_summary.get("model") if isinstance(stage_summary, dict) else None
            if not model and rows:
                model = rows[0].get("model")
            pricing = resolve_model_pricing(str(model or ""))
        usage = summarize_token_usage(
            [row.get("usage", {}) for row in rows if isinstance(row.get("usage"), dict)],
            pricing,
        )
        cost = usage.get("cost_usd")
        return float(cost) if isinstance(cost, (int, float)) else None

    baseline_answer_cost = rows_cost(baseline_answers, "answer_summary.json")
    baseline_judge_cost = rows_cost(baseline_scores, "judge_summary.json")
    baseline_cost = (
        baseline_answer_cost + baseline_judge_cost
        if baseline_answer_cost is not None and baseline_judge_cost is not None
        else None
    )
    current_cost_value = current.get("llm_cost", {}).get("total_cost_usd")
    current_cost = float(current_cost_value) if isinstance(current_cost_value, (int, float)) else None

    def delta(current_value: Any, baseline_value: Any) -> float | None:
        if not isinstance(current_value, (int, float)) or not isinstance(baseline_value, (int, float)):
            return None
        return float(current_value) - float(baseline_value)

    baseline_roots = baseline.get("root_cause_distribution", {})
    return {
        "baseline_run": str(baseline_run),
        "shared_case_count": len(shared_ids),
        "metric_deltas": {
            f"hit_at_{current['top_k']}": delta(current.get("hit_at_k"), baseline.get("hit_at_k")),
            f"recall_at_{current['top_k']}": delta(current.get("recall_at_k"), baseline.get("recall_at_k")),
            "mrr": delta(current.get("mrr"), baseline.get("mrr")),
            "accuracy": delta(current.get("answer_accuracy"), baseline.get("answer_accuracy")),
            "add_p95_ms": delta(current["latency_breakdown"]["Add"]["p95"], baseline_add_p95),
            "search_p95_ms": delta(current["latency_breakdown"]["Search"]["p95"], baseline_search_p95),
            "answer_p95_ms": delta(current["latency_breakdown"]["Answer"]["p95"], baseline_answer_p95),
            "judge_p95_ms": delta(current["latency_breakdown"]["Judge"]["p95"], baseline_judge_p95),
            "error_rate": delta(
                current["api_stability"]["api_error_count"] / current["total_cases"] if current["total_cases"] else None,
                baseline_failure_count / len(baseline_cases) if baseline_cases else None,
            ),
            "total_tokens": current_tokens - baseline_tokens,
            "cost": delta(current_cost, baseline_cost),
            "cost_usd": delta(current_cost, baseline_cost),
        },
        "root_cause_deltas": {
            key: int(current["root_cause_distribution"].get(key, 0)) - int(baseline_roots.get(key, 0))
            for key in ROOT_CAUSES
        },
        "newly_fixed_cases": fixed,
        "newly_failed_cases": regressed,
        "comparison_notes": [
            "Root-cause labels added in v2 have no exact v1 counterpart and should be read with the per-case list."
        ],
    }


def _render_summary(summary: dict[str, Any]) -> str:
    q = summary["quadrants"]
    root = summary["root_cause_distribution"]
    root_descriptions = {
        "PASS": "检索、上下文传递和最终回答均通过",
        "DATA_ERROR": "数据集字段或 Evidence 引用不完整",
        "ADD_FAILURE": "Evidence 未正确进入 Memory 输入",
        "INDEX_FAILURE": "Memory 索引阶段失败",
        "RETRIEVAL_MISS": "TopK 和候选结果中均未找到 Evidence",
        "RETRIEVAL_PARTIAL": "只找到了部分 Evidence",
        "RETRIEVAL_LOW_RANK": "找到了 Evidence，但排名低于 TopK",
        "RETRIEVAL_WRONG_CHUNK": "命中 session，但返回片段不含标注 Evidence",
        "CONTEXT_LOSS": "Evidence 内容在检索返回或 Answer 上下文中丢失",
        "CONTEXT_TRUNCATION": "Answer 输入在客户端发生截断",
        "ANSWER_FAILURE": "Evidence 已到达 Answer 阶段，但生成失败或答案错误",
        "JUDGE_SUSPECT": "Judge 失败或判分结果存在疑点，需要人工复核",
        "API_FAILURE": "Memory 或 LLM API 请求失败",
        "TIMEOUT": "某个 API 阶段超时",
        "PIPELINE_FAILURE": "链路产物缺失，无法完成该 case 的评测",
    }
    gap_translations = {
        "Provider-side prompt truncation is not exposed by the OpenAI-compatible endpoint; client-side truncation is recorded.":
            "OpenAI-compatible 接口没有暴露服务端 Prompt 截断状态；当前已记录客户端是否截断。",
        "Human Judge review remains a manual field and is not auto-filled.":
            "人工 Judge 复核仍需手工填写，框架不会自动伪造人工结论。",
        "LLM cost is NOT_RECORDED because no price table was configured; token usage is recorded.":
            "尚未配置模型价格表，因此 Cost 为 NOT_RECORDED；Token Usage 已完整记录。",
        "The run used a dirty working tree without an eval source snapshot, so the exact code cannot be reconstructed from the commit alone.":
            "本次运行使用了 dirty 工作区且没有源码快照；仅凭 Git commit 无法严格还原当时运行代码。",
    }
    non_pass = [(key, root[key]) for key in ROOT_CAUSES if key != "PASS" and root[key] > 0]
    interpretation = [
        f"- 本次共评测 **{summary['total_cases']}** 条 case，其中 **{summary['successful_pipeline_cases']}** 条生成了完整的 Retrieval、Answer 和 Judge 产物，**{summary['failed_pipeline_cases']}** 条链路不完整。",
        f"- Retrieval 实际计分 **{summary['retrieval_scored_cases']}** 条，Hit@{summary['top_k']} 为 **{_pct(summary['hit_at_k'])}**，Recall@{summary['top_k']} 为 **{_pct(summary['recall_at_k'])}**，MRR 为 **{_display(summary['mrr'])}**。",
        f"- Answer/Judge 实际计分 **{summary['answer_scored_cases']}** 条，答案准确率为 **{_pct(summary['answer_accuracy'])}**。",
    ]
    if non_pass:
        largest = max(count for _, count in non_pass)
        main_causes = "、".join(f"`{key}`（{count} 条）" for key, count in non_pass if count == largest)
        interpretation.append(f"- 当前数量最多的失败根因是 {main_causes}；应优先打开对应 case Trace，从上游向下排查。")
    else:
        interpretation.append(
            f"- 本次所选 **{summary['total_cases']}** 条 case 未发现失败根因；这只代表当前 run 的样本，不代表未运行的 case 已经通过。"
        )
    if q["C_retrieval_fail_answer_pass"]:
        interpretation.append(
            f"- 有 **{q['C_retrieval_fail_answer_pass']}** 条属于 C 象限：虽然答案判对，但 Retrieval 未通过，可能是模型猜对或利用了非 Evidence 信息，不能视为 Memory 成功。"
        )
    run_info = summary["run_info"]
    latency = summary["latency_breakdown"]
    api = summary["api_stability"]
    conclusions = summary["conclusions"]
    integrity = summary["dataset_integrity"]
    integrity_counts = integrity.get("counts", {}) if isinstance(integrity, dict) else {}
    processing = summary["processing_observability"]
    llm_cost = summary["llm_cost"]
    conditional = summary["conditional_answer_accuracy"]
    scenarios = summary["scenario_findings"]
    code_snapshot = run_info.get("eval_code_snapshot")
    code_snapshot_hash = (
        code_snapshot.get("manifest_sha256", NOT_RECORDED)
        if isinstance(code_snapshot, dict)
        else NOT_RECORDED
    )
    type_hit_key = f"hit_at_{summary['top_k']}"
    type_recall_key = f"recall_at_{summary['top_k']}"
    lines = [
        "# Trace 汇总报告",
        "",
        f"> 评测目录：`{summary['run_dir']}`  ",
        "> 排查原则：始终沿真实链路从上游向下检查——Add → Retrieval → Context → Answer → Judge。",
        "",
        "## Run 基础信息",
        "",
        "| 字段 | 值 |",
        "| --- | --- |",
        f"| Run ID | `{_markdown(run_info['run_id'])}` |",
        f"| Dataset | {_markdown(run_info['dataset_name'])} / `{_markdown(run_info['dataset_version'])}` |",
        f"| Case / Session / Turn / Evidence Session | {run_info['case_count']} / {run_info['session_count']} / {run_info['turn_count']} / {run_info['evidence_session_count']} |",
        f"| Memory | {_markdown(run_info['memory_backend'])} `{_markdown(run_info['memory_version'])}` |",
        f"| TopK | {run_info['top_k']} |",
        f"| Answer / Judge Model | `{_markdown(run_info['answer_model'])}` / `{_markdown(run_info['judge_model'])}` |",
        f"| Prompt Version | `{_markdown(run_info['answer_prompt_version'])}` / `{_markdown(run_info['judge_prompt_version'])}` |",
        f"| Eval Commit | `{_markdown(run_info['eval_code_commit'])}`（dirty={_markdown(run_info['eval_code_dirty'])}） |",
        f"| Eval Code Snapshot | `{_markdown(code_snapshot_hash)}` |",
        f"| Reproducibility | `{_markdown(run_info['reproducibility_status'])}` |",
        f"| Start / End | {_markdown(run_info['start_time'])} / {_markdown(run_info['end_time'])} |",
        "",
        "## Dataset 完整性",
        "",
        f"- Run 选中数据验收状态：**{_markdown(integrity.get('status', NOT_RECORDED))}**；源数据验收状态：**{_markdown(integrity.get('source_integrity', {}).get('status', NOT_RECORDED))}**。",
        "",
        "| 指标 | 数量 |",
        "| --- | ---: |",
        f"| 实际加载 Case / Session / Turn / Evidence Session | {_display(integrity_counts.get('actual_loaded_case_count'))} / {_display(integrity_counts.get('actual_loaded_session_count'))} / {_display(integrity_counts.get('actual_loaded_turn_count'))} / {_display(integrity_counts.get('evidence_session_count'))} |",
        f"| 缺失 Question / Gold Answer / Evidence ID | {_display(integrity_counts.get('missing_question_count'))} / {_display(integrity_counts.get('missing_gold_answer_count'))} / {_display(integrity_counts.get('missing_evidence_id_count'))} |",
        f"| 重复 Session ID / Case ID | {_display(integrity_counts.get('duplicate_session_id_count'))} / {_display(integrity_counts.get('duplicate_case_id_count'))} |",
        f"| 时间戳异常 / 解析失败 / 跳过 | {_display(integrity_counts.get('timestamp_anomaly_count'))} / {_display(integrity_counts.get('data_parse_failure_count'))} / {_display(integrity_counts.get('data_skipped_count'))} |",
        "",
        "## 本次结果解读",
        "",
        *interpretation,
        "",
        "## 总览",
        "",
        "| 指标 | 结果 |",
        "| --- | ---: |",
        f"| Case 总数 | {summary['total_cases']} |",
        f"| 完整生成 Retrieval、Answer、Judge 产物 | {summary['successful_pipeline_cases']} |",
        f"| 链路产物不完整 | {summary['failed_pipeline_cases']} |",
        f"| Retrieval 实际计分数 | {summary['retrieval_scored_cases']} |",
        f"| Hit@{summary['top_k']} | {_pct(summary['hit_at_k'])} |",
        f"| Recall@{summary['top_k']} | {_pct(summary['recall_at_k'])} |",
        f"| MRR | {_display(summary['mrr'])} |",
        f"| Answer 准确率 | {_pct(summary['answer_accuracy'])}（{summary['answer_scored_cases']} 条已计分） |",
        f"| Pipeline Success Rate | {_pct(summary['pipeline_success_rate'])} |",
        f"| 严格端到端成功率（Retrieval PASS 且 Answer PASS） | {_pct(summary['grounded_end_to_end_accuracy'])} |",
        f"| Add 失败 | {summary['add_failure_count']} |",
        f"| Retrieval 失败 | {summary['retrieval_failure_count']} |",
        f"| Answer 失败 | {summary['answer_failure_count']} |",
        f"| Judge 可疑 | {summary['judge_suspect_count']} |",
        "",
        "## 延迟与 API 稳定性",
        "",
        "| 阶段 | Avg ms | P50 ms | P95 ms | P99 ms |",
        "| --- | ---: | ---: | ---: | ---: |",
        *[
            f"| {stage} | {_display(values['avg'], 1)} | {_display(values['p50'], 1)} | {_display(values['p95'], 1)} | {_display(values['p99'], 1)} |"
            for stage, values in latency.items()
        ],
        "",
        "- End-to-End 为每条 Case 的 Add + Index + Search + Answer + Judge 记录耗时之和，不包含服务启动、关闭和编排开销。",
        f"- Memory API：Index 请求 {api['memory'].get('memory_index_requests', NOT_RECORDED)}，Search 请求 {api['memory'].get('memory_search_requests', NOT_RECORDED)}，HTTP 2xx {api['memory'].get('http_2xx', NOT_RECORDED)}。",
        f"- LLM API：Answer 请求 {api['answer_api_requests']}，Judge 请求 {api['judge_api_requests']}，重试 {api['answer_retries'] + api['judge_retries']}，超时 {api['timeouts']}，错误 {api['api_error_count']}。",
        "",
        "## Index / Memory Processing",
        "",
        "| 指标 | 结果 |",
        "| --- | --- |",
        f"| Indexed Documents / Chunks | {_display(processing['indexed_document_count'])} / {_display(processing['indexed_chunk_count'])} |",
        f"| Average Chunks / Session | {_display(processing['average_chunks_per_session'])} |",
        f"| Embedding | enabled={_display(processing['embedding'].get('enabled'))}; status={_display(processing['embedding'].get('status'))}; calls={_display(processing['embedding'].get('call_count'))}; failures={_display(processing['embedding'].get('failure_count'))}; chunks={_display(processing['embedding'].get('chunks_with_embedding'))} |",
        f"| Extraction | enabled={_display(processing['extraction'].get('enabled'))}; status={_display(processing['extraction'].get('status'))}; calls={_display(processing['extraction'].get('call_count'))}; failures={_display(processing['extraction'].get('failure_count'))} |",
        "",
        "## LLM Token 与 Cost",
        "",
        "| 阶段 | Input Tokens | Cache Hit | Cache Miss | Output Tokens | Cost USD |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
        f"| Answer | {_display(summary['answer_stage'].get('token_usage', {}).get('input_tokens'))} | {_display(summary['answer_stage'].get('token_usage', {}).get('cache_hit_input_tokens'))} | {_display(summary['answer_stage'].get('token_usage', {}).get('cache_miss_input_tokens'))} | {_display(summary['answer_stage'].get('token_usage', {}).get('output_tokens'))} | {_display(llm_cost['answer_cost_usd'], 8)} |",
        f"| Judge | {_display(summary['judge_stage'].get('token_usage', {}).get('input_tokens'))} | {_display(summary['judge_stage'].get('token_usage', {}).get('cache_hit_input_tokens'))} | {_display(summary['judge_stage'].get('token_usage', {}).get('cache_miss_input_tokens'))} | {_display(summary['judge_stage'].get('token_usage', {}).get('output_tokens'))} | {_display(llm_cost['judge_cost_usd'], 8)} |",
        f"| Total | - | - | - | - | {_display(llm_cost['total_cost_usd'], 8)} |",
        "",
        "- Cost 按 Runner 保存的价格表计算；旧产物没有价格表时按报告构建时匹配的内置价格表回算。缓存未分类的 Input Token 按 Cache Miss 计费。",
        f"- Answer Pricing（USD / 1M tokens）：hit={_display(llm_cost['answer_pricing'].get('cache_hit_input') if isinstance(llm_cost['answer_pricing'], dict) else None)}，miss={_display(llm_cost['answer_pricing'].get('cache_miss_input') if isinstance(llm_cost['answer_pricing'], dict) else None)}，output={_display(llm_cost['answer_pricing'].get('output') if isinstance(llm_cost['answer_pricing'], dict) else None)}，multiplier={_display(llm_cost['answer_pricing'].get('multiplier') if isinstance(llm_cost['answer_pricing'], dict) else None)}。",
        f"- Judge Pricing（USD / 1M tokens）：hit={_display(llm_cost['judge_pricing'].get('cache_hit_input') if isinstance(llm_cost['judge_pricing'], dict) else None)}，miss={_display(llm_cost['judge_pricing'].get('cache_miss_input') if isinstance(llm_cost['judge_pricing'], dict) else None)}，output={_display(llm_cost['judge_pricing'].get('output') if isinstance(llm_cost['judge_pricing'], dict) else None)}，multiplier={_display(llm_cost['judge_pricing'].get('multiplier') if isinstance(llm_cost['judge_pricing'], dict) else None)}。",
        f"- Pricing Source：Answer={_markdown(llm_cost['answer_pricing'].get('source', NOT_RECORDED) if isinstance(llm_cost['answer_pricing'], dict) else NOT_RECORDED)}；Judge={_markdown(llm_cost['judge_pricing'].get('source', NOT_RECORDED) if isinstance(llm_cost['judge_pricing'], dict) else NOT_RECORDED)}。",
        "",
        "## 按 Question Type 拆分",
        "",
        f"| Question Type | Cases | Hit@{summary['top_k']} | Recall@{summary['top_k']} | MRR | Accuracy | Search Avg ms |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
        *[
            f"| {_markdown(question_type)} | {values['case_count']} | {_pct(values[type_hit_key])} | {_pct(values[type_recall_key])} | {_display(values['mrr'])} | {_pct(values['accuracy'])} | {_display(values['avg_search_latency_ms'], 1)} |"
            for question_type, values in summary["question_type_breakdown"].items()
        ],
        "",
        "## Retrieval 条件下的 Answer Accuracy",
        "",
        "| 条件 | Cases | Correct | Accuracy |",
        "| --- | ---: | ---: | ---: |",
        *[
            f"| {label} | {values['case_count']} | {values['correct_count']} | {NOT_APPLICABLE if values['case_count'] == 0 else _pct(values['accuracy'])} |"
            for label, values in conditional.items()
        ],
        "",
        "## 重点场景结论",
        "",
        f"- 单 Evidence Accuracy：**{_pct(scenarios['single_evidence_accuracy'])}**；多 Evidence Accuracy：**{_pct(scenarios['multiple_evidence_accuracy'])}**；差值（多 - 单）：**{_pp(scenarios['multiple_minus_single_accuracy'])}**。",
        f"- Temporal Accuracy：**{_pct(scenarios['temporal_accuracy'])}**，相对总体差值：**{_pp(scenarios['temporal_minus_overall_accuracy'])}**。",
        f"- Knowledge Update Accuracy：**{_pct(scenarios['knowledge_update_accuracy'])}**，相对总体差值：**{_pp(scenarios['knowledge_update_minus_overall_accuracy'])}**。",
        f"- 至少找到部分 Evidence 后的 Answer Accuracy：**{_pct(scenarios['evidence_found_answer_accuracy'])}**。",
        "- 样本量只有 20 条，各场景差值用于定位信号，不作为统计显著性结论。",
        "",
        "## Retrieval × Answer 四象限",
        "",
        "| 分类 | 数量 | 如何理解 |",
        "| --- | ---: | --- |",
        f"| A：Retrieval ✓ + Answer ✓ | {q['A_retrieval_pass_answer_pass']} | 正常成功，Memory 找对且最终答对 |",
        f"| B：Retrieval ✓ + Answer ✗ | {q['B_retrieval_pass_answer_fail']} | 排查上下文丢失、Answer 推理或 Judge |",
        f"| C：Retrieval ✗ + Answer ✓ | {q['C_retrieval_fail_answer_pass']} | 可能依靠模型先验猜对，不能证明 Memory 有效 |",
        f"| D：Retrieval ✗ + Answer ✗ | {q['D_retrieval_fail_answer_fail']} | 优先排查检索召回和排序 |",
        f"| 未计分 | {q['not_scored']} | Answer/Judge 产物不完整 |",
        "",
        "## 主要根因分布",
        "",
        "| 根因标签 | 数量 | 含义 |",
        "| --- | ---: | --- |",
    ]
    for key in ROOT_CAUSES:
        lines.append(f"| `{key}` | {root[key]} | {root_descriptions[key]} |")
    lines.extend(
        [
            "",
            "## 进一步排查入口",
            "",
            "- [按失败优先级排列的 Case 索引](trace_index.md)",
            "- [Judge 人工复核队列](judge_review.md)",
            "- 机器可读汇总：`trace_summary.json`",
            "",
            "## 开发侧结论",
            "",
            f"- Memory 是否全部成功写入：**{'是' if conclusions['memory_all_written'] else '否'}**。",
            f"- Evidence 是否全部写入：**{'是' if conclusions['all_evidence_written'] else '否'}**。",
            f"- Search 是否稳定完成：**{'是' if conclusions['search_stable'] else '否'}**。",
            f"- Retrieval Miss/Partial {conclusions['recall_failure_count']} 条，Low-rank {conclusions['low_rank_failure_count']} 条，Wrong-chunk {conclusions['wrong_chunk_failure_count']} 条。",
            f"- Context Loss/Truncation 共 {conclusions['context_loss_count']} 条；Judge Suspect 共 {conclusions['judge_suspect_count']} 条。",
            f"- 平均耗时最大的阶段：**{conclusions['max_latency_stage']}**；数量最大的失败根因：**{conclusions['largest_error_source']}**。",
            f"- 多 Evidence 相比单 Evidence：**{_pp(scenarios['multiple_minus_single_accuracy'])}**；Temporal 相比总体：**{_pp(scenarios['temporal_minus_overall_accuracy'])}**；Knowledge Update 相比总体：**{_pp(scenarios['knowledge_update_minus_overall_accuracy'])}**。",
            f"- Evidence 找到后的 Answer Accuracy：**{_pct(scenarios['evidence_found_answer_accuracy'])}**。",
            "- 是否存在 Judge 误判：**尚不能确认**；自动可疑检测为 0，但没有人工复核标签，不能据此证明 Judge 无误判。",
            f"- 代码可复现状态：**{_markdown(conclusions['reproducibility_status'])}**。",
            "- 本 run 已冻结 Dataset、Case Selection、TopK、模型、Prompt、Memory Config Hash 与 Memory Version；Eval Code 是否可严格复现以上一条状态为准。",
        ]
    )
    comparison = summary.get("comparison")
    if isinstance(comparison, dict):
        deltas = comparison["metric_deltas"]
        hit_delta_key = f"hit_at_{summary['top_k']}"
        recall_delta_key = f"recall_at_{summary['top_k']}"
        accuracy_delta_text = (
            f"{deltas['accuracy'] * 100:+.1f} pp" if deltas["accuracy"] is not None else NOT_RECORDED
        )
        case_regression_text = (
            "无 Case 级准确率退化"
            if not comparison["newly_failed_cases"]
            else f"{len(comparison['newly_failed_cases'])} 条 case 退化"
        )
        lines.extend(
            [
                "",
                "## 与基线版本对比",
                "",
                f"> 基线：`{_markdown(comparison['baseline_run'])}`；共同 Case：{comparison['shared_case_count']}。",
                "",
                "| 指标 | Delta（当前 - 基线） |",
                "| --- | ---: |",
                f"| Hit@{summary['top_k']} | {_display(deltas[hit_delta_key])} |",
                f"| Recall@{summary['top_k']} | {_display(deltas[recall_delta_key])} |",
                f"| MRR | {_display(deltas['mrr'])} |",
                f"| Accuracy | {accuracy_delta_text} |",
                f"| Add P95 ms | {_display(deltas['add_p95_ms'], 1)} |",
                f"| Search P95 ms | {_display(deltas['search_p95_ms'], 1)} |",
                f"| Answer P95 ms | {_display(deltas['answer_p95_ms'], 1)} |",
                f"| Judge P95 ms | {_display(deltas['judge_p95_ms'], 1)} |",
                f"| Total Tokens | {deltas['total_tokens']:+d} |",
                f"| LLM Cost USD | {_display(deltas['cost_usd'], 8)} |",
                "",
                f"- Newly Fixed Cases：{_markdown(', '.join(comparison['newly_fixed_cases']) or '无')}。",
                f"- Newly Failed Cases：{_markdown(', '.join(comparison['newly_failed_cases']) or '无')}。",
                f"- 相对上一版的主要改善：Accuracy {accuracy_delta_text}，修复 {len(comparison['newly_fixed_cases'])} 条 case。",
                f"- 相对上一版的已知退化：{case_regression_text}；Judge P95 变化 {_display(deltas['judge_p95_ms'], 1)} ms。",
                "- 注意：v2 新增了更细的 Root Cause 标签，Root Cause Delta 应结合 per-case Trace 解读。",
            ]
        )
    lines.extend(["", "## 下一版 Runner 需要补充的可观测字段", ""])
    lines.extend(f"- {gap_translations.get(gap, gap)}" for gap in summary["observability_gaps"])
    lines.append("")
    return "\n".join(lines)


def build_trace_report(
    run_dir: str | Path,
    dataset_path: str | Path | None = None,
    baseline_run: str | Path | None = None,
) -> dict[str, Any]:
    run_dir = Path(run_dir).resolve()
    if not run_dir.is_dir():
        raise FileNotFoundError(f"Run directory not found: {run_dir}")
    run_config = _read_json(run_dir / "run_config.json") if (run_dir / "run_config.json").is_file() else {}
    if dataset_path is None:
        dataset_value = run_config.get("dataset", run_config.get("dataset_path"))
        dataset_path = Path(str(dataset_value)) if dataset_value else None
    else:
        dataset_path = Path(dataset_path)
    dataset_cases, dataset_metadata = _load_dataset(dataset_path.resolve() if dataset_path else None)

    prepared_rows = _read_jsonl(run_dir / "prepared.jsonl")
    retrieval_rows = _read_jsonl(run_dir / "retrieval.jsonl")
    answer_rows = _read_jsonl(run_dir / "answers.jsonl")
    score_rows = _read_jsonl(run_dir / "scores.jsonl")
    add_rows = _read_jsonl(run_dir / "add_trace.jsonl")
    retrieval_failures = _index_rows(_read_jsonl(run_dir / "failures.jsonl"))
    answer_failures = _index_rows(_read_jsonl(run_dir / "answer_failures.jsonl"))
    judge_failures = _index_rows(_read_jsonl(run_dir / "judge_failures.jsonl"))
    prepared = _index_rows(prepared_rows)
    retrieval = _index_rows(retrieval_rows)
    answers = _index_rows(answer_rows)
    scores = _index_rows(score_rows)
    adds = _index_rows(add_rows)

    ordered_ids: list[str] = []
    for rows in (add_rows, retrieval_rows, prepared_rows, answer_rows, score_rows):
        for row in rows:
            ident = _row_id(row)
            if ident and ident not in ordered_ids:
                ordered_ids.append(ident)
    for mapping in (retrieval_failures, answer_failures, judge_failures):
        for ident in mapping:
            if ident not in ordered_ids:
                ordered_ids.append(ident)
    if not ordered_ids:
        raise ValueError(f"No case artifacts found in {run_dir}")

    top_k = int(run_config.get("top_k") or 10)
    cases = [
        _case_analysis(
            ident=ident,
            run_dir=run_dir,
            dataset_case=dataset_cases.get(ident),
            prepared=prepared.get(ident),
            retrieval=retrieval.get(ident),
            answer=answers.get(ident),
            score=scores.get(ident),
            add_trace=adds.get(ident),
            retrieval_failure=retrieval_failures.get(ident),
            answer_failure=answer_failures.get(ident),
            judge_failure=judge_failures.get(ident),
            top_k=top_k,
        )
        for ident in ordered_ids
    ]
    trace_dir = run_dir / "trace"
    case_dir = trace_dir / "cases"
    case_dir.mkdir(parents=True, exist_ok=True)
    for case in cases:
        case_name = _safe_name(case["case"]["case_id"])
        (case_dir / f"{case_name}.md").write_text(_render_case(case), encoding="utf-8")
        (case_dir / f"{case_name}.json").write_text(
            json.dumps(case, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    if dataset_path is not None and Path(dataset_path).is_file():
        selected_dataset_cases = [dataset_cases[ident] for ident in ordered_ids if ident in dataset_cases]
        freeze_dataset_integrity(
            Path(dataset_path).resolve(),
            run_dir,
            selected_dataset_cases,
            source_case_count=len(dataset_cases),
        )
    summary = _summary(cases, run_dir, top_k)
    summary["dataset"] = str(dataset_path.resolve()) if dataset_path else NOT_RECORDED
    summary["dataset_id"] = run_config.get(
        "dataset_id", dataset_metadata.get("dataset_id", NOT_RECORDED)
    )
    summary["dataset_name"] = run_config.get(
        "dataset_name", summary.get("run_info", {}).get("dataset_name", NOT_RECORDED)
    )
    summary["dataset_version"] = run_config.get(
        "dataset_version", summary.get("run_info", {}).get("dataset_version", NOT_RECORDED)
    )
    summary["source_dataset"] = run_config.get("source_dataset", NOT_RECORDED)
    summary["language"] = run_config.get("language", NOT_RECORDED)
    summary["translated"] = run_config.get("translated", NOT_RECORDED)
    summary["case_count"] = len(cases)
    if baseline_run is not None:
        summary["comparison"] = _build_comparison(summary, Path(baseline_run).resolve())
    (trace_dir / "trace_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (trace_dir / "trace_summary.md").write_text(_render_summary(summary), encoding="utf-8")
    (trace_dir / "trace_index.md").write_text(_render_index(cases), encoding="utf-8")
    (trace_dir / "judge_review.md").write_text(_render_judge_review(cases), encoding="utf-8")
    return summary
