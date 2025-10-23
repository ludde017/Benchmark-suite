"""OCR benchmark suite package."""

from .data_loader import DocumentSample, load_manifest
from .evaluator import BenchmarkRunner
from .metrics import compute_metrics

__all__ = [
    "DocumentSample",
    "load_manifest",
    "BenchmarkRunner",
    "compute_metrics",
]
