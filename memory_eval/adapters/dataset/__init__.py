"""Dataset adapters that map benchmark-specific records to one eval schema."""

from .base import DatasetAdapter, DatasetLoadResult
from .registry import create_dataset_adapter, load_dataset_cases

__all__ = [
    "DatasetAdapter",
    "DatasetLoadResult",
    "create_dataset_adapter",
    "load_dataset_cases",
]

