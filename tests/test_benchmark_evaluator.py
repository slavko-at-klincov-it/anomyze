"""Unit tests for the benchmark evaluator."""

from anomyze.benchmark.evaluator import Evaluator
from anomyze.benchmark.loader import GroundTruthEntity, Sample
from anomyze.pipeline import DetectedEntity


class _MockOrchestrator:
    """Returns pre-defined predictions keyed by sample text."""

    def __init__(self, canned: dict[str, list[DetectedEntity]]):
        self.canned = canned
        self.calls: list[str] = []

    def detect(self, text: str) -> tuple[str, list[DetectedEntity]]:
        self.calls.append(text)
        return text, list(self.canned.get(text, []))


def _pred(
    entity_group: str, start: int, end: int, source: str = "regex"
) -> DetectedEntity:
    return DetectedEntity(
        word="x",
        entity_group=entity_group,
        score=1.0,
        start=start,
        end=end,
        source=source,
    )


def test_evaluator_runs_all_samples() -> None:
    samples = [
        Sample(
            id="s1",
            text="Email a@b.at hier",
            entities=[GroundTruthEntity(6, 12, "EMAIL")],
        ),
        Sample(
            id="s2",
            text="IBAN AT00 0000",
            entities=[GroundTruthEntity(5, 14, "IBAN")],
        ),
        Sample(
            id="s3",
            text="Nichts",
            entities=[],
        ),
    ]
    orch = _MockOrchestrator(
        {
            "Email a@b.at hier": [_pred("EMAIL", 6, 12, source="regex")],
            "IBAN AT00 0000": [_pred("IBAN", 5, 14, source="regex")],
            "Nichts": [],
        }
    )

    report = Evaluator(orch, samples).run()

    assert orch.calls == ["Email a@b.at hier", "IBAN AT00 0000", "Nichts"]
    assert report.num_samples == 3
    assert report.overall.tp == 2
    assert report.overall.fp == 0
    assert report.overall.fn == 0
    assert report.overall.f1 == 1.0


def test_evaluator_layer_breakdown_from_source() -> None:
    samples = [
        Sample(
            id="s1",
            text="text",
            entities=[
                GroundTruthEntity(0, 2, "EMAIL"),
                GroundTruthEntity(2, 4, "PER"),
            ],
        )
    ]
    orch = _MockOrchestrator(
        {
            "text": [
                _pred("EMAIL", 0, 2, source="regex"),
                _pred("PER", 2, 4, source="pii"),
            ]
        }
    )

    report = Evaluator(orch, samples).run()

    assert report.by_layer["regex"].tp == 1
    assert report.by_layer["regex"].fn == 1  # pii layer found PER, regex missed it
    assert report.by_layer["pii"].tp == 1
    assert report.by_layer["pii"].fn == 1


def test_evaluator_mixed_outcomes() -> None:
    samples = [
        Sample(
            id="s1",
            text="abcdefghij",
            entities=[
                GroundTruthEntity(0, 5, "EMAIL"),
                GroundTruthEntity(5, 10, "IBAN"),
            ],
        )
    ]
    # Correct EMAIL, wrong category for IBAN position, extra PER FP
    orch = _MockOrchestrator(
        {
            "abcdefghij": [
                _pred("EMAIL", 0, 5, source="regex"),
                _pred("EMAIL", 5, 10, source="regex"),
                _pred("PER", 0, 5, source="pii"),
            ]
        }
    )

    report = Evaluator(orch, samples).run()

    assert report.by_category["EMAIL"].tp == 1
    assert report.by_category["EMAIL"].fp == 1
    assert report.by_category["IBAN"].fn == 1
    assert report.by_category["PER"].fp == 1
