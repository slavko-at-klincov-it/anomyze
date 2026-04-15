"""Tests for the Austrian legal-whitelist filter."""

from anomyze.patterns.whitelist import (
    filter_whitelisted,
    is_legal_paragraph,
    is_whitelisted,
)
from anomyze.pipeline import DetectedEntity


def _ent(word: str, group: str = "ORG") -> DetectedEntity:
    return DetectedEntity(
        word=word,
        entity_group=group,
        score=0.9,
        start=0,
        end=len(word),
        source="org",
    )


class TestLegalParagraph:
    def test_basic_paragraph(self) -> None:
        assert is_legal_paragraph("§ 123")

    def test_paragraph_with_letter(self) -> None:
        assert is_legal_paragraph("§ 123a")

    def test_paragraph_with_abs(self) -> None:
        assert is_legal_paragraph("§ 123 Abs. 2")

    def test_paragraph_with_abs_and_ziffer(self) -> None:
        assert is_legal_paragraph("§ 123 Abs. 2 Z 3")

    def test_article(self) -> None:
        assert is_legal_paragraph("Art. 5")

    def test_artikel_full(self) -> None:
        assert is_legal_paragraph("Artikel 5 Abs. 2")

    def test_plain_text_not_paragraph(self) -> None:
        assert not is_legal_paragraph("Maria Gruber")

    def test_empty(self) -> None:
        assert not is_legal_paragraph("")


class TestLegalCodes:
    def test_asvg(self) -> None:
        assert is_whitelisted(_ent("ASVG"))

    def test_dsgvo(self) -> None:
        assert is_whitelisted(_ent("DSGVO"))

    def test_b_vg(self) -> None:
        assert is_whitelisted(_ent("B-VG"))

    def test_stgb(self) -> None:
        assert is_whitelisted(_ent("StGB"))

    def test_unknown_code_not_whitelisted(self) -> None:
        assert not is_whitelisted(_ent("XYZG"))


class TestAuthorities:
    def test_full_ministry_name(self) -> None:
        assert is_whitelisted(_ent("Bundesministerium für Inneres"))

    def test_ministry_abbreviation(self) -> None:
        assert is_whitelisted(_ent("BMI"))
        assert is_whitelisted(_ent("BMF"))

    def test_high_court(self) -> None:
        assert is_whitelisted(_ent("Verfassungsgerichtshof"))
        assert is_whitelisted(_ent("VfGH"))

    def test_oegk(self) -> None:
        assert is_whitelisted(_ent("ÖGK"))

    def test_regional_suffix_allowed(self) -> None:
        assert is_whitelisted(_ent("Magistrat Wien"))
        assert is_whitelisted(_ent("Bezirkshauptmannschaft Graz-Umgebung"))

    def test_case_insensitive(self) -> None:
        assert is_whitelisted(_ent("bundesministerium für inneres"))


class TestEntityGroupGating:
    def test_person_name_not_whitelisted(self) -> None:
        # Even if a PER entity literally reads "ASVG", it must not be
        # whitelisted (avoids cases where NER misclassifies an acronym
        # as a person).
        assert not is_whitelisted(_ent("ASVG", group="PER"))

    def test_iban_not_whitelisted(self) -> None:
        assert not is_whitelisted(_ent("AT61 1904 3002 3457 3201", group="IBAN"))

    def test_loc_whitelisted_for_authority(self) -> None:
        assert is_whitelisted(_ent("Statistik Austria", group="LOC"))


class TestFilterWhitelisted:
    def test_removes_only_whitelisted(self) -> None:
        entities = [
            _ent("Karl Nehammer", group="PER"),
            _ent("BMI", group="ORG"),
            _ent("Wien", group="LOC"),
            _ent("DSGVO", group="ORG"),
        ]
        result = filter_whitelisted(entities)
        result_words = [e.word for e in result]
        assert "Karl Nehammer" in result_words
        assert "Wien" in result_words  # not a whitelisted authority
        assert "BMI" not in result_words
        assert "DSGVO" not in result_words

    def test_empty_list(self) -> None:
        assert filter_whitelisted([]) == []

    def test_no_whitelisted(self) -> None:
        entities = [_ent("Karl Nehammer", group="PER")]
        result = filter_whitelisted(entities)
        assert len(result) == 1
