"""Trace adapters bridging runner-native results to the dashboard contract."""

from .memeval import ANSWER_DIMENSIONS, MemEvalTraceAdapter

__all__ = ["ANSWER_DIMENSIONS", "MemEvalTraceAdapter"]
