"""
Adversarial tests against the full anonymization pipeline.

Exercises Unicode obfuscation, zero-width tricks, boundary conditions,
dense PII, and cross-entity overlaps end-to-end. ML models are mocked
so these tests run quickly (<1s) and focus on the deterministic
layers: normalizer, regex, Presidio-compat, ensemble, entity resolver,
channels, and quality check.
"""

from unittest.mock import MagicMock

import pytest

from anomyze.config.settings import Settings
from anomyze.pipeline.orchestrator import PipelineOrchestrator


@pytest.fixture
def orch() -> PipelineOrchestrator:
    """Orchestrator with ML pipelines mocked to return no entities."""
    settings = Settings(
        use_anomaly_detection=False,
        use_gliner=False,
        device="cpu",
    )
    o = PipelineOrchestrator(settings)
    o.model_manager._pii_pipeline = MagicMock(return_value=[])
    o.model_manager._org_pipeline = MagicMock(return_value=[])
    o.model_manager._mlm_pipeline = MagicMock(return_value=[])
    o.model_manager._device = "cpu"
    o.model_manager._device_name = "CPU [test]"
    return o


class TestUnicodeHomoglyphAttacks:
    """PII obscured by Cyrillic/Greek lookalikes must still be detected."""

    def test_cyrillic_in_iban_defeated_by_normalizer(self, orch) -> None:
        # "АТ" with Cyrillic A (U+0410) and T (U+0422) instead of Latin A, T
        text = "Konto: \u0410\u042261 1904 3002 3457 3201"
        result = orch.process(text, channel="govgpt")
        # Normalizer maps Cyrillic → Latin, then IBAN regex matches
        assert "[IBAN_1]" in result.text
        assert "1904 3002 3457 3201" not in result.text

    def test_fullwidth_iban_digits(self, orch) -> None:
        # Fullwidth digits ０-９ normalize to ASCII
        text = "AT\uff16\uff11 \uff11\uff19\uff10\uff14 3002 3457 3201"
        result = orch.process(text, channel="govgpt")
        assert "[IBAN_1]" in result.text

    def test_mixed_cyrillic_latin_email(self, orch) -> None:
        # "example" with Cyrillic e (U+0435)
        text = "Mail: maria@\u0435xample.at"
        result = orch.process(text, channel="govgpt")
        assert "[EMAIL_1]" in result.text
        assert "@" not in result.text.replace("[EMAIL_1]", "")


class TestZeroWidthAttacks:
    """Zero-width chars placed inside PII must not evade detection."""

    def test_zero_width_in_iban(self, orch) -> None:
        # Zero-width space between AT and digits
        text = "AT\u200b61 1904 3002 3457 3201"
        result = orch.process(text, channel="govgpt")
        assert "[IBAN_1]" in result.text

    def test_zero_width_in_email(self, orch) -> None:
        text = "Mail: maria\u200b@exa\u200bmple\u200b.at"
        result = orch.process(text, channel="govgpt")
        assert "[EMAIL_1]" in result.text

    def test_soft_hyphen_in_svnr(self, orch) -> None:
        # Soft hyphen in the middle of SVNR
        text = "SVNR: 1234\u00ad 010180"
        result = orch.process(text, channel="govgpt")
        assert "[SVNR_1]" in result.text

    def test_bom_prefix(self, orch) -> None:
        # UTF-8 BOM at start
        text = "\ufeffKontakt: maria@example.at"
        result = orch.process(text, channel="govgpt")
        assert "[EMAIL_1]" in result.text


class TestBoundaryConditions:
    """PII at text boundaries must still be detected."""

    def test_pii_at_very_start(self, orch) -> None:
        text = "maria@example.at ist die Mail"
        result = orch.process(text, channel="govgpt")
        assert "[EMAIL_1]" in result.text

    def test_pii_at_very_end(self, orch) -> None:
        text = "Mail ist: maria@example.at"
        result = orch.process(text, channel="govgpt")
        assert "[EMAIL_1]" in result.text
        assert "maria@example.at" not in result.text

    def test_empty_text(self, orch) -> None:
        result = orch.process("", channel="govgpt")
        assert result.text == ""
        assert result.entity_count == 0

    def test_whitespace_only(self, orch) -> None:
        result = orch.process("   \n\t  ", channel="govgpt")
        assert result.entity_count == 0

    def test_single_char(self, orch) -> None:
        result = orch.process("x", channel="govgpt")
        assert result.text == "x"
        assert result.entity_count == 0


class TestDensePII:
    """Many PII entities in close proximity should all be detected."""

    def test_multiple_distinct_pii(self, orch) -> None:
        text = (
            "Kontakt: maria@example.at, "
            "IBAN AT61 1904 3002 3457 3201, "
            "SVNR 1234 010180, Tel: +43 664 1234567"
        )
        result = orch.process(text, channel="govgpt")
        # All four PII categories anonymized
        assert "[EMAIL_1]" in result.text
        assert "[IBAN_1]" in result.text
        assert "[SVNR_1]" in result.text
        assert "[TELEFON_1]" in result.text

    def test_repeated_same_entity_same_placeholder(self, orch) -> None:
        text = "maria@example.at schrieb. Antwort an maria@example.at"
        result = orch.process(text, channel="govgpt")
        # Same email → same placeholder; appears exactly twice
        assert result.text.count("[EMAIL_1]") == 2
        assert "[EMAIL_2]" not in result.text


class TestQualityReportIntegration:
    """Quality report should reflect actual anonymization outcome."""

    def test_clean_output_passes_quality_check(self, orch) -> None:
        text = "Heute war das Wetter schön."
        result = orch.process(text, channel="govgpt")
        assert result.quality_report is not None
        assert result.quality_report.passed
        assert result.quality_report.leak_count == 0

    def test_successful_anonymization_passes_quality_check(self, orch) -> None:
        text = "Konto: AT61 1904 3002 3457 3201 von maria@example.at"
        result = orch.process(text, channel="govgpt")
        # After anonymization, no raw IBAN or email should remain
        assert result.quality_report is not None
        assert result.quality_report.leak_count == 0


class TestChannelConsistency:
    """All channels must produce consistent anonymization of the same input."""

    def test_same_input_all_channels(self, orch) -> None:
        text = "Konto: AT61 1904 3002 3457 3201 von maria@example.at"
        g = orch.process(text, channel="govgpt")
        i = orch.process(text, channel="ifg")
        k = orch.process(text, channel="kapa")

        # All three redact the IBAN and email
        for r in (g, i, k):
            assert "1904 3002" not in r.text
            assert "maria@example.at" not in r.text


class TestPerformanceSanity:
    """Pipeline should handle reasonable sizes without errors."""

    def test_long_text_no_crash(self, orch) -> None:
        # 10 KB of repeated PII
        text = "Kontakt maria@example.at mit IBAN AT61 1904 3002 3457 3201. " * 100
        result = orch.process(text, channel="govgpt")
        # Should anonymize all occurrences to the same two placeholders
        assert "[EMAIL_1]" in result.text
        assert "[IBAN_1]" in result.text
        # No other distinct placeholders for these types
        assert "[EMAIL_2]" not in result.text
        assert "[IBAN_2]" not in result.text

    def test_no_pii_long_text(self, orch) -> None:
        text = "Heute scheint die Sonne. " * 500
        result = orch.process(text, channel="govgpt")
        assert result.entity_count == 0
