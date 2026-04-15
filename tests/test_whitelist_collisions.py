"""Regression guard: whitelist must not swallow person names that
happen to contain an authority token.

Example collision: "Magistrat Müller" detected by NER as an ORG
variant would be whitelisted — but "Müller" detected as PER must not.
"""

from anomyze.patterns.whitelist import filter_whitelisted, is_whitelisted
from anomyze.pipeline import DetectedEntity


def _ent(word: str, group: str) -> DetectedEntity:
    return DetectedEntity(
        word=word,
        entity_group=group,
        score=0.9,
        start=0,
        end=len(word),
        source="org",
    )


class TestPersonGroupImmune:
    def test_person_named_bmi_not_whitelisted(self) -> None:
        # Even though "BMI" is in AT_AUTHORITIES, a PER entity with
        # that surface string must NOT be whitelisted.
        assert not is_whitelisted(_ent("BMI", group="PER"))

    def test_person_named_asvg_not_whitelisted(self) -> None:
        assert not is_whitelisted(_ent("ASVG", group="PER"))

    def test_person_magistrat_nachname_not_whitelisted(self) -> None:
        # Hypothetical rare surname collision
        assert not is_whitelisted(_ent("Magistrat", group="PER"))


class TestAuthorityAsOrgWhitelisted:
    def test_bmi_as_org(self) -> None:
        assert is_whitelisted(_ent("BMI", group="ORG"))

    def test_magistrat_wien_as_org(self) -> None:
        assert is_whitelisted(_ent("Magistrat Wien", group="ORG"))


class TestFilterPreservesPersonInsideAuthority:
    def test_person_alongside_authority_kept(self) -> None:
        # Pipeline emits two entities for "Bundesministerium für Inneres,
        # Karl Nehammer": the authority as ORG and the person as PER.
        # After filtering, the PER entity survives.
        entities = [
            _ent("Bundesministerium für Inneres", group="ORG"),
            _ent("Karl Nehammer", group="PER"),
        ]
        result = filter_whitelisted(entities)
        kept_words = {e.word for e in result}
        assert "Karl Nehammer" in kept_words
        assert "Bundesministerium für Inneres" not in kept_words
