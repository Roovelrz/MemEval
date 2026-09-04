"""Stage-23 audit for a frozen MemEval benchmark release."""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

from .release import DIMENSION_DIRECTORIES, ReviewedBenchmark, ReviewedCaseArtifact


# The development document described the pre-deduplication target of 300 Cases.
# The frozen v0.1 intentionally removed one overlapping Case from D01 and D02.
EXPECTED_CASE_COUNTS = {
    "D01": 37,
    "D02": 37,
    "D03": 38,
    "D04": 38,
    "D05": 37,
    "D06": 37,
    "D07": 37,
    "D08": 37,
}

EXPECTED_PAYLOAD_TYPES = {
    "D01": "write",
    "D02": "retrieval",
    "D03": "temporal",
    "D04": "activation",
    "D05": "profile",
    "D06": "conflict",
    "D07": "scale",
    "D08": "privacy",
}


@dataclass(frozen=True)
class ContextFacts:
    event_ids: frozenset[str]
    session_ids: frozenset[str]
    memory_ids: frozenset[str]
    memory_orders: dict[str, int]
    deletion_orders: dict[str, int]
    event_count: int
    event_start: str | None
    event_end: str | None
    metadata_text: str
    content_text: str | None
    sha256: str


@dataclass
class BenchmarkAuditReport:
    case_counts: dict[str, int] = field(default_factory=dict)
    review_counts: dict[str, dict[str, int]] = field(default_factory=dict)
    context_count: int = 0
    checked_hash_count: int = 0
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def total_cases(self) -> int:
        return sum(self.case_counts.values())

    @property
    def ok(self) -> bool:
        return not self.errors

    def raise_for_errors(self) -> None:
        if self.errors:
            raise ValueError("Benchmark audit failed:\n- " + "\n- ".join(self.errors))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _json_text(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _normalise_text(value: Any) -> str:
    return " ".join(str(value).casefold().split())


def _iter_context_events(path: Path) -> tuple[list[dict[str, Any]], str]:
    digest = hashlib.sha256()
    if path.suffix.casefold() == ".jsonl":
        events: list[dict[str, Any]] = []
        with path.open("rb") as handle:
            for raw_line in handle:
                digest.update(raw_line)
                if raw_line.strip():
                    events.append(json.loads(raw_line))
        return events, digest.hexdigest()

    raw = path.read_bytes()
    digest.update(raw)
    document = json.loads(raw)
    events = document.get("events")
    if not isinstance(events, list):
        raise ValueError(f"Context {path} has no events list")
    return events, digest.hexdigest()


def _load_context_facts(path: Path, *, collect_content: bool) -> ContextFacts:
    events, sha256 = _iter_context_events(path)
    event_ids: list[str] = []
    session_ids: set[str] = set()
    memory_ids: set[str] = set()
    memory_orders: dict[str, int] = {}
    deletion_orders: dict[str, int] = {}
    metadata_values: list[Any] = []
    content_values: list[str] = []

    for fallback_order, event in enumerate(events):
        event_id = str(event.get("event_id", "")).strip()
        if event_id:
            event_ids.append(event_id)
        session_id = str(event.get("session_id", "")).strip()
        if session_id:
            session_ids.add(session_id)
        order_value = event.get("order", fallback_order)
        order = int(order_value) if isinstance(order_value, (int, float)) else fallback_order
        metadata = event.get("metadata", {})
        if not isinstance(metadata, dict):
            metadata = {}
        metadata_values.append(metadata)
        memory_id = str(metadata.get("memory_id", "")).strip()
        if memory_id:
            memory_ids.add(memory_id)
            memory_orders[memory_id] = min(order, memory_orders.get(memory_id, order))
        target_memory_id = str(metadata.get("target_memory_id", "")).strip()
        if target_memory_id and metadata.get("operation") == "delete":
            deletion_orders[target_memory_id] = min(order, deletion_orders.get(target_memory_id, order))
        if collect_content:
            content_values.append(str(event.get("content", "")))

    return ContextFacts(
        event_ids=frozenset(event_ids),
        session_ids=frozenset(session_ids),
        memory_ids=frozenset(memory_ids),
        memory_orders=memory_orders,
        deletion_orders=deletion_orders,
        event_count=len(events),
        event_start=event_ids[0] if event_ids else None,
        event_end=event_ids[-1] if event_ids else None,
        metadata_text=_json_text(metadata_values).casefold(),
        content_text="\n".join(content_values) if collect_content else None,
        sha256=sha256,
    )


def _add_missing_ids(
    report: BenchmarkAuditReport,
    artifact: ReviewedCaseArtifact,
    label: str,
    identifiers: Iterable[Any],
    available: frozenset[str],
) -> None:
    missing = sorted({str(value) for value in identifiers if str(value)} - set(available))
    if missing:
        report.errors.append(
            f"{artifact.dimension_id}/{artifact.case_path.name}: {label} cannot be resolved: {missing[:5]}"
        )


def _answer_values(dimension_id: str, payload: dict[str, Any]) -> list[str]:
    if dimension_id in {"D02", "D03", "D05", "D06", "D07"}:
        value = payload.get("gold_answer")
        return [str(value)] if value is not None else []
    return []


def _audit_case_references(
    report: BenchmarkAuditReport,
    artifact: ReviewedCaseArtifact,
    facts: ContextFacts,
) -> None:
    case = artifact.case
    envelope = case["envelope"]
    payload = case["gold"]["payload"]
    dimension_id = artifact.dimension_id

    if dimension_id == "D01":
        ids = list(payload.get("scored_event_ids", [])) + list(payload.get("non_memory_event_ids", []))
        for memory in payload.get("gold_memories", []):
            ids.extend(memory.get("evidence_event_ids", []))
        _add_missing_ids(report, artifact, "D01 Evidence ID", ids, facts.event_ids)
    elif dimension_id == "D02":
        _add_missing_ids(
            report,
            artifact,
            "D02 Evidence session ID",
            payload.get("gold_evidence_ids", []),
            facts.session_ids,
        )
    elif dimension_id == "D03":
        ids = list(payload.get("evidence_event_ids", []))
        for relation in payload.get("temporal_relations", []):
            ids.extend(
                value
                for key in ("evidence_event_id", "forget_event_id", "deletion_event_id")
                if (value := relation.get(key))
            )
        _add_missing_ids(report, artifact, "D03 Evidence ID", ids, facts.event_ids)
    elif dimension_id == "D04":
        _add_missing_ids(
            report, artifact, "D04 required memory ID", payload.get("required_memory_ids", []), facts.event_ids
        )
    elif dimension_id == "D05":
        ids = [
            evidence_id
            for item in payload.get("profile_items", [])
            for evidence_id in item.get("evidence_event_ids", [])
        ]
        _add_missing_ids(report, artifact, "D05 Evidence ID", ids, facts.event_ids)
    elif dimension_id == "D06":
        versions = payload.get("fact_versions", [])
        winning = {str(value) for value in payload.get("winning_fact_ids", [])}
        stale = {str(value) for value in payload.get("stale_fact_ids", [])}
        version_ids = {str(version.get("fact_id", "")) for version in versions}
        status_winning = {
            str(version.get("fact_id", "")) for version in versions if version.get("status") == "winning"
        }
        status_stale = {
            str(version.get("fact_id", "")) for version in versions if version.get("status") == "stale"
        }
        if winning != status_winning or stale != status_stale or version_ids != winning | stale:
            report.errors.append(
                f"D06/{artifact.case_path.name}: fact version statuses do not match winning/stale IDs"
            )
        source_name = str(envelope.get("metadata", {}).get("source_name", ""))
        lines = (facts.content_text or "").splitlines()
        for version in versions:
            fact_id = str(version.get("fact_id", ""))
            match = re.fullmatch(r"(.+):fact_(\d+)", fact_id)
            if not match or match.group(1) != source_name:
                report.errors.append(f"D06/{artifact.case_path.name}: malformed fact ID {fact_id!r}")
                continue
            fact_number = int(match.group(2))
            line_index = fact_number + 1
            value = str(version.get("value", ""))
            if line_index >= len(lines) or not lines[line_index].startswith(f"{fact_number}. "):
                report.errors.append(f"D06/{artifact.case_path.name}: fact {fact_id!r} has no source line")
            elif _normalise_text(value) not in _normalise_text(lines[line_index]):
                report.errors.append(
                    f"D06/{artifact.case_path.name}: value {value!r} is absent from source line {fact_id!r}"
                )
    elif dimension_id == "D07":
        _add_missing_ids(
            report, artifact, "D07 Evidence ID", payload.get("gold_evidence_ids", []), facts.event_ids
        )
    elif dimension_id == "D08":
        all_memory_ids = (
            list(payload.get("allowed_memory_ids", []))
            + list(payload.get("forbidden_memory_ids", []))
            + list(payload.get("deleted_memory_ids", []))
        )
        _add_missing_ids(report, artifact, "D08 memory ID", all_memory_ids, facts.memory_ids)
        for memory_id in payload.get("deleted_memory_ids", []):
            if memory_id not in facts.deletion_orders:
                report.errors.append(
                    f"D08/{artifact.case_path.name}: deleted memory {memory_id!r} has no delete event"
                )
            elif facts.memory_orders.get(memory_id, 10**18) >= facts.deletion_orders[memory_id]:
                report.errors.append(
                    f"D08/{artifact.case_path.name}: deleted memory {memory_id!r} was not written first"
                )

    query_text = _normalise_text(envelope["query"]["text"])
    for answer in _answer_values(dimension_id, payload):
        normalised_answer = _normalise_text(answer)
        if len(normalised_answer) >= 8 and normalised_answer in query_text:
            report.errors.append(
                f"{dimension_id}/{artifact.case_path.name}: Gold answer is present in Query text"
            )
        # D03 intentionally exposes source-native timestamps: they are the temporal
        # Evidence from which the answer is derived, not a copied answer label.
        if (
            dimension_id != "D03"
            and len(normalised_answer) >= 8
            and normalised_answer in facts.metadata_text
        ):
            report.errors.append(
                f"{dimension_id}/{artifact.case_path.name}: Gold answer is present in Context metadata"
            )


def _audit_d04(report: BenchmarkAuditReport, cases: list[ReviewedCaseArtifact]) -> None:
    activation_counts: Counter[bool] = Counter()
    pairs: dict[str, list[ReviewedCaseArtifact]] = defaultdict(list)
    for artifact in cases:
        payload = artifact.case["gold"]["payload"]
        activation_counts[bool(payload.get("should_activate"))] += 1
        pair_id = str(artifact.case["envelope"]["metadata"].get("pair_id", ""))
        pairs[pair_id].append(artifact)
    if activation_counts != Counter({True: 19, False: 19}):
        report.errors.append(f"D04 activation balance is {dict(activation_counts)}, expected 19/19")
    if len(pairs) != 19 or "" in pairs:
        report.errors.append(f"D04 has {len(pairs)} valid pair groups, expected 19")
    for pair_id, artifacts in pairs.items():
        if len(artifacts) != 2:
            report.errors.append(f"D04 pair {pair_id!r} contains {len(artifacts)} cases")
            continue
        payloads = [artifact.case["gold"]["payload"] for artifact in artifacts]
        queries = {artifact.case["envelope"]["query"]["text"] for artifact in artifacts}
        if {bool(payload["should_activate"]) for payload in payloads} != {True, False}:
            report.errors.append(f"D04 pair {pair_id!r} does not contain one positive and one negative")
        if len(queries) != 1:
            report.errors.append(f"D04 pair {pair_id!r} has inconsistent Query text")
        if len({_json_text(payload.get("preference")) for payload in payloads}) != 1:
            report.errors.append(f"D04 pair {pair_id!r} has inconsistent preference Gold")
        if len({_json_text(payload.get("answer_criteria")) for payload in payloads}) != 1:
            report.errors.append(f"D04 pair {pair_id!r} has inconsistent answer criteria")


def _audit_d07(report: BenchmarkAuditReport, cases: list[ReviewedCaseArtifact]) -> None:
    paired_groups: dict[str, list[ReviewedCaseArtifact]] = defaultdict(list)
    stress_count = 0
    expected_levels = {"100K", "500K", "1M", "10M"}
    for artifact in cases:
        metadata = artifact.case["envelope"]["metadata"]
        payload = artifact.case["gold"]["payload"]
        if metadata.get("case_kind") == "paired_scale":
            paired_groups[str(payload.get("scale_group_id", ""))].append(artifact)
        elif metadata.get("case_kind") == "10m_stress":
            stress_count += 1
        else:
            report.errors.append(f"D07/{artifact.case_path.name}: unknown case_kind")
    if len(paired_groups) != 8 or "" in paired_groups:
        report.errors.append(f"D07 has {len(paired_groups)} paired groups, expected 8")
    if stress_count != 5:
        report.errors.append(f"D07 has {stress_count} stress cases, expected 5")
    for group_id, artifacts in paired_groups.items():
        payloads = [artifact.case["gold"]["payload"] for artifact in artifacts]
        levels = {str(payload.get("scale_level")) for payload in payloads}
        if levels != expected_levels:
            report.errors.append(f"D07 group {group_id!r} has levels {sorted(levels)}")
        queries = {artifact.case["envelope"]["query"]["text"] for artifact in artifacts}
        answers = {_json_text(payload.get("gold_answer")) for payload in payloads}
        evidence = {_json_text(payload.get("gold_evidence_ids")) for payload in payloads}
        if len(queries) != 1:
            report.errors.append(f"D07 group {group_id!r} has inconsistent Query")
        if len(answers) != 1:
            report.errors.append(f"D07 group {group_id!r} has inconsistent Answer")
        if len(evidence) != 1:
            report.errors.append(f"D07 group {group_id!r} has inconsistent Gold Evidence")
        ordered = sorted(
            (
                int(payload["target_tokens"]),
                int(artifact.case["envelope"]["context"]["token_count"]),
            )
            for artifact, payload in zip(artifacts, payloads)
        )
        if any(a[0] >= b[0] or a[1] >= b[1] for a, b in zip(ordered, ordered[1:])):
            report.errors.append(f"D07 group {group_id!r} is not monotonically increasing")


def _audit_d08(
    report: BenchmarkAuditReport,
    cases: list[ReviewedCaseArtifact],
    context_cache: dict[Path, ContextFacts],
) -> None:
    scenario_counts: Counter[str] = Counter()
    all_canaries: list[str] = []
    for artifact in cases:
        payload = artifact.case["gold"]["payload"]
        scenario_counts[str(payload.get("scenario_type", ""))] += 1
        if payload.get("owner_user_id") == payload.get("querying_user_id"):
            report.errors.append(f"D08/{artifact.case_path.name}: owner and querying user are identical")
        forbidden = payload.get("forbidden_memory_ids", [])
        if not forbidden:
            report.errors.append(f"D08/{artifact.case_path.name}: forbidden_memory_ids is empty")
        facts = context_cache[artifact.context_path]
        for canary in payload.get("canary_tokens", []):
            token = str(canary)
            all_canaries.append(token)
            if (facts.content_text or "").count(token) != 1:
                report.errors.append(
                    f"D08/{artifact.case_path.name}: Canary {token!r} does not appear exactly once"
                )
    expected = Counter(
        {"cross_user_isolation": 19, "deletion": 10, "forbidden_canary_exposure": 8}
    )
    if scenario_counts != expected:
        report.errors.append(f"D08 scenario counts are {dict(scenario_counts)}, expected {dict(expected)}")
    if len(all_canaries) != len(set(all_canaries)):
        report.errors.append("D08 Canary tokens are not globally unique")


def audit_benchmark(
    root: str | Path,
    *,
    expected_counts: dict[str, int] | None = None,
    verify_hashes: bool = True,
) -> BenchmarkAuditReport:
    """Run all stage-23 structural, review, Evidence and dimension checks."""

    report = BenchmarkAuditReport()
    benchmark = ReviewedBenchmark(root)
    expected = expected_counts or EXPECTED_CASE_COUNTS

    try:
        report.review_counts = benchmark.assert_review_complete()
    except (FileNotFoundError, KeyError, ValueError, json.JSONDecodeError) as exc:
        report.errors.append(f"Human-review verification failed: {exc}")

    artifacts_by_dimension: dict[str, list[ReviewedCaseArtifact]] = {}
    all_artifacts: list[ReviewedCaseArtifact] = []
    for dimension_id in DIMENSION_DIRECTORIES:
        try:
            artifacts = list(benchmark.iter_cases(dimension_id))
        except (FileNotFoundError, KeyError, ValueError, json.JSONDecodeError) as exc:
            report.errors.append(f"{dimension_id} cannot be loaded: {exc}")
            artifacts = []
        artifacts_by_dimension[dimension_id] = artifacts
        all_artifacts.extend(artifacts)
        report.case_counts[dimension_id] = len(artifacts)
        expected_count = expected.get(dimension_id)
        if expected_count is not None and len(artifacts) != expected_count:
            report.errors.append(
                f"{dimension_id} has {len(artifacts)} cases, expected {expected_count}"
            )

    seen_case_ids: dict[str, str] = {}
    seen_query_ids: dict[str, str] = {}
    fingerprints: dict[str, str] = {}
    context_cache: dict[Path, ContextFacts] = {}
    hash_cache: dict[Path, str] = {}

    for artifact in all_artifacts:
        case = artifact.case
        envelope = case.get("envelope", {})
        gold = case.get("gold", {})
        case_id = str(envelope.get("case_id", "")).strip()
        query = envelope.get("query", {})
        query_id = str(query.get("query_id", "")).strip()
        query_text = str(query.get("text", "")).strip()
        source_record_id = str(envelope.get("source", {}).get("source_record_id", "")).strip()
        payload_type = str(gold.get("payload_type", ""))
        payload = gold.get("payload")

        if not case_id:
            report.errors.append(f"{artifact.dimension_id}/{artifact.case_path.name}: empty case_id")
        elif case_id in seen_case_ids:
            report.errors.append(
                f"Duplicate case_id {case_id!r}: {seen_case_ids[case_id]} and {artifact.case_path}"
            )
        else:
            seen_case_ids[case_id] = str(artifact.case_path)
        if not query_id:
            report.errors.append(f"{artifact.dimension_id}/{artifact.case_path.name}: empty query_id")
        elif query_id in seen_query_ids:
            report.errors.append(
                f"Duplicate query_id {query_id!r}: {seen_query_ids[query_id]} and {artifact.case_path}"
            )
        else:
            seen_query_ids[query_id] = str(artifact.case_path)
        if not query_text:
            report.errors.append(f"{artifact.dimension_id}/{artifact.case_path.name}: empty Query text")
        if not source_record_id:
            report.errors.append(
                f"{artifact.dimension_id}/{artifact.case_path.name}: source_record_id is not traceable"
            )
        if envelope.get("dimension_id") != artifact.dimension_id:
            report.errors.append(f"{artifact.dimension_id}/{artifact.case_path.name}: dimension_id mismatch")
        if payload_type != EXPECTED_PAYLOAD_TYPES[artifact.dimension_id] or not isinstance(payload, dict):
            report.errors.append(
                f"{artifact.dimension_id}/{artifact.case_path.name}: Gold Payload does not match dimension"
            )
            continue

        fingerprint = hashlib.sha256(
            _json_text(
                {
                    "dimension": artifact.dimension_id,
                    "context_ref": envelope.get("context", {}).get("context_ref"),
                    "query": query_text,
                    "gold": payload,
                }
            ).encode("utf-8")
        ).hexdigest()
        if fingerprint in fingerprints:
            report.errors.append(
                f"Duplicate Case content: {fingerprints[fingerprint]} and {artifact.case_path}"
            )
        else:
            fingerprints[fingerprint] = str(artifact.case_path)

        if not artifact.context_path.is_file():
            report.errors.append(
                f"{artifact.dimension_id}/{artifact.case_path.name}: missing {artifact.context_path}"
            )
            continue
        if artifact.context_path not in context_cache:
            try:
                context_cache[artifact.context_path] = _load_context_facts(
                    artifact.context_path,
                    collect_content=artifact.dimension_id in {"D06", "D08"},
                )
                hash_cache[artifact.context_path] = context_cache[artifact.context_path].sha256
            except (OSError, ValueError, json.JSONDecodeError) as exc:
                report.errors.append(f"Cannot parse Context {artifact.context_path}: {exc}")
                continue
        facts = context_cache[artifact.context_path]
        context_ref = envelope.get("context", {})
        if int(context_ref.get("event_count", -1)) != facts.event_count:
            report.errors.append(f"{artifact.dimension_id}/{artifact.case_path.name}: event_count mismatch")
        if context_ref.get("event_start") != facts.event_start:
            report.errors.append(f"{artifact.dimension_id}/{artifact.case_path.name}: event_start mismatch")
        if context_ref.get("event_end") != facts.event_end:
            report.errors.append(f"{artifact.dimension_id}/{artifact.case_path.name}: event_end mismatch")
        if len(facts.event_ids) != facts.event_count:
            report.errors.append(f"{artifact.dimension_id}/{artifact.case_path.name}: duplicate/empty event_id")
        _audit_case_references(report, artifact, facts)

    report.context_count = len(context_cache)

    if verify_hashes:
        for dimension_id in DIMENSION_DIRECTORIES:
            try:
                manifest = benchmark.load_manifest(dimension_id)
                version_dir = benchmark.dimension_dir(dimension_id).resolve()
            except (FileNotFoundError, KeyError, json.JSONDecodeError) as exc:
                report.errors.append(f"{dimension_id} hash manifest cannot be loaded: {exc}")
                continue
            file_hashes = manifest.get("file_hashes")
            if not isinstance(file_hashes, dict) or not file_hashes:
                report.errors.append(f"{dimension_id} manifest has no file_hashes")
                continue
            for relative_path, expected_hash in sorted(file_hashes.items()):
                path = (version_dir / relative_path).resolve()
                try:
                    path.relative_to(version_dir)
                except ValueError:
                    report.errors.append(f"{dimension_id} hash path escapes version directory: {relative_path}")
                    continue
                if not path.is_file():
                    report.errors.append(f"{dimension_id} hash target is missing: {relative_path}")
                    continue
                actual_hash = hash_cache.get(path)
                if actual_hash is None:
                    actual_hash = _sha256(path)
                    hash_cache[path] = actual_hash
                report.checked_hash_count += 1
                if actual_hash != str(expected_hash):
                    report.errors.append(f"{dimension_id} SHA-256 mismatch: {relative_path}")

    _audit_d04(report, artifacts_by_dimension["D04"])
    _audit_d07(report, artifacts_by_dimension["D07"])
    _audit_d08(report, artifacts_by_dimension["D08"], context_cache)
    return report
