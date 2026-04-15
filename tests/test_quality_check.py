"""Tests for post-anonymization quality check."""

from anomyze.pipeline import DetectedEntity
from anomyze.pipeline.quality_check import (
    QualityIssue,
    QualityReport,
    check_output,
)


def _entity(
    word: str,
    group: str = "PER",
    start: int = 0,
    end: int = 0,
    placeholder: str = "",
) -> DetectedEntity:
    return DetectedEntity(
        word=word,
        entity_group=group,
        score=0.9,
        start=start,
        end=end or len(word),
        source="pii",
        placeholder=placeholder,
    )


class TestCleanOutput:
    """Output with no issues should pass the quality check."""

    def test_empty_text(self) -> None:
        report = check_output("", [])
        assert report.passed
        assert report.issues == []
        assert report.leak_count == 0

    def test_plain_text_no_entities(self) -> None:
        report = check_output("Hello world.", [])
        assert report.passed

    def test_placeholder_only(self) -> None:
        report = check_output("Hallo [PERSON_1], wie geht es?", [])
        assert report.passed

    def test_entity_fully_anonymized(self) -> None:
        ent = _entity("Maria Huber", placeholder="[PERSON_1]")
        report = check_output("[PERSON_1] ist hier", [ent])
        assert report.passed


class TestRegexLeaks:
    """Regex-detectable PII patterns left in output should be flagged."""

    def test_email_leak(self) -> None:
        report = check_output("Mail an maria@example.at", [])
        assert not report.passed
        assert report.leak_count >= 1
        assert any(i.pii_type == "EMAIL" for i in report.issues)

    def test_email_inside_placeholder_not_flagged(self) -> None:
        # The placeholder itself doesn't contain an email pattern
        report = check_output("Mail an [EMAIL_1]", [])
        assert report.passed

    def test_iban_leak(self) -> None:
        report = check_output("Konto: AT61 1904 3002 3457 3201", [])
        assert not report.passed
        assert any(i.pii_type == "IBAN" for i in report.issues)

    def test_svnr_leak(self) -> None:
        report = check_output("SVNR: 1237 010180", [])
        assert not report.passed
        assert any(i.pii_type == "SVN" for i in report.issues)

    def test_phone_leak(self) -> None:
        report = check_output("Tel: +43 664 1234567", [])
        assert not report.passed
        assert any(i.pii_type == "TELEFON" for i in report.issues)

    def test_multiple_leaks_counted(self) -> None:
        text = "Mail maria@example.at, IBAN AT61 1904 3002 3457 3201"
        report = check_output(text, [])
        assert not report.passed
        assert report.leak_count >= 2


class TestEntityWordLeaks:
    """Anonymized entity words still in the output should be flagged."""

    def test_entity_word_still_in_output(self) -> None:
        # Entity was anonymized but its word is still in output
        ent = _entity("Maria Huber", placeholder="[PERSON_1]")
        report = check_output("[PERSON_1] sagte: Maria Huber kam auch", [ent])
        assert not report.passed
        assert any(i.pii_type == "PER" for i in report.issues)

    def test_entity_without_placeholder_ignored(self) -> None:
        # Entity wasn't anonymized (no placeholder) — don't flag its presence
        ent = _entity("Maria Huber", placeholder="")
        report = check_output("Maria Huber kam vorbei", [ent])
        assert report.passed

    def test_case_insensitive_leak(self) -> None:
        ent = _entity("Maria", placeholder="[PERSON_1]")
        report = check_output("[PERSON_1] und maria gingen", [ent])
        assert not report.passed

    def test_word_boundary_no_false_positive(self) -> None:
        # "Wien" anonymized; "Wiener" in output should NOT trigger
        ent = _entity("Wien", group="LOC", placeholder="[ORT_1]")
        report = check_output("[ORT_1] ist die Wienerstraße", [ent])
        # "Wien" does not appear as a whole word in output
        assert report.passed

    def test_entity_word_only_in_placeholder_passes(self) -> None:
        ent = _entity("Maria", placeholder="[PERSON_1]")
        # Word never appears in output outside of the placeholder itself
        report = check_output("[PERSON_1] ist hier", [ent])
        assert report.passed


class TestPlaceholderFormat:
    """Malformed placeholders should be flagged."""

    def test_valid_govgpt_format(self) -> None:
        report = check_output("[PERSON_1] [IBAN_2]", [])
        assert report.passed

    def test_valid_ifg_format(self) -> None:
        report = check_output("[GESCHWÄRZT:PERSON] [GESCHWÄRZT:IBAN]", [])
        assert report.passed

    def test_valid_kapa_review_format(self) -> None:
        report = check_output("[PRÜFEN:PERSON_1]", [])
        assert report.passed

    def test_malformed_no_number(self) -> None:
        report = check_output("[PERSON]", [])
        assert not report.passed
        assert any(i.type == "format" for i in report.issues)

    def test_malformed_lowercase(self) -> None:
        report = check_output("[person_1]", [])
        assert not report.passed
        assert any(i.type == "format" for i in report.issues)

    def test_combined_issues(self) -> None:
        text = "[BROKEN] and maria@example.at"
        report = check_output(text, [])
        assert not report.passed
        # One format issue + one leak
        assert any(i.type == "format" for i in report.issues)
        assert any(i.type == "leak" for i in report.issues)


class TestQualityReportSerialization:
    """QualityReport should be JSON-serializable via to_dict."""

    def test_empty_report(self) -> None:
        report = QualityReport(passed=True, issues=[], leak_count=0)
        data = report.to_dict()
        assert data == {"passed": True, "leak_count": 0, "issues": []}

    def test_report_with_issue(self) -> None:
        issue = QualityIssue(
            type="leak",
            pii_type="EMAIL",
            position=5,
            snippet="foo@bar.com",
            description="Test",
        )
        report = QualityReport(passed=False, issues=[issue], leak_count=1)
        data = report.to_dict()
        assert data["passed"] is False
        assert data["leak_count"] == 1
        assert len(data["issues"]) == 1
        assert data["issues"][0]["pii_type"] == "EMAIL"
