"""Tests for Austrian name data resources."""

from anomyze.patterns.at_names import (
    AT_FIRST_NAMES,
    AT_LAST_NAMES,
    is_at_firstname,
    is_at_lastname,
    is_at_name,
    phonetic_match_firstname,
    phonetic_match_lastname,
)


class TestFirstNameLookup:
    """Test first-name lookups."""

    def test_known_firstname(self) -> None:
        assert is_at_firstname("Maria")
        assert is_at_firstname("Karl")
        assert is_at_firstname("Johann")

    def test_case_insensitive(self) -> None:
        assert is_at_firstname("maria")
        assert is_at_firstname("KARL")

    def test_whitespace_stripped(self) -> None:
        assert is_at_firstname("  Maria  ")

    def test_unknown_firstname(self) -> None:
        assert not is_at_firstname("Xerxes")

    def test_empty(self) -> None:
        assert not is_at_firstname("")


class TestLastNameLookup:
    """Test last-name lookups."""

    def test_known_lastname(self) -> None:
        assert is_at_lastname("Huber")
        assert is_at_lastname("Gruber")
        assert is_at_lastname("Müller")

    def test_case_insensitive(self) -> None:
        assert is_at_lastname("huber")
        assert is_at_lastname("GRUBER")

    def test_unknown_lastname(self) -> None:
        assert not is_at_lastname("Fakename")


class TestCombinedName:
    """Test the is_at_name union check."""

    def test_firstname_matched(self) -> None:
        assert is_at_name("Maria")

    def test_lastname_matched(self) -> None:
        assert is_at_name("Huber")

    def test_unknown_not_matched(self) -> None:
        assert not is_at_name("Zzzz")


class TestPhoneticMatching:
    """Test phonetic fuzzy matching against AT name lists."""

    def test_mueller_matches_umlaut_variant(self) -> None:
        # "Mueller" should match "Müller" via Kölner Phonetik
        matches = phonetic_match_lastname("Mueller")
        assert "müller" in matches

    def test_meyer_variant_matches(self) -> None:
        # Meyer, Mayer, Maier should all match the same phonetic bucket
        meyer_matches = phonetic_match_lastname("Meyer")
        mayer_matches = phonetic_match_lastname("Mayer")
        assert meyer_matches == mayer_matches
        assert "mayer" in meyer_matches or "meyer" in meyer_matches

    def test_no_phonetic_match(self) -> None:
        assert phonetic_match_firstname("Zzzxxx") == frozenset()


class TestNameSetsNonEmpty:
    """Sanity checks on the loaded name sets."""

    def test_first_name_set_reasonable_size(self) -> None:
        assert len(AT_FIRST_NAMES) > 50

    def test_last_name_set_reasonable_size(self) -> None:
        assert len(AT_LAST_NAMES) > 50

    def test_all_lowercase(self) -> None:
        assert all(n == n.lower() for n in AT_FIRST_NAMES)
        assert all(n == n.lower() for n in AT_LAST_NAMES)
