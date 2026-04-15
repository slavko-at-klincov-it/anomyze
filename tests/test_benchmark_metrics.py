"""Unit tests for benchmark metrics."""

from anomyze.benchmark.loader import GroundTruthEntity, Sample
from anomyze.benchmark.metrics import compute_metrics
from anomyze.pipeline import DetectedEntity


def _pred(
    entity_group: str,
    start: int,
    end: int,
    source: str = "regex",
    word: str = "x",
    score: float = 1.0,
) -> DetectedEntity:
    return DetectedEntity(
        word=word,
        entity_group=entity_group,
        score=score,
        start=start,
        end=end,
        source=source,
    )


def _sample(sample_id: str, text: str, entities: list[GroundTruthEntity]) -> Sample:
    return Sample(id=sample_id, text=text, entities=entities)


def test_perfect_match_yields_unity_metrics() -> None:
    samples = [
        _sample(
            "s1",
            "foo bar",
            [GroundTruthEntity(0, 3, "EMAIL"), GroundTruthEntity(4, 7, "IBAN")],
        )
    ]
    preds = [[_pred("EMAIL", 0, 3), _pred("IBAN", 4, 7)]]

    report = compute_metrics(preds, samples)

    assert report.overall.precision == 1.0
    assert report.overall.recall == 1.0
    assert report.overall.f1 == 1.0
    assert report.by_category["EMAIL"].f1 == 1.0
    assert report.by_category["IBAN"].f1 == 1.0


def test_all_false_positives() -> None:
    samples = [_sample("s1", "abcdefghij", [])]
    preds = [[_pred("EMAIL", 0, 3)]]

    report = compute_metrics(preds, samples)

    assert report.overall.tp == 0
    assert report.overall.fp == 1
    assert report.overall.precision == 0.0
    assert report.overall.recall == 0.0


def test_all_false_negatives() -> None:
    samples = [_sample("s1", "abcdefghij", [GroundTruthEntity(0, 4, "EMAIL")])]
    preds: list[list[DetectedEntity]] = [[]]

    report = compute_metrics(preds, samples)

    assert report.overall.tp == 0
    assert report.overall.fn == 1
    assert report.overall.precision == 0.0
    assert report.overall.recall == 0.0


def test_iou_exactly_fifty_percent_is_tp() -> None:
    # Span A = [0, 10], span B = [5, 10] -> inter=5, union=10, IoU=0.5
    samples = [_sample("s1", "a" * 20, [GroundTruthEntity(0, 10, "EMAIL")])]
    preds = [[_pred("EMAIL", 5, 10)]]

    report = compute_metrics(preds, samples)

    assert report.overall.tp == 1
    assert report.overall.fp == 0
    assert report.overall.fn == 0


def test_iou_below_fifty_same_category_counts_fp_and_fn() -> None:
    # Span A = [0, 10], span B = [6, 10] -> inter=4, union=10, IoU=0.4
    samples = [_sample("s1", "a" * 20, [GroundTruthEntity(0, 10, "EMAIL")])]
    preds = [[_pred("EMAIL", 6, 10)]]

    report = compute_metrics(preds, samples)

    assert report.overall.tp == 0
    assert report.overall.fp == 1
    assert report.overall.fn == 1


def test_same_span_different_category_counts_fp_and_fn() -> None:
    samples = [_sample("s1", "a" * 20, [GroundTruthEntity(0, 10, "EMAIL")])]
    preds = [[_pred("IBAN", 0, 10)]]

    report = compute_metrics(preds, samples)

    assert report.overall.tp == 0
    assert report.overall.fp == 1
    assert report.overall.fn == 1
    assert report.by_category["EMAIL"].fn == 1
    assert report.by_category["IBAN"].fp == 1


def test_empty_inputs_yield_zero_metrics() -> None:
    samples = [_sample("s1", "text", [])]
    preds: list[list[DetectedEntity]] = [[]]

    report = compute_metrics(preds, samples)

    assert report.overall.tp == 0
    assert report.overall.fp == 0
    assert report.overall.fn == 0
    assert report.overall.precision == 0.0
    assert report.overall.recall == 0.0
    assert report.overall.f1 == 0.0


def test_per_category_aggregation() -> None:
    samples = [
        _sample(
            "s1",
            "abcdefghijkl",
            [
                GroundTruthEntity(0, 3, "EMAIL"),
                GroundTruthEntity(4, 7, "EMAIL"),
                GroundTruthEntity(8, 12, "IBAN"),
            ],
        )
    ]
    # Detect both EMAILs correctly, miss the IBAN, produce one IBAN FP
    preds = [
        [
            _pred("EMAIL", 0, 3),
            _pred("EMAIL", 4, 7),
            _pred("IBAN", 0, 3),
        ]
    ]

    report = compute_metrics(preds, samples)

    assert report.by_category["EMAIL"].tp == 2
    assert report.by_category["EMAIL"].fp == 0
    assert report.by_category["EMAIL"].fn == 0
    assert report.by_category["EMAIL"].f1 == 1.0
    assert report.by_category["IBAN"].tp == 0
    assert report.by_category["IBAN"].fp == 1
    assert report.by_category["IBAN"].fn == 1


def test_layer_breakdown_credits_each_layer() -> None:
    samples = [
        _sample(
            "s1",
            "abcdefghijkl",
            [GroundTruthEntity(0, 3, "EMAIL"), GroundTruthEntity(4, 7, "PER")],
        )
    ]
    preds = [
        [
            _pred("EMAIL", 0, 3, source="regex"),
            _pred("PER", 4, 7, source="pii"),
            _pred("IBAN", 8, 12, source="regex"),
        ]
    ]

    report = compute_metrics(preds, samples)

    assert report.by_layer["regex"].tp == 1  # EMAIL
    assert report.by_layer["regex"].fp == 1  # IBAN
    assert report.by_layer["regex"].fn == 1  # missed PER
    assert report.by_layer["pii"].tp == 1  # PER
    assert report.by_layer["pii"].fp == 0
    assert report.by_layer["pii"].fn == 1  # missed EMAIL


def test_mismatched_lengths_raises() -> None:
    import pytest

    samples = [_sample("s1", "x", [])]
    preds: list[list[DetectedEntity]] = [[], []]

    with pytest.raises(ValueError):
        compute_metrics(preds, samples)


def test_greedy_matching_prefers_best_iou() -> None:
    # Two predictions for the same GT. Only the best IoU one should count as TP.
    samples = [_sample("s1", "a" * 20, [GroundTruthEntity(0, 10, "EMAIL")])]
    preds = [[_pred("EMAIL", 0, 5), _pred("EMAIL", 0, 10)]]

    report = compute_metrics(preds, samples)

    # Second pred (IoU=1) is TP, first pred (IoU=0.5) is FP
    assert report.overall.tp == 1
    assert report.overall.fp == 1
    assert report.overall.fn == 0
