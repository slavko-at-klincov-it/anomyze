"""Tests for adversarial text normalization."""

from anomyze.pipeline.normalizer import (
    normalize_adversarial,
    normalize_unicode,
    normalize_whitespace,
    remove_invisible,
    replace_homoglyphs,
)


class TestRemoveInvisible:
    """Test zero-width and invisible character removal."""

    def test_zero_width_space(self) -> None:
        assert remove_invisible("Mar\u200bia") == "Maria"

    def test_zero_width_joiner(self) -> None:
        assert remove_invisible("Hu\u200dber") == "Huber"

    def test_soft_hyphen(self) -> None:
        assert remove_invisible("Gru\u00adber") == "Gruber"

    def test_bom(self) -> None:
        assert remove_invisible("\ufeffHallo") == "Hallo"

    def test_multiple_invisible(self) -> None:
        assert remove_invisible("M\u200ba\u200cr\u200di\u200ea") == "Maria"

    def test_no_invisible(self) -> None:
        assert remove_invisible("Normal text") == "Normal text"

    def test_empty_string(self) -> None:
        assert remove_invisible("") == ""


class TestReplaceHomoglyphs:
    """Test Cyrillic/Greek homoglyph replacement."""

    def test_cyrillic_lowercase_a(self) -> None:
        # Cyrillic а (U+0430) → Latin a
        assert replace_homoglyphs("M\u0430ria") == "Maria"

    def test_cyrillic_lowercase_o(self) -> None:
        # Cyrillic о (U+043E) → Latin o
        assert replace_homoglyphs("H\u043eber") == "Hober"

    def test_cyrillic_uppercase_m(self) -> None:
        # Cyrillic М (U+041C) → Latin M
        assert replace_homoglyphs("\u041caria") == "Maria"

    def test_mixed_cyrillic_latin(self) -> None:
        # "Маriа" with Cyrillic М and а
        assert replace_homoglyphs("\u041c\u0430ri\u0430") == "Maria"

    def test_cyrillic_uppercase_p(self) -> None:
        # Cyrillic Р (U+0420) → Latin P
        assert replace_homoglyphs("\u0420eter") == "Peter"

    def test_greek_omicron(self) -> None:
        # Greek ο (U+03BF) → Latin o
        assert replace_homoglyphs("v\u03bfn") == "von"

    def test_no_homoglyphs(self) -> None:
        assert replace_homoglyphs("Maria Huber") == "Maria Huber"

    def test_preserves_real_cyrillic(self) -> None:
        # Non-lookalike Cyrillic chars should be preserved
        assert replace_homoglyphs("\u0431") == "\u0431"  # б has no Latin lookalike


class TestNormalizeUnicode:
    """Test NFKC Unicode normalization."""

    def test_fullwidth_letter(self) -> None:
        # Fullwidth Ｍ (U+FF2D) → M
        assert normalize_unicode("\uff2daria") == "Maria"

    def test_fullwidth_digits(self) -> None:
        # Fullwidth ６１ → 61
        assert normalize_unicode("AT\uff16\uff11") == "AT61"

    def test_composed_umlaut(self) -> None:
        # a + combining umlaut → ä
        assert normalize_unicode("a\u0308") == "\u00e4"

    def test_preserves_german_umlauts(self) -> None:
        text = "Müller Straße Grüße Öffentlich"
        assert normalize_unicode(text) == text

    def test_superscript_digits(self) -> None:
        # ² → 2
        assert normalize_unicode("m\u00b2") == "m2"


class TestNormalizeWhitespace:
    """Test whitespace normalization."""

    def test_multiple_spaces(self) -> None:
        assert normalize_whitespace("Maria   Huber") == "Maria Huber"

    def test_tabs(self) -> None:
        assert normalize_whitespace("Maria\t\tHuber") == "Maria Huber"

    def test_mixed_space_tab(self) -> None:
        assert normalize_whitespace("Maria \t Huber") == "Maria Huber"

    def test_preserves_newlines(self) -> None:
        assert normalize_whitespace("Zeile 1\nZeile 2") == "Zeile 1\nZeile 2"

    def test_preserves_single_spaces(self) -> None:
        assert normalize_whitespace("a b c") == "a b c"


class TestNormalizeAdversarial:
    """Test the full normalization pipeline."""

    def test_combined_zero_width_and_homoglyph(self) -> None:
        # Zero-width space in name + Cyrillic а
        text = "M\u200b\u0430ri\u0430 Hu\u200dber"
        assert normalize_adversarial(text) == "Maria Huber"

    def test_fullwidth_iban_digits(self) -> None:
        assert normalize_adversarial("AT\uff16\uff11 1904") == "AT61 1904"

    def test_clean_text_unchanged(self) -> None:
        text = "Maria Huber wohnt in Wien."
        assert normalize_adversarial(text) == text

    def test_preserves_german_special_chars(self) -> None:
        text = "Müller Straße Grüße Österreich"
        assert normalize_adversarial(text) == text

    def test_email_with_invisible_chars(self) -> None:
        text = "maria\u200b@\u200bexample\u200b.at"
        assert normalize_adversarial(text) == "maria@example.at"

    def test_phone_with_zero_width(self) -> None:
        # Zero-width chars are removed, not replaced with spaces
        text = "+43\u200b664\u200b123\u200b4567"
        assert normalize_adversarial(text) == "+436641234567"

    def test_idempotent(self) -> None:
        text = "Maria Huber, Musterstraße 12, 1010 Wien"
        assert normalize_adversarial(normalize_adversarial(text)) == text
