"""Tests for ICD-10 recognition and DSGVO Art. 9 channel behaviour."""

from anomyze.channels.ifg import IFGChannel
from anomyze.channels.kapa import KAPAChannel
from anomyze.config.settings import Settings
from anomyze.patterns.healthcare import is_icd10_code
from anomyze.pipeline import DetectedEntity
from anomyze.pipeline.recognizers import ATICD10Recognizer


class TestICD10Validation:
    def test_valid_code(self) -> None:
        assert is_icd10_code("F32.1")

    def test_valid_code_without_subcategory(self) -> None:
        assert is_icd10_code("I10")

    def test_out_of_range(self) -> None:
        # C98 does not exist (C-chapter ends at C97)
        assert not is_icd10_code("C98")

    def test_wrong_letter_prefix(self) -> None:
        # U is kept because of U07.x (COVID-19). O-chapter exists.
        # Test for a letter range that simply doesn't exist in ICD-10:
        # there is no chapter starting with lowercase or with digits.
        assert not is_icd10_code("A100")  # too many digits
        assert not is_icd10_code("A1")    # too few digits

    def test_empty(self) -> None:
        assert not is_icd10_code("")


class TestATICD10Recognizer:
    def test_requires_context(self) -> None:
        r = ATICD10Recognizer()
        # No medical context → no match, even though "A01" is a valid code
        assert r.analyze("Raum A01 ist frei.") == []

    def test_valid_with_context(self) -> None:
        r = ATICD10Recognizer()
        results = r.analyze("Diagnose: F32.1 (mittelgradige depressive Episode)")
        assert len(results) == 1
        assert results[0].entity_type == "HEALTH_DIAGNOSIS"
        assert results[0].text == "F32.1"

    def test_invalid_code_rejected(self) -> None:
        r = ATICD10Recognizer()
        # C99 is outside the C-chapter range even with context
        results = r.analyze("Diagnose C99 wurde gestellt")
        assert results == []


class TestIFGArt9Aggregation:
    def test_art9_collapses_to_besondere_kategorie(self) -> None:
        text = "Diagnose F32.1 und I10 festgestellt"
        entities = [
            DetectedEntity(word="F32.1", entity_group="HEALTH_DIAGNOSIS",
                           score=0.9, start=9, end=14, source="presidio_compat"),
            DetectedEntity(word="I10", entity_group="HEALTH_DIAGNOSIS",
                           score=0.9, start=19, end=22, source="presidio_compat"),
        ]
        result = IFGChannel().format_output(text, entities, Settings())
        assert "[GESCHWÄRZT:BESONDERE_KATEGORIE]" in result.text
        # Redaction protocol uses the collapsed category
        assert len(result.redaction_protocol) == 1
        assert result.redaction_protocol[0].category == "BESONDERE_KATEGORIE"
        assert result.redaction_protocol[0].count == 2

    def test_normal_categories_preserved(self) -> None:
        text = "Maria Gruber, Diagnose F32.1"
        entities = [
            DetectedEntity(word="Maria Gruber", entity_group="PER",
                           score=0.9, start=0, end=12, source="pii"),
            DetectedEntity(word="F32.1", entity_group="HEALTH_DIAGNOSIS",
                           score=0.9, start=23, end=28, source="presidio_compat"),
        ]
        result = IFGChannel().format_output(text, entities, Settings())
        categories = {e.category for e in result.redaction_protocol}
        assert "PERSON" in categories
        assert "BESONDERE_KATEGORIE" in categories


class TestKAPAArt9AlwaysFlagged:
    def test_art9_flagged_even_with_high_confidence(self) -> None:
        text = "Diagnose: F32.1"
        entities = [
            DetectedEntity(word="F32.1", entity_group="HEALTH_DIAGNOSIS",
                           score=0.99, start=10, end=15, source="presidio_compat"),
        ]
        result = KAPAChannel().format_output(text, entities, Settings())
        assert len(result.flagged_for_review) == 1
        assert "PRÜFEN" in result.flagged_for_review[0]
        assert result.audit_entries[0].action == "flagged_for_review"

    def test_non_art9_follows_review_threshold(self) -> None:
        text = "Maria Gruber"
        entities = [
            DetectedEntity(word="Maria Gruber", entity_group="PER",
                           score=0.99, start=0, end=12, source="pii"),
        ]
        settings = Settings(kapa_review_threshold=0.85)
        result = KAPAChannel().format_output(text, entities, settings)
        # High-confidence non-Art.9 entity → anonymized, not flagged
        assert result.flagged_for_review == []
        assert result.audit_entries[0].action == "anonymized"
