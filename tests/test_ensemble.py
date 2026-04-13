"""Tests for the ensemble aggregation layer."""

import pytest

from anomyze.pipeline import DetectedEntity
from anomyze.pipeline.ensemble import merge_entities


class TestEnsembleMerge:
    """Test basic ensemble merging behavior."""

    def test_empty_input(self) -> None:
        assert merge_entities([], "") == []

    def test_single_entity_passthrough(self) -> None:
        ent = DetectedEntity(
            word="Maria", entity_group="PER", score=0.9,
            start=0, end=5, source="pii",
        )
        result = merge_entities([ent], "Maria ist hier")
        assert len(result) == 1
        assert result[0].word == "Maria"
        assert result[0].score == 0.9
        assert result[0].source == "pii"
        assert result[0].sources == ("pii",)

    def test_non_overlapping_stay_separate(self) -> None:
        text = "Maria arbeitet bei XYZ GmbH"
        entities = [
            DetectedEntity(
                word="Maria", entity_group="PER", score=0.9,
                start=0, end=5, source="pii",
            ),
            DetectedEntity(
                word="XYZ GmbH", entity_group="ORG", score=0.85,
                start=19, end=27, source="org",
            ),
        ]
        result = merge_entities(entities, text)
        assert len(result) == 2
        assert result[0].word == "Maria"
        assert result[1].word == "XYZ GmbH"


class TestConfidenceAggregation:
    """Test the confidence score combination formula."""

    def test_two_sources_combined(self) -> None:
        text = "Maria Huber ist hier"
        entities = [
            DetectedEntity(
                word="Maria Huber", entity_group="PER", score=0.9,
                start=0, end=11, source="regex",
            ),
            DetectedEntity(
                word="Maria Huber", entity_group="PER", score=0.85,
                start=0, end=11, source="pii",
            ),
        ]
        result = merge_entities(entities, text)
        assert len(result) == 1
        # 1 - (1-0.9)*(1-0.85) = 1 - 0.1*0.15 = 1 - 0.015 = 0.985
        assert result[0].score == pytest.approx(0.985)

    def test_three_sources_combined(self) -> None:
        text = "Maria Huber ist hier"
        entities = [
            DetectedEntity(
                word="Maria Huber", entity_group="PER", score=0.9,
                start=0, end=11, source="regex",
            ),
            DetectedEntity(
                word="Maria Huber", entity_group="PER", score=0.85,
                start=0, end=11, source="pii",
            ),
            DetectedEntity(
                word="Maria Huber", entity_group="PER", score=0.7,
                start=0, end=11, source="gliner",
            ),
        ]
        result = merge_entities(entities, text)
        assert len(result) == 1
        # 1 - (0.1 * 0.15 * 0.3) = 1 - 0.0045 = 0.9955
        assert result[0].score == pytest.approx(0.9955)

    def test_combined_score_always_higher(self) -> None:
        text = "Test entity hier"
        entities = [
            DetectedEntity(
                word="Test entity", entity_group="PER", score=0.6,
                start=0, end=11, source="pii",
            ),
            DetectedEntity(
                word="Test entity", entity_group="PER", score=0.5,
                start=0, end=11, source="org",
            ),
        ]
        result = merge_entities(entities, text)
        max_individual = max(e.score for e in entities)
        assert result[0].score > max_individual


class TestEntityGroupResolution:
    """Test that entity_group is taken from the highest-scoring source."""

    def test_highest_score_wins(self) -> None:
        text = "Wien ist schoen"
        entities = [
            DetectedEntity(
                word="Wien", entity_group="LOC", score=0.95,
                start=0, end=4, source="org",
            ),
            DetectedEntity(
                word="Wien", entity_group="ADRESSE", score=0.7,
                start=0, end=4, source="regex",
            ),
        ]
        result = merge_entities(entities, text)
        assert len(result) == 1
        assert result[0].entity_group == "LOC"

    def test_lower_score_group_not_used(self) -> None:
        text = "Wien ist schoen"
        entities = [
            DetectedEntity(
                word="Wien", entity_group="ADRESSE", score=0.95,
                start=0, end=4, source="regex",
            ),
            DetectedEntity(
                word="Wien", entity_group="LOC", score=0.7,
                start=0, end=4, source="org",
            ),
        ]
        result = merge_entities(entities, text)
        assert result[0].entity_group == "ADRESSE"


class TestSourceTracking:
    """Test that all contributing sources are tracked."""

    def test_single_source(self) -> None:
        text = "Maria hier"
        ent = DetectedEntity(
            word="Maria", entity_group="PER", score=0.9,
            start=0, end=5, source="pii",
        )
        result = merge_entities([ent], text)
        assert result[0].source == "pii"
        assert result[0].sources == ("pii",)

    def test_ensemble_source_label(self) -> None:
        text = "Maria hier"
        entities = [
            DetectedEntity(
                word="Maria", entity_group="PER", score=0.9,
                start=0, end=5, source="pii",
            ),
            DetectedEntity(
                word="Maria", entity_group="PER", score=0.8,
                start=0, end=5, source="org",
            ),
        ]
        result = merge_entities(entities, text)
        assert result[0].source == "ensemble"
        assert result[0].sources == ("pii", "org")

    def test_deduplicated_sources(self) -> None:
        text = "Maria hier"
        entities = [
            DetectedEntity(
                word="Maria", entity_group="PER", score=0.9,
                start=0, end=5, source="pii",
            ),
            DetectedEntity(
                word="Maria", entity_group="PER", score=0.85,
                start=0, end=5, source="pii",
            ),
        ]
        result = merge_entities(entities, text)
        assert result[0].sources == ("pii",)
        assert result[0].source == "pii"


class TestSpanMerging:
    """Test handling of partially overlapping spans."""

    def test_wider_span_used(self) -> None:
        text = "Maria Huber wohnt hier"
        entities = [
            DetectedEntity(
                word="Maria", entity_group="PER", score=0.8,
                start=0, end=5, source="pii",
            ),
            DetectedEntity(
                word="Maria Huber", entity_group="PER", score=0.9,
                start=0, end=11, source="org",
            ),
        ]
        result = merge_entities(entities, text)
        assert len(result) == 1
        assert result[0].word == "Maria Huber"
        assert result[0].start == 0
        assert result[0].end == 11

    def test_union_span_from_text(self) -> None:
        text = "Musterstraße 12, 1010 Wien hier"
        entities = [
            DetectedEntity(
                word="Musterstraße 12", entity_group="ADRESSE", score=0.9,
                start=0, end=15, source="regex",
            ),
            DetectedEntity(
                word="1010 Wien", entity_group="LOC", score=0.8,
                start=17, end=26, source="org",
            ),
        ]
        result = merge_entities(entities, text)
        # These don't overlap (15 < 17), so they stay separate
        assert len(result) == 2

    def test_partial_overlap_merged(self) -> None:
        text = "Dr. Maria Huber-Schmidt hier"
        entities = [
            DetectedEntity(
                word="Dr. Maria", entity_group="PER", score=0.85,
                start=0, end=9, source="regex",
            ),
            DetectedEntity(
                word="Maria Huber-Schmidt", entity_group="PER", score=0.9,
                start=4, end=23, source="pii",
            ),
        ]
        result = merge_entities(entities, text)
        assert len(result) == 1
        # Union span: 0 to 23
        assert result[0].start == 0
        assert result[0].end == 23
        assert result[0].word == "Dr. Maria Huber-Schmidt"


class TestContextPreservation:
    """Test that context/anomaly fields are preserved through merging."""

    def test_context_preserved(self) -> None:
        text = "Maria hier"
        entities = [
            DetectedEntity(
                word="Maria", entity_group="PER", score=0.8,
                start=0, end=5, source="pii",
            ),
            DetectedEntity(
                word="Maria", entity_group="PER", score=0.7,
                start=0, end=5, source="perplexity",
                context="high perplexity in context",
                anomaly_score=0.6,
            ),
        ]
        result = merge_entities(entities, text)
        assert result[0].context == "high perplexity in context"
        assert result[0].anomaly_score == 0.6
