"""Dimension Builder interfaces and registry."""

from .base import DimensionBuildResult, DimensionBuilder, DimensionCandidate, DimensionCase
from .registry import DIMENSION_BUILDERS, create_dimension_builder, register_dimension_builder
from .d01_write import D01WriteBuilder
from .d02_retrieval import D02RetrievalBuilder
from .d03_temporal import D03TemporalBuilder
from .d04_activation import D04ActivationBuilder
from .d05_profile import D05ProfileBuilder
from .d06_conflict import D06ConflictBuilder
from .d07_scale import D07ScaleBuilder
from .d08_privacy import D08PrivacyBuilder

__all__ = [
    "DIMENSION_BUILDERS",
    "DimensionBuildResult",
    "DimensionBuilder",
    "DimensionCandidate",
    "DimensionCase",
    "D01WriteBuilder",
    "D02RetrievalBuilder",
    "D03TemporalBuilder",
    "D04ActivationBuilder",
    "D05ProfileBuilder",
    "D06ConflictBuilder",
    "D07ScaleBuilder",
    "D08PrivacyBuilder",
    "create_dimension_builder",
    "register_dimension_builder",
]
