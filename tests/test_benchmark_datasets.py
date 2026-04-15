"""Integration tests for the benchmark datasets."""

from pathlib import Path

import pytest

from anomyze.benchmark.loader import load_dataset
from anomyze.channels.govgpt import ENTITY_GROUP_TO_PLACEHOLDER

KNOWN_CATEGORIES = set(ENTITY_GROUP_TO_PLACEHOLDER) | {
    "ORG_DETECTED",
    "QUASI_ID",
    "FIRMENBUCH",
}

DATASETS_DIR = Path(__file__).resolve().parents[1] / "benchmarks" / "datasets"


KNOWN_CATEGORIES.update({"UID", "BIC"})


@pytest.mark.parametrize(
    "filename",
    ["synthetic_at.json", "realistic_at.json", "smoke_at.json"],
)
def test_dataset_loads_and_spans_are_valid(filename: str) -> None:
    dataset_path = DATASETS_DIR / filename
    assert dataset_path.exists(), f"Missing dataset file: {dataset_path}"

    samples = load_dataset(dataset_path)
    assert samples, f"Dataset {filename} is empty"

    for sample in samples:
        assert sample.text, f"Sample {sample.id!r} has empty text"
        for entity in sample.entities:
            # Spans are validated by the loader, but double-check here
            assert 0 <= entity.start < entity.end <= len(sample.text)
            substring = sample.text[entity.start:entity.end]
            assert substring, (
                f"Sample {sample.id!r}: empty slice at [{entity.start}:{entity.end}]"
            )
            assert entity.type in KNOWN_CATEGORIES, (
                f"Sample {sample.id!r}: unknown entity type {entity.type!r}"
            )


def test_synthetic_dataset_has_minimum_size() -> None:
    samples = load_dataset(DATASETS_DIR / "synthetic_at.json")
    assert len(samples) >= 20, (
        f"synthetic_at.json should have at least 20 samples, got {len(samples)}"
    )


def test_realistic_dataset_covers_multiple_categories() -> None:
    samples = load_dataset(DATASETS_DIR / "realistic_at.json")
    categories = {e.type for s in samples for e in s.entities}
    # At least 6 different PII categories across the realistic docs
    assert len(categories) >= 6, (
        f"realistic_at.json only covers {categories}"
    )
