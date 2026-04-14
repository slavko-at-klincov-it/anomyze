"""Tests for entity resolution."""

from anomyze.pipeline import DetectedEntity
from anomyze.pipeline.entity_resolver import canonical_key, resolve_entities


def _per(word: str, start: int = 0, end: int = 0) -> DetectedEntity:
    return DetectedEntity(
        word=word, entity_group='PER', score=0.9,
        start=start, end=end or len(word), source='pii',
    )


def _org(word: str, start: int = 0, end: int = 0) -> DetectedEntity:
    return DetectedEntity(
        word=word, entity_group='ORG', score=0.9,
        start=start, end=end or len(word), source='org',
    )


def _entity(word: str, group: str, start: int = 0, end: int = 0) -> DetectedEntity:
    return DetectedEntity(
        word=word, entity_group=group, score=0.9,
        start=start, end=end or len(word), source='regex',
    )


class TestCanonicalKeyPER:
    """Test canonical_key for PER entities."""

    def test_simple_name(self) -> None:
        assert canonical_key(_per("Maria Huber")) == "maria huber"

    def test_dr_title_stripped(self) -> None:
        assert canonical_key(_per("Dr. Maria Huber")) == "maria huber"

    def test_mag_title_stripped(self) -> None:
        assert canonical_key(_per("Mag. Maria Huber")) == "maria huber"

    def test_mag_a_female_title(self) -> None:
        assert canonical_key(_per("Mag.a Maria Huber")) == "maria huber"

    def test_prof_stripped(self) -> None:
        assert canonical_key(_per("Prof. Karl Müller")) == "karl müller"

    def test_herr_frau_stripped(self) -> None:
        assert canonical_key(_per("Herr Huber")) == "huber"
        assert canonical_key(_per("Frau Huber")) == "huber"

    def test_multiple_titles(self) -> None:
        assert canonical_key(_per("Dr. Mag. Maria Huber")) == "maria huber"

    def test_article_stripped(self) -> None:
        assert canonical_key(_per("der Karl")) == "karl"

    def test_von_preserved(self) -> None:
        # "von" is part of legal name, must NOT be stripped
        assert canonical_key(_per("Karl von Habsburg")) == "karl von habsburg"

    def test_hyphenated_name_preserved(self) -> None:
        assert canonical_key(_per("Maria Müller-Schmidt")) == "maria müller-schmidt"

    def test_only_title_falls_back(self) -> None:
        # If everything is stripped, fall back to lowercase original
        assert canonical_key(_per("Dr.")) == "dr."


class TestCanonicalKeyORG:
    """Test canonical_key for ORG entities."""

    def test_simple_org(self) -> None:
        assert canonical_key(_org("Anomyze")) == "anomyze"

    def test_gmbh_stripped(self) -> None:
        assert canonical_key(_org("XYZ GmbH")) == "xyz"

    def test_ag_stripped(self) -> None:
        assert canonical_key(_org("Acme AG")) == "acme"

    def test_kg_stripped(self) -> None:
        assert canonical_key(_org("Foo KG")) == "foo"

    def test_firma_stripped(self) -> None:
        assert canonical_key(_org("Firma XYZ")) == "xyz"

    def test_article_and_suffix(self) -> None:
        assert canonical_key(_org("die XYZ GmbH")) == "xyz"

    def test_complex_legal_form(self) -> None:
        assert canonical_key(_org("XYZ GmbH & Co. KG")) == "xyz"

    def test_org_detected_group(self) -> None:
        ent = _entity("Acme AG", "ORG_DETECTED")
        assert canonical_key(ent) == "acme"


class TestCanonicalKeyOther:
    """Test canonical_key for non-PER/ORG entity types."""

    def test_email_lowercase(self) -> None:
        ent = _entity("Maria@Example.AT", "EMAIL")
        assert canonical_key(ent) == "maria@example.at"

    def test_iban_lowercase(self) -> None:
        ent = _entity("AT61 1904 3002 3457 3201", "IBAN")
        assert canonical_key(ent) == "at61 1904 3002 3457 3201"

    def test_loc_lowercase(self) -> None:
        ent = _entity("Wien", "LOC")
        assert canonical_key(ent) == "wien"

    def test_empty_word(self) -> None:
        assert canonical_key(_per("")) == ""


class TestResolveEntitiesBasic:
    """Test basic resolve_entities behavior."""

    def test_empty_list(self) -> None:
        assert resolve_entities([]) == []

    def test_single_entity(self) -> None:
        assert resolve_entities([_per("Maria Huber")]) == ["maria huber"]

    def test_distinct_entities(self) -> None:
        ents = [_per("Maria Huber"), _per("Karl Schmidt")]
        keys = resolve_entities(ents)
        assert keys == ["maria huber", "karl schmidt"]

    def test_identical_entities(self) -> None:
        ents = [_per("Maria Huber"), _per("Maria Huber")]
        keys = resolve_entities(ents)
        assert keys[0] == keys[1] == "maria huber"


class TestResolveEntitiesPER:
    """Test PER-specific resolution (title stripping, partial matching)."""

    def test_title_variations_match(self) -> None:
        ents = [
            _per("Dr. Maria Huber"),
            _per("Maria Huber"),
            _per("Frau Huber"),
        ]
        keys = resolve_entities(ents)
        # All three resolve to the same canonical key
        assert keys[0] == keys[1] == keys[2] == "maria huber"

    def test_partial_first_name_unambiguous(self) -> None:
        # "Maria" links to "Maria Huber" because it's the only candidate
        ents = [_per("Maria Huber"), _per("Maria")]
        keys = resolve_entities(ents)
        assert keys[0] == keys[1] == "maria huber"

    def test_partial_last_name_unambiguous(self) -> None:
        # "Huber" links to "Maria Huber" because it's the only candidate
        ents = [_per("Maria Huber"), _per("Huber")]
        keys = resolve_entities(ents)
        assert keys[0] == keys[1] == "maria huber"

    def test_ambiguous_partial_not_linked(self) -> None:
        # "Maria" cannot be unambiguously linked when both
        # "Maria Huber" and "Maria Schmidt" are present
        ents = [_per("Maria Huber"), _per("Maria Schmidt"), _per("Maria")]
        keys = resolve_entities(ents)
        assert keys[0] == "maria huber"
        assert keys[1] == "maria schmidt"
        assert keys[2] == "maria"  # NOT linked

    def test_partial_not_in_full_names_unchanged(self) -> None:
        # "Klaus" doesn't appear in any full name; stays as "klaus"
        ents = [_per("Maria Huber"), _per("Klaus")]
        keys = resolve_entities(ents)
        assert keys[0] == "maria huber"
        assert keys[1] == "klaus"


class TestResolveEntitiesORG:
    """Test ORG-specific resolution."""

    def test_org_variants_match(self) -> None:
        ents = [
            _org("XYZ GmbH"),
            _org("die XYZ GmbH"),
            _org("Firma XYZ"),
        ]
        keys = resolve_entities(ents)
        assert keys[0] == keys[1] == keys[2] == "xyz"


class TestResolveEntitiesCrossType:
    """Test that different entity types don't cross-link."""

    def test_per_and_loc_with_same_word(self) -> None:
        # "Wien" as a person name vs "Wien" as a location must remain separate.
        # canonical_key for both is "wien" but they have different entity groups.
        ents = [_per("Wien"), _entity("Wien", "LOC")]
        keys = resolve_entities(ents)
        # Both produce the same canonical key string
        # (the channel uses (type, key) tuples to distinguish them)
        assert keys[0] == keys[1] == "wien"

    def test_per_partial_does_not_match_org(self) -> None:
        # "Schmidt" should not link to "Schmidt GmbH" (ORG)
        ents = [_org("Schmidt GmbH"), _per("Schmidt")]
        keys = resolve_entities(ents)
        assert keys[0] == "schmidt"
        assert keys[1] == "schmidt"  # Stays as single token (no PER full name)
