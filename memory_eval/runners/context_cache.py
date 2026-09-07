"""Validated Context grouping for performance-only batch runs."""

from __future__ import annotations

import hashlib
from collections import OrderedDict
from dataclasses import dataclass
from typing import Iterable

from dataset.build_pipeline.release import ReviewedCaseArtifact


@dataclass(frozen=True)
class ContextGroup:
    context_id: str
    context_sha256: str
    artifacts: tuple[ReviewedCaseArtifact, ...]


class ContextCache:
    """Group identical Contexts without weakening tenant or user boundaries."""

    def group(self, artifacts: Iterable[ReviewedCaseArtifact]) -> list[ContextGroup]:
        rows = list(artifacts)
        hashes_by_context: dict[str, str] = {}
        groups: OrderedDict[tuple[str, str, str, str], list[ReviewedCaseArtifact]] = OrderedDict()
        digests: dict[tuple[str, str, str, str], str] = {}

        for artifact in rows:
            envelope = artifact.case["envelope"]
            identity = envelope["identity"]
            context_id = str(identity.get("context_id") or "")
            if not context_id:
                raise ValueError(f"Case {envelope['case_id']!r} has no context_id")
            digest = hashlib.sha256(artifact.context_path.read_bytes()).hexdigest()
            previous = hashes_by_context.setdefault(context_id, digest)
            if previous != digest:
                raise ValueError(f"context_id {context_id!r} refers to different Context content")

            # D08 actions can delete data and therefore always retain Case isolation.
            mutation_scope = str(envelope["case_id"]) if artifact.dimension_id == "D08" else ""
            key = (
                context_id,
                str(identity.get("tenant_id") or ""),
                str(identity.get("user_id") or ""),
                mutation_scope,
            )
            groups.setdefault(key, []).append(artifact)
            digests[key] = digest

        return [
            ContextGroup(key[0], digests[key], tuple(group))
            for key, group in groups.items()
        ]
