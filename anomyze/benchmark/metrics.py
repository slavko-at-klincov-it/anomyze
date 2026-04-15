"""
Metric computation for benchmark framework.

Computes precision, recall, and F1 between detected entities and
ground-truth annotations, per category and overall. Provides a
per-layer breakdown grouped by entity.source so you can see which
detection stage contributes how much.
"""

from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field

from anomyze.benchmark.loader import GroundTruthEntity, Sample
from anomyze.pipeline import DetectedEntity


@dataclass
class CategoryMetrics:
    """Precision/recall/F1 counts for a single category or layer.

    Attributes:
        tp: True positive count.
        fp: False positive count.
        fn: False negative count.
        precision: TP / (TP + FP), 0.0 when denominator is 0.
        recall: TP / (TP + FN), 0.0 when denominator is 0.
        f1: Harmonic mean of precision and recall, 0.0 when P+R is 0.
    """

    tp: int = 0
    fp: int = 0
    fn: int = 0
    precision: float = 0.0
    recall: float = 0.0
    f1: float = 0.0

    def finalize(self) -> None:
        """Compute derived precision/recall/F1 from tp/fp/fn."""
        self.precision = self.tp / (self.tp + self.fp) if (self.tp + self.fp) else 0.0
        self.recall = self.tp / (self.tp + self.fn) if (self.tp + self.fn) else 0.0
        denom = self.precision + self.recall
        self.f1 = (2 * self.precision * self.recall / denom) if denom else 0.0


@dataclass
class BenchmarkReport:
    """Aggregated metrics for an evaluation run.

    Attributes:
        overall: Metrics aggregated across all categories.
        by_category: Metrics per entity category.
        by_layer: Metrics grouped by entity.source.
        num_samples: Number of samples evaluated.
    """

    overall: CategoryMetrics = field(default_factory=CategoryMetrics)
    by_category: dict[str, CategoryMetrics] = field(default_factory=dict)
    by_layer: dict[str, CategoryMetrics] = field(default_factory=dict)
    num_samples: int = 0


def _iou(a_start: int, a_end: int, b_start: int, b_end: int) -> float:
    """Intersection-over-union for two half-open integer spans."""
    inter = max(0, min(a_end, b_end) - max(a_start, b_start))
    if inter == 0:
        return 0.0
    union = max(a_end, b_end) - min(a_start, b_start)
    return inter / union if union else 0.0


def _spans_overlap(
    pred: DetectedEntity, gt: GroundTruthEntity, iou_threshold: float = 0.5
) -> bool:
    """Return True if prediction and ground truth spans overlap with IoU >= threshold."""
    return _iou(pred.start, pred.end, gt.start, gt.end) >= iou_threshold


def _layer_of(entity: DetectedEntity) -> str:
    return entity.source or "unknown"


def _match_pairs(
    predictions: Sequence[DetectedEntity],
    ground_truth: Sequence[GroundTruthEntity],
    iou_threshold: float,
) -> tuple[list[tuple[int, int]], set[int], set[int]]:
    """Greedy 1:1 matching: each pred-gt pair must share category and IoU>=threshold."""
    candidates: list[tuple[float, int, int]] = []
    for i, pred in enumerate(predictions):
        for j, gt in enumerate(ground_truth):
            if pred.entity_group != gt.type:
                continue
            iou = _iou(pred.start, pred.end, gt.start, gt.end)
            if iou >= iou_threshold:
                candidates.append((iou, i, j))

    candidates.sort(key=lambda c: (-c[0], c[1], c[2]))

    used_pred: set[int] = set()
    used_gt: set[int] = set()
    matches: list[tuple[int, int]] = []

    for _iou_val, pi, gj in candidates:
        if pi in used_pred or gj in used_gt:
            continue
        used_pred.add(pi)
        used_gt.add(gj)
        matches.append((pi, gj))

    unmatched_pred = set(range(len(predictions))) - used_pred
    unmatched_gt = set(range(len(ground_truth))) - used_gt
    return matches, unmatched_pred, unmatched_gt


def _collect_all_layers(
    predictions_by_sample: Sequence[Sequence[DetectedEntity]],
) -> set[str]:
    layers: set[str] = set()
    for preds in predictions_by_sample:
        for p in preds:
            layers.add(_layer_of(p))
    return layers


def compute_metrics(
    predictions_by_sample: Iterable[Sequence[DetectedEntity]],
    samples: Sequence[Sample],
    iou_threshold: float = 0.5,
) -> BenchmarkReport:
    """Compute precision/recall/F1 over all samples.

    Per-category metrics use a greedy 1:1 match between predictions and
    ground truth requiring identical category and IoU >= iou_threshold.

    Per-layer metrics credit each layer independently: for each GT entity
    the layer gets a TP if any of its predictions matches, otherwise FN;
    each unmatched prediction of a layer contributes an FP.

    Args:
        predictions_by_sample: Iterable of prediction lists, aligned with samples.
        samples: Benchmark samples with ground-truth annotations.
        iou_threshold: Minimum IoU required to count a match.

    Returns:
        BenchmarkReport with overall, per-category and per-layer metrics.
    """
    predictions_list = [list(preds) for preds in predictions_by_sample]

    if len(predictions_list) != len(samples):
        raise ValueError(
            f"Predictions ({len(predictions_list)}) and samples ({len(samples)}) "
            "have different lengths"
        )

    report = BenchmarkReport(num_samples=len(samples))
    all_layers = _collect_all_layers(predictions_list)

    for preds, sample in zip(predictions_list, samples, strict=True):
        _accumulate_category_counts(
            preds, sample.entities, report.by_category, iou_threshold
        )
        _accumulate_layer_counts(
            preds, sample.entities, report.by_layer, all_layers, iou_threshold
        )

    for metrics in report.by_category.values():
        metrics.finalize()
    for metrics in report.by_layer.values():
        metrics.finalize()

    report.overall.tp = sum(m.tp for m in report.by_category.values())
    report.overall.fp = sum(m.fp for m in report.by_category.values())
    report.overall.fn = sum(m.fn for m in report.by_category.values())
    report.overall.finalize()

    return report


def _accumulate_category_counts(
    predictions: Sequence[DetectedEntity],
    ground_truth: Sequence[GroundTruthEntity],
    by_category: dict[str, CategoryMetrics],
    iou_threshold: float,
) -> None:
    matches, unmatched_pred, unmatched_gt = _match_pairs(
        predictions, ground_truth, iou_threshold
    )

    for pi, _gj in matches:
        category = predictions[pi].entity_group
        by_category.setdefault(category, CategoryMetrics()).tp += 1

    for pi in unmatched_pred:
        category = predictions[pi].entity_group
        by_category.setdefault(category, CategoryMetrics()).fp += 1

    for gj in unmatched_gt:
        category = ground_truth[gj].type
        by_category.setdefault(category, CategoryMetrics()).fn += 1


def _accumulate_layer_counts(
    predictions: Sequence[DetectedEntity],
    ground_truth: Sequence[GroundTruthEntity],
    by_layer: dict[str, CategoryMetrics],
    all_layers: set[str],
    iou_threshold: float,
) -> None:
    """Credit each layer independently per ground-truth entity and prediction."""
    preds_by_layer: dict[str, list[DetectedEntity]] = {}
    for p in predictions:
        preds_by_layer.setdefault(_layer_of(p), []).append(p)

    for layer in all_layers:
        layer_preds = preds_by_layer.get(layer, [])
        matches, unmatched_pred, unmatched_gt = _match_pairs(
            layer_preds, ground_truth, iou_threshold
        )
        bucket = by_layer.setdefault(layer, CategoryMetrics())
        bucket.tp += len(matches)
        bucket.fp += len(unmatched_pred)
        bucket.fn += len(unmatched_gt)
