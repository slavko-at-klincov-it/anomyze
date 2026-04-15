"""
Benchmark evaluator.

Runs a pipeline orchestrator over a list of samples and returns a
BenchmarkReport comparing predictions against ground truth.
"""

from collections.abc import Sequence
from typing import Protocol

from anomyze.benchmark.loader import Sample
from anomyze.benchmark.metrics import BenchmarkReport, compute_metrics
from anomyze.pipeline import DetectedEntity


class _Detector(Protocol):
    def detect(self, text: str) -> tuple[str, list[DetectedEntity]]:
        ...


class Evaluator:
    """Runs a pipeline orchestrator over samples and computes metrics.

    The orchestrator only needs a ``detect(text)`` method returning
    ``(preprocessed_text, entities)``. This matches
    :class:`anomyze.pipeline.orchestrator.PipelineOrchestrator` and
    is easy to mock in tests.
    """

    def __init__(
        self,
        orchestrator: _Detector,
        samples: Sequence[Sample],
        iou_threshold: float = 0.5,
    ):
        self.orchestrator = orchestrator
        self.samples = list(samples)
        self.iou_threshold = iou_threshold

    def run(self) -> BenchmarkReport:
        """Execute detection for every sample and aggregate metrics."""
        predictions: list[list[DetectedEntity]] = []
        for sample in self.samples:
            _text, entities = self.orchestrator.detect(sample.text)
            predictions.append(entities)
        return compute_metrics(predictions, self.samples, self.iou_threshold)
