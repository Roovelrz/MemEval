"""Registry for concrete stage-21 Dimension Builders."""

from __future__ import annotations

from .base import DimensionBuilder


DIMENSION_BUILDERS: dict[str, type[DimensionBuilder]] = {}


def register_dimension_builder(builder_class: type[DimensionBuilder]) -> type[DimensionBuilder]:
    dimension_id = builder_class.dimension_id.strip().lower()
    if not dimension_id:
        raise ValueError("Dimension Builder must define dimension_id")
    if dimension_id in DIMENSION_BUILDERS:
        raise ValueError(f"Dimension Builder {dimension_id!r} is already registered")
    DIMENSION_BUILDERS[dimension_id] = builder_class
    return builder_class


def create_dimension_builder(dimension_id: str) -> DimensionBuilder:
    key = dimension_id.strip().lower()
    try:
        builder_class = DIMENSION_BUILDERS[key]
    except KeyError as exc:
        choices = ", ".join(sorted(DIMENSION_BUILDERS)) or "none registered yet"
        raise ValueError(f"Unknown Dimension Builder {dimension_id!r}; available: {choices}") from exc
    return builder_class()
