"""
Unit tests for PipelineOrchestrator with mocked ML models.

Covers paths that are not well-exercised by the higher-level API
and adversarial tests: settings toggles (individual detection layers
off), the backwards-compatible anonymize() function, and the
detect()-only entry point.
"""

from unittest.mock import MagicMock

import pytest

from anomyze.config.settings import Settings
from anomyze.pipeline import DetectedEntity
from anomyze.pipeline.orchestrator import PipelineOrchestrator, anonymize


def _mock_orch(**overrides) -> PipelineOrchestrator:
    settings = Settings(
        use_anomaly_detection=False,
        use_gliner=False,
        device="cpu",
        **overrides,
    )
    o = PipelineOrchestrator(settings)
    o.model_manager._pii_pipeline = MagicMock(return_value=[])
    o.model_manager._org_pipeline = MagicMock(return_value=[])
    o.model_manager._mlm_pipeline = MagicMock(return_value=[])
    o.model_manager._device = "cpu"
    o.model_manager._device_name = "CPU [test]"
    return o


class TestDetectEntryPoint:
    """detect() returns entities without channel formatting."""

    def test_detect_returns_tuple(self) -> None:
        o = _mock_orch()
        text, entities = o.detect("maria@example.at")
        assert isinstance(text, str)
        assert isinstance(entities, list)

    def test_detect_finds_email(self) -> None:
        o = _mock_orch()
        _, entities = o.detect("Mail: maria@example.at")
        assert any(e.entity_group == "EMAIL" for e in entities)

    def test_detect_empty_text(self) -> None:
        o = _mock_orch()
        text, entities = o.detect("")
        assert text == ""
        assert entities == []

    def test_detect_sorted_by_position(self) -> None:
        o = _mock_orch()
        _, entities = o.detect(
            "Mail maria@example.at Konto AT61 1904 3002 3457 3201"
        )
        starts = [e.start for e in entities]
        assert starts == sorted(starts)


class TestSettingsToggles:
    """Individual detection-layer toggles behave correctly."""

    def test_regex_fallback_off(self) -> None:
        o = _mock_orch(use_regex_fallback=False)
        _, entities = o.detect("Mail maria@example.at IBAN AT61 1904 3002 3457 3201")
        # With regex off and mocked NER/presidio email handling, regex-only
        # signals (IBAN, email) from the regex layer are not produced.
        # But presidio_compat still runs and may still catch IBAN.
        iban_sources = [e.source for e in entities if e.entity_group == "IBAN"]
        assert "regex" not in iban_sources

    def test_presidio_compat_off(self) -> None:
        o = _mock_orch(use_presidio_compat=False)
        _, entities = o.detect("FN 12345a ist eine Firmenbuchnummer")
        # FIRMENBUCH is a Presidio-compat-only entity type
        assert not any(e.entity_group == "FIRMENBUCH" for e in entities)

    def test_adversarial_normalization_off(self) -> None:
        o = _mock_orch(use_adversarial_normalization=False)
        # Zero-width space in IBAN should cause regex miss when normalizer off
        _, entities = o.detect("IBAN AT\u200b61 1904 3002 3457 3201")
        iban_words = [e.word for e in entities if e.entity_group == "IBAN"]
        # Regex can't see the full IBAN through the zero-width char
        assert not iban_words or "\u200b" not in iban_words[0]

    def test_encoding_fix_off(self) -> None:
        o = _mock_orch(fix_encoding=False)
        # With encoding fix off, common broken characters stay broken
        _, entities = o.detect("\u00a0maria@example.at")
        # But detection should still work (NBSP doesn't break email regex)
        assert any(e.entity_group == "EMAIL" for e in entities)


class TestQualityCheckToggle:
    """run_quality_check setting controls whether a report is attached."""

    def test_quality_check_on(self) -> None:
        o = _mock_orch(run_quality_check=True)
        result = o.process("Mail maria@example.at", channel="govgpt")
        assert result.quality_report is not None

    def test_quality_check_off(self) -> None:
        o = _mock_orch(run_quality_check=False)
        result = o.process("Mail maria@example.at", channel="govgpt")
        assert result.quality_report is None


class TestAnonymizeBackwardCompat:
    """Backwards-compatible anonymize() function."""

    def test_anonymize_basic(self) -> None:
        settings = Settings(
            use_anomaly_detection=False,
            use_gliner=False,
            use_presidio_compat=False,
            device="cpu",
        )
        result = anonymize(
            "Mail maria@example.at",
            pii_pipeline=MagicMock(return_value=[]),
            org_pipeline=MagicMock(return_value=[]),
            mlm_pipeline=MagicMock(return_value=[]),
            settings=settings,
        )
        assert "[EMAIL_1]" in result.text
        assert result.mapping

    def test_anonymize_empty_entities(self) -> None:
        settings = Settings(
            use_anomaly_detection=False,
            use_gliner=False,
            device="cpu",
        )
        result = anonymize(
            "Nur Klartext ohne PII",
            pii_pipeline=MagicMock(return_value=[]),
            org_pipeline=MagicMock(return_value=[]),
            mlm_pipeline=MagicMock(return_value=[]),
            settings=settings,
        )
        assert result.entity_count == 0
        assert result.mapping == {}


class TestUnknownChannelRaises:
    """Unknown channel names should raise ValueError."""

    def test_unknown_channel(self) -> None:
        o = _mock_orch()
        with pytest.raises(ValueError, match="Unknown channel"):
            o.process("text", channel="nonsense")


class TestDetectedEntityContract:
    """Invariants on the entities returned by detect()."""

    def test_entities_have_required_fields(self) -> None:
        o = _mock_orch()
        _, entities = o.detect("Mail maria@example.at")
        for e in entities:
            assert isinstance(e, DetectedEntity)
            assert e.word
            assert e.entity_group
            assert 0.0 <= e.score <= 1.0
            assert 0 <= e.start < e.end
            assert e.source

    def test_spans_within_text(self) -> None:
        o = _mock_orch()
        text, entities = o.detect("Mail maria@example.at Ende")
        for e in entities:
            assert e.end <= len(text)
            # The span should match the word (ignoring merge effects on the
            # text itself, which isn't modified by detect())
            assert text[e.start:e.end] == e.word or e.source == "ensemble"
