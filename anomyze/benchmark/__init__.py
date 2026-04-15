"""
Benchmark framework for Anomyze.

Measures detection quality (precision, recall, F1) on annotated
ground-truth datasets. Enables regression detection and per-layer
analysis (which layer detects which PII category how well).
"""

from anomyze.benchmark.evaluator import Evaluator
from anomyze.benchmark.loader import GroundTruthEntity, Sample, load_dataset
from anomyze.benchmark.metrics import (
    BenchmarkReport,
    CategoryMetrics,
    compute_metrics,
)
from anomyze.benchmark.reporter import format_json, format_text

__all__ = [
    "BenchmarkReport",
    "CategoryMetrics",
    "Evaluator",
    "GroundTruthEntity",
    "Sample",
    "compute_metrics",
    "format_json",
    "format_text",
    "load_dataset",
]
