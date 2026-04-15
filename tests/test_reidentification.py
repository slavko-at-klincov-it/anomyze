"""Tests for the quasi-identifier / re-identification detector."""

from anomyze.config.settings import Settings
from anomyze.pipeline import DetectedEntity
from anomyze.pipeline.reidentification import (
    DEFAULT_WINDOW,
    _estimate_k,
    detect_quasi_identifiers,
)


def _loc(word: str, start: int) -> DetectedEntity:
    return DetectedEntity(
        word=word,
        entity_group="LOC",
        score=0.9,
        start=start,
        end=start + len(word),
        source="org",
    )


def _per(word: str, start: int) -> DetectedEntity:
    return DetectedEntity(
        word=word,
        entity_group="PER",
        score=0.95,
        start=start,
        end=start + len(word),
        source="pii",
    )


class TestKEstimate:
    def test_zero_signals_gives_max_k(self) -> None:
        assert _estimate_k(set()) == 6

    def test_each_extra_signal_shrinks_k(self) -> None:
        assert _estimate_k({"role", "age"}) == 4
        assert _estimate_k({"role", "age", "location"}) == 3
        assert _estimate_k({"role", "age", "location", "gender"}) == 2

    def test_minimum_k_is_one(self) -> None:
        assert _estimate_k({"a", "b", "c", "d", "e", "f", "g"}) == 1


class TestBasicSignals:
    def test_role_plus_age_plus_loc_flagged(self) -> None:
        text = "der Beschwerdeführer aus Graz, geboren 1985"
        existing = [_loc("Graz", text.find("Graz"))]
        result = detect_quasi_identifiers(text, existing, Settings())
        assert any(e.entity_group == "QUASI_ID" for e in result)

    def test_single_signal_no_flag(self) -> None:
        text = "der Beschwerdeführer legte Einspruch ein"
        assert detect_quasi_identifiers(text, [], Settings()) == []

    def test_person_nearby_blocks_flag(self) -> None:
        text = "Maria Gruber aus Graz, geboren 1985"
        existing = [
            _per("Maria Gruber", 0),
            _loc("Graz", text.find("Graz")),
        ]
        assert detect_quasi_identifiers(text, existing, Settings()) == []


class TestProfession:
    def test_profession_plus_location(self) -> None:
        text = "arbeitet als Bäckerin in Graz, geboren 1985"
        existing = [_loc("Graz", text.find("Graz"))]
        result = detect_quasi_identifiers(text, existing, Settings())
        assert any(e.entity_group == "QUASI_ID" for e in result)
        # At least one signal explains the k-estimate in its context
        assert any("k~" in e.context for e in result)


class TestRelationship:
    def test_relationship_signal(self) -> None:
        text = "die Ehefrau des Bürgermeisters von Linz, 45-jährig"
        existing = [_loc("Linz", text.find("Linz"))]
        result = detect_quasi_identifiers(text, existing, Settings())
        assert any(e.entity_group == "QUASI_ID" for e in result)


class TestConfigurableWindow:
    def test_custom_window(self) -> None:
        # Role and age separated by > default 200 chars (240 dots)
        text = (
            "der Beschwerdeführer "
            + "." * 240
            + " geboren 1985"
        )
        # Default 200: signals too far apart → no flag
        assert detect_quasi_identifiers(text, [], Settings()) == []
        # Widened window 500: signals now inside the window → flag fires
        wide = Settings(quasi_id_window=500)
        result = detect_quasi_identifiers(text, [], wide)
        assert any(e.entity_group == "QUASI_ID" for e in result)


class TestContextLayerShim:
    def test_shim_delegates(self) -> None:
        # The old ContextLayer._detect_quasi_identifiers still exists
        # and delegates to the new module — keeps external callers
        # working.
        from unittest.mock import MagicMock

        from anomyze.pipeline.context_layer import ContextLayer
        text = "der Beschwerdeführer aus Graz, geboren 1985"
        existing = [_loc("Graz", text.find("Graz"))]
        layer = ContextLayer()
        result = layer.process(text, existing, MagicMock(side_effect=Exception),
                               Settings())
        quasi = [e for e in result if e.entity_group == "QUASI_ID"]
        assert len(quasi) >= 1


class TestDefaultWindowConstant:
    def test_matches_settings_default(self) -> None:
        # Sanity check: module-level default and Settings default
        # agree, so changing one without the other is caught here.
        assert DEFAULT_WINDOW == Settings().quasi_id_window
