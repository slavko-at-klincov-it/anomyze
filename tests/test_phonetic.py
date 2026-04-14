"""Tests for Kölner Phonetik encoding."""

from anomyze.pipeline.phonetic import cologne_phonetic, phonetic_equal


class TestColognePhonetic:
    """Test the Kölner Phonetik algorithm."""

    def test_empty(self) -> None:
        assert cologne_phonetic("") == ""

    def test_single_letter(self) -> None:
        # A is a vowel → '0' but then trailing zeros are stripped
        # (only the first character keeps leading '0' if present)
        assert cologne_phonetic("A") == "0"

    def test_non_letters(self) -> None:
        assert cologne_phonetic("123") == ""

    def test_meyer_variants_all_equal(self) -> None:
        # Meyer, Mayer, Maier, Meier should produce the same code
        code = cologne_phonetic("Meyer")
        assert cologne_phonetic("Mayer") == code
        assert cologne_phonetic("Maier") == code
        assert cologne_phonetic("Meier") == code

    def test_mueller_variants_equal(self) -> None:
        # "Mueller" and "Müller" should encode to the same code
        assert phonetic_equal("Mueller", "Müller")

    def test_mueller_code(self) -> None:
        # Expected: M=6, Ü=0, L=5, L (collapsed), E=0, R=7 → 657
        assert cologne_phonetic("Müller") == "657"

    def test_schmidt(self) -> None:
        # Expected encoding for Schmidt
        code = cologne_phonetic("Schmidt")
        # S=8, C=8 (same, collapsed), H silent, M=6, I=0, D=2, T=2 (collapsed)
        # Vowels (not initial) removed → 862
        assert code == "862"

    def test_umlaut_normalization(self) -> None:
        assert cologne_phonetic("Müller") == cologne_phonetic("Mueller")
        assert cologne_phonetic("Schöpf") == cologne_phonetic("Schoepf")

    def test_ß_treated_as_s(self) -> None:
        assert cologne_phonetic("Weiß") == cologne_phonetic("Weiss")

    def test_different_names_different_codes(self) -> None:
        # Names that sound different should not collide
        assert cologne_phonetic("Meyer") != cologne_phonetic("Bauer")
        assert cologne_phonetic("Huber") != cologne_phonetic("Gruber")

    def test_h_is_silent(self) -> None:
        # H is silent except after P where it becomes F
        assert cologne_phonetic("Haus") == cologne_phonetic("aus")

    def test_ph_encodes_as_f(self) -> None:
        # PH → 3 (F sound)
        assert cologne_phonetic("Phil") == cologne_phonetic("Fil")

    def test_initial_c_before_vowel(self) -> None:
        # Initial C before A/H/K/L/O/Q/R/U/X → 4 (K sound)
        assert cologne_phonetic("Christian")[0] == "4"

    def test_case_insensitive(self) -> None:
        assert cologne_phonetic("Müller") == cologne_phonetic("müller")
        assert cologne_phonetic("MÜLLER") == cologne_phonetic("Müller")


class TestPhoneticEqual:
    """Test the phonetic_equal helper."""

    def test_equal_variants(self) -> None:
        assert phonetic_equal("Meier", "Mayer")
        assert phonetic_equal("Müller", "Mueller")

    def test_not_equal(self) -> None:
        assert not phonetic_equal("Huber", "Gruber")
        assert not phonetic_equal("Maria", "Thomas")

    def test_empty_strings(self) -> None:
        assert phonetic_equal("", "")
