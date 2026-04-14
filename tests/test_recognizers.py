"""Tests for the Presidio-compatible recognizer layer."""

from anomyze.config.settings import Settings
from anomyze.pipeline.presidio_compat_layer import PresidioCompatLayer
from anomyze.pipeline.recognizers import (
    ATAktenzahlRecognizer,
    ATFirmenbuchRecognizer,
    ATIBANRecognizer,
    ATKFZRecognizer,
    ATPassportRecognizer,
    ATSVNRRecognizer,
    Pattern,
    PatternRecognizer,
)


class TestPatternDataclass:
    """Test the Pattern dataclass."""

    def test_create_pattern(self) -> None:
        p = Pattern(name="test", regex=r"\d+", score=0.7)
        assert p.name == "test"
        assert p.regex == r"\d+"
        assert p.score == 0.7

    def test_pattern_is_frozen(self) -> None:
        p = Pattern(name="test", regex=r"\d+", score=0.7)
        try:
            p.name = "changed"  # type: ignore[misc]
        except Exception:
            return
        raise AssertionError("Pattern should be frozen")


class _DigitRecognizer(PatternRecognizer):
    """Test recognizer that matches sequences of digits."""

    supported_entity = "DIGITS"
    patterns = [Pattern(name="digits", regex=r"\b\d{4,}\b", score=0.6)]
    context = ["nummer", "id"]


class TestPatternRecognizerBase:
    """Test the PatternRecognizer base class."""

    def test_compiles_patterns(self) -> None:
        r = _DigitRecognizer()
        assert len(r._compiled) == 1

    def test_finds_matches(self) -> None:
        r = _DigitRecognizer()
        results = r.analyze("Code 12345 hier")
        assert len(results) == 1
        assert results[0].entity_type == "DIGITS"
        assert results[0].text == "12345"
        assert results[0].score == 0.6
        assert results[0].recognizer_name == "_DigitRecognizer"

    def test_no_match(self) -> None:
        r = _DigitRecognizer()
        assert r.analyze("nur Buchstaben") == []

    def test_short_number_not_matched(self) -> None:
        r = _DigitRecognizer()
        # Pattern requires 4+ digits
        assert r.analyze("123") == []

    def test_context_boost(self) -> None:
        r = _DigitRecognizer()
        # Without context: score 0.6
        without = r.analyze("Code 12345 hier")
        assert without[0].score == 0.6
        # With context "nummer": score 0.6 + 0.2 = 0.8
        with_ctx = r.analyze("Die Nummer 12345 ist falsch")
        assert with_ctx[0].score == 0.8

    def test_context_clamped_to_one(self) -> None:
        class HighBaseRecognizer(PatternRecognizer):
            supported_entity = "TEST"
            patterns = [Pattern(name="t", regex=r"\b\d{4,}\b", score=0.95)]
            context = ["nummer"]
            context_boost = 0.5

        r = HighBaseRecognizer()
        result = r.analyze("Die Nummer 12345")
        # 0.95 + 0.5 = 1.45 → clamped to 1.0
        assert result[0].score == 1.0

    def test_validation_can_filter_matches(self) -> None:
        class EvenOnlyRecognizer(PatternRecognizer):
            supported_entity = "EVEN"
            patterns = [Pattern(name="e", regex=r"\b\d{4,}\b", score=0.7)]

            def _is_valid_match(self, matched, full_text, start, end):
                return int(matched) % 2 == 0

        r = EvenOnlyRecognizer()
        results = r.analyze("Numbers: 1234 and 1235")
        assert len(results) == 1
        assert results[0].text == "1234"


class TestATSVNRRecognizer:
    """Test Austrian SVNR recognition."""

    def test_svnr_with_space(self) -> None:
        r = ATSVNRRecognizer()
        results = r.analyze("SVNR: 1234 010180")
        assert len(results) == 1
        assert results[0].text == "1234 010180"

    def test_svnr_invalid_month_rejected(self) -> None:
        r = ATSVNRRecognizer()
        # Month 13 is invalid
        results = r.analyze("1234 011380")
        assert results == []

    def test_svnr_invalid_day_rejected(self) -> None:
        r = ATSVNRRecognizer()
        # Day 32 is invalid
        results = r.analyze("1234 320180")
        assert results == []

    def test_svnr_context_boost(self) -> None:
        r = ATSVNRRecognizer()
        without = r.analyze("Nummer: 1234 010180")
        with_ctx = r.analyze("Sozialversicherung: 1234 010180")
        assert with_ctx[0].score > without[0].score


class TestATIBANRecognizer:
    """Test Austrian IBAN recognition."""

    def test_iban_with_spaces(self) -> None:
        r = ATIBANRecognizer()
        results = r.analyze("Konto: AT61 1904 3002 3457 3201")
        assert len(results) == 1

    def test_iban_without_spaces(self) -> None:
        r = ATIBANRecognizer()
        results = r.analyze("Konto: AT611904300234573201")
        assert len(results) == 1


class TestATKFZRecognizer:
    """Test Austrian license plate recognition."""

    def test_wien_plate(self) -> None:
        r = ATKFZRecognizer()
        results = r.analyze("Auto: W-12345 AB")
        assert len(results) == 1

    def test_steiermark_plate(self) -> None:
        r = ATKFZRecognizer()
        results = r.analyze("ST 999 X")
        assert len(results) == 1

    def test_no_kfz(self) -> None:
        r = ATKFZRecognizer()
        # XXX is not a valid Bundesland code
        assert r.analyze("XXX 12345 AB") == []


class TestATFirmenbuchRecognizer:
    """Test Austrian Firmenbuchnummer recognition."""

    def test_basic_fn(self) -> None:
        r = ATFirmenbuchRecognizer()
        results = r.analyze("FN 12345a")
        assert len(results) == 1
        assert results[0].text == "FN 12345a"

    def test_fn_without_space(self) -> None:
        r = ATFirmenbuchRecognizer()
        results = r.analyze("FN12345a")
        assert len(results) == 1

    def test_fn_context_boost(self) -> None:
        r = ATFirmenbuchRecognizer()
        without = r.analyze("Eingabe: FN 12345a")
        with_ctx = r.analyze("Firmenbuch: FN 12345a")
        assert with_ctx[0].score > without[0].score


class TestATPassportRecognizer:
    """Test Austrian passport recognition."""

    def test_passport_low_score_without_context(self) -> None:
        r = ATPassportRecognizer()
        results = r.analyze("Code: P1234567")
        assert len(results) == 1
        assert results[0].score < 0.7  # Low without context

    def test_passport_high_score_with_context(self) -> None:
        r = ATPassportRecognizer()
        results = r.analyze("Reisepass: P1234567")
        assert results[0].score > 0.65


class TestATAktenzahlRecognizer:
    """Test Austrian Aktenzahl/Geschäftszahl recognition."""

    def test_gz_format(self) -> None:
        r = ATAktenzahlRecognizer()
        results = r.analyze("GZ 2024-1234")
        assert len(results) >= 1

    def test_az_format(self) -> None:
        r = ATAktenzahlRecognizer()
        results = r.analyze("Az. BMI-1/123")
        assert len(results) >= 1

    def test_zl_format(self) -> None:
        r = ATAktenzahlRecognizer()
        results = r.analyze("Zl 567/2023")
        assert len(results) >= 1


class TestPresidioCompatLayer:
    """Test the PresidioCompatLayer integration."""

    def test_layer_runs_all_recognizers(self) -> None:
        layer = PresidioCompatLayer()
        text = "FN 12345a, IBAN AT61 1904 3002 3457 3201"
        entities = layer.process(text, Settings(presidio_threshold=0.4))
        groups = {e.entity_group for e in entities}
        assert "FIRMENBUCH" in groups
        assert "IBAN" in groups

    def test_threshold_filter(self) -> None:
        layer = PresidioCompatLayer()
        # Passport pattern alone has score 0.5, so threshold 0.6 filters it out
        entities = layer.process("Code: P1234567", Settings(presidio_threshold=0.6))
        assert all(e.entity_group != "REISEPASS" for e in entities)

    def test_returns_detected_entity(self) -> None:
        layer = PresidioCompatLayer()
        entities = layer.process("FN 12345a", Settings(presidio_threshold=0.4))
        assert len(entities) == 1
        e = entities[0]
        assert e.word == "FN 12345a"
        assert e.entity_group == "FIRMENBUCH"
        assert e.source == "presidio_compat"

    def test_custom_recognizer_set(self) -> None:
        layer = PresidioCompatLayer(recognizers=[ATFirmenbuchRecognizer()])
        # Only Firmenbuch detected; IBAN ignored
        entities = layer.process(
            "FN 12345a, IBAN AT61 1904 3002 3457 3201",
            Settings(presidio_threshold=0.4),
        )
        assert len(entities) == 1
        assert entities[0].entity_group == "FIRMENBUCH"

    def test_empty_text(self) -> None:
        layer = PresidioCompatLayer()
        assert layer.process("", Settings()) == []
