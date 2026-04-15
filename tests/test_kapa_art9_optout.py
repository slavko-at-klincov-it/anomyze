"""Tests for the KAPA Art.9 always-flag opt-out."""

from anomyze.channels.kapa import KAPAChannel
from anomyze.config.settings import Settings
from anomyze.pipeline import DetectedEntity


def _art9_entity(score: float = 0.99) -> DetectedEntity:
    return DetectedEntity(
        word="F32.1",
        entity_group="HEALTH_DIAGNOSIS",
        score=score,
        start=10,
        end=15,
        source="presidio_compat",
    )


def _normal_entity(score: float = 0.99) -> DetectedEntity:
    return DetectedEntity(
        word="Maria Gruber",
        entity_group="PER",
        score=score,
        start=0,
        end=12,
        source="pii",
    )


class TestArt9DefaultBehaviour:
    def test_high_score_art9_flagged_by_default(self) -> None:
        result = KAPAChannel().format_output(
            "Diagnose: F32.1",
            [_art9_entity(0.99)],
            Settings(),
        )
        assert len(result.flagged_for_review) == 1
        assert "PRÜFEN" in result.flagged_for_review[0]
        assert result.audit_entries[0].action == "flagged_for_review"

    def test_high_score_non_art9_anonymised_by_default(self) -> None:
        result = KAPAChannel().format_output(
            "Maria Gruber",
            [_normal_entity(0.99)],
            Settings(),
        )
        assert result.flagged_for_review == []
        assert result.audit_entries[0].action == "anonymized"


class TestArt9OptOut:
    def test_high_score_art9_anonymised_when_opt_out(self) -> None:
        result = KAPAChannel().format_output(
            "Diagnose: F32.1",
            [_art9_entity(0.99)],
            Settings(always_review_art9=False),
        )
        assert result.flagged_for_review == []
        assert result.audit_entries[0].action == "anonymized"

    def test_low_score_art9_still_flagged_when_opt_out(self) -> None:
        result = KAPAChannel().format_output(
            "Diagnose: F32.1",
            [_art9_entity(0.5)],
            Settings(always_review_art9=False, kapa_review_threshold=0.85),
        )
        assert len(result.flagged_for_review) == 1
        assert result.audit_entries[0].action == "flagged_for_review"


class TestPlaceholderActionInvariant:
    """Invariant: placeholder uses [PRÜFEN: prefix iff action=flagged_for_review.

    Mirrors the comment in kapa.py.
    """

    def test_invariant_holds_default(self) -> None:
        for score in (0.5, 0.99):
            result = KAPAChannel().format_output(
                "Diagnose: F32.1",
                [_art9_entity(score)],
                Settings(),
            )
            placeholder = result.audit_entries[0].placeholder
            action = result.audit_entries[0].action
            assert ("PRÜFEN" in placeholder) == (action == "flagged_for_review")

    def test_invariant_holds_opt_out(self) -> None:
        for score in (0.5, 0.99):
            result = KAPAChannel().format_output(
                "Diagnose: F32.1",
                [_art9_entity(score)],
                Settings(always_review_art9=False),
            )
            placeholder = result.audit_entries[0].placeholder
            action = result.audit_entries[0].action
            assert ("PRÜFEN" in placeholder) == (action == "flagged_for_review")
