"""Comprehensive tests for the regex detection layer and Austrian PII patterns."""

import pytest
from pathlib import Path

from anomyze.patterns import (
    find_emails_regex,
    find_titled_names_regex,
    find_labeled_names_regex,
    find_ibans_regex,
    find_svnr_regex,
    find_tax_number_regex,
    find_birth_date_regex,
    find_aktenzahl_regex,
    find_passport_regex,
    find_id_card_regex,
    find_license_plate_regex,
    find_phone_regex,
    find_address_regex,
    is_blacklisted,
    ENTITY_BLACKLIST,
)
from anomyze.pipeline.regex_layer import RegexLayer


# ---------------------------------------------------------------------------
# Email tests
# ---------------------------------------------------------------------------
class TestEmailRegex:
    """Tests for email detection."""

    def test_simple_email(self):
        text = "Kontakt: test@example.com"
        result = find_emails_regex(text)
        assert len(result) == 1
        assert result[0].word == "test@example.com"
        assert result[0].entity_group == "EMAIL"

    def test_multiple_emails(self):
        text = "Mail an foo@bar.de und baz@qux.at"
        result = find_emails_regex(text)
        assert len(result) == 2

    def test_no_email(self):
        text = "Kein Email hier"
        result = find_emails_regex(text)
        assert len(result) == 0

    def test_email_confidence(self):
        text = "test@example.com"
        result = find_emails_regex(text)
        assert result[0].score == 0.99
        assert result[0].source == "regex"


# ---------------------------------------------------------------------------
# Titled names tests
# ---------------------------------------------------------------------------
class TestTitledNames:
    """Tests for titled name detection."""

    def test_herr_name(self):
        text = "Bitte kontaktieren Sie Herrn Müller"
        result = find_titled_names_regex(text)
        assert len(result) == 1
        assert result[0].word == "Müller"

    def test_frau_name(self):
        text = "Frau Schmidt ist erreichbar"
        result = find_titled_names_regex(text)
        assert len(result) == 1
        assert result[0].word == "Schmidt"

    def test_frau_with_title(self):
        text = "Frau Dr. Elisabeth Steiner"
        result = find_titled_names_regex(text)
        assert len(result) == 1
        assert "Elisabeth" in result[0].word

    def test_full_name(self):
        text = "Herrn Thomas Müller"
        result = find_titled_names_regex(text)
        assert len(result) == 1
        assert result[0].word == "Thomas Müller"

    def test_mag_title(self):
        text = "Frau Mag. Katharina Huber"
        result = find_titled_names_regex(text)
        assert len(result) == 1
        assert "Katharina" in result[0].word

    def test_multiple_titles(self):
        text = "Herr Prof. Dr. Wolfgang Schneider"
        result = find_titled_names_regex(text)
        assert len(result) == 1
        assert "Wolfgang Schneider" in result[0].word


# ---------------------------------------------------------------------------
# Labeled names tests
# ---------------------------------------------------------------------------
class TestLabeledNames:
    """Tests for labeled name detection."""

    def test_protokollfuehrer(self):
        text = "Protokollführer: Max Mustermann"
        result = find_labeled_names_regex(text)
        assert len(result) == 1
        assert result[0].word == "Max Mustermann"

    def test_verfasser(self):
        text = "Verfasser: Anna Schmidt"
        result = find_labeled_names_regex(text)
        assert len(result) == 1

    def test_erstellt_von(self):
        text = "Erstellt von: Stefan Berger"
        result = find_labeled_names_regex(text)
        assert len(result) == 1
        assert result[0].word == "Stefan Berger"


# ---------------------------------------------------------------------------
# Blacklist tests
# ---------------------------------------------------------------------------
class TestBlacklist:
    """Tests for blacklist functionality."""

    def test_blacklisted_word(self):
        assert is_blacklisted("protokoll") is True
        assert is_blacklisted("meeting") is True
        assert is_blacklisted("e-mail") is True

    def test_not_blacklisted(self):
        assert is_blacklisted("Müller") is False
        assert is_blacklisted("Siemens") is False

    def test_short_words(self):
        assert is_blacklisted("ab") is True
        assert is_blacklisted("x") is True

    def test_admin_terms(self):
        assert is_blacklisted("bescheid") is True
        assert is_blacklisted("bundesministerium") is True


# ---------------------------------------------------------------------------
# IBAN tests
# ---------------------------------------------------------------------------
class TestIBANRegex:
    """Tests for IBAN detection."""

    def test_at_iban_with_spaces(self):
        text = "IBAN AT61 1904 3002 3457 3201"
        result = find_ibans_regex(text)
        assert len(result) == 1
        assert result[0].entity_group == "IBAN"
        assert "AT61" in result[0].word

    def test_at_iban_without_spaces(self):
        text = "IBAN AT611904300234573201"
        result = find_ibans_regex(text)
        assert len(result) == 1

    def test_de_iban(self):
        text = "DE89 3704 0044 0532 0130 00"
        result = find_ibans_regex(text)
        assert len(result) == 1

    def test_no_iban(self):
        text = "Keine IBAN hier"
        result = find_ibans_regex(text)
        assert len(result) == 0


# ---------------------------------------------------------------------------
# SVNr tests
# ---------------------------------------------------------------------------
class TestSVNrRegex:
    """Tests for Austrian Sozialversicherungsnummer detection."""

    def test_svnr_with_space(self):
        text = "SVNr. 1008 140387"
        result = find_svnr_regex(text)
        assert len(result) == 1
        assert result[0].entity_group == "SVN"
        assert result[0].score == 0.95

    def test_svnr_without_space(self):
        text = "Versicherungsnummer: 1008140387"
        result = find_svnr_regex(text)
        assert len(result) == 1

    def test_svnr_invalid_month(self):
        # Month 15 is invalid
        text = "Nr. 1234151587"
        result = find_svnr_regex(text)
        assert len(result) == 0

    def test_svnr_invalid_day(self):
        # Day 35 is invalid
        text = "Nr. 1234350187"
        result = find_svnr_regex(text)
        assert len(result) == 0

    def test_svnr_valid_edge_dates(self):
        # Day 31, month 12
        text = "Nr. 1007311287"
        result = find_svnr_regex(text)
        assert len(result) == 1


# ---------------------------------------------------------------------------
# Steuernummer tests
# ---------------------------------------------------------------------------
class TestTaxNumberRegex:
    """Tests for Austrian Steuernummer detection."""

    def test_tax_number_dash_slash(self):
        text = "Steuernummer: 12-345/6789"
        result = find_tax_number_regex(text)
        assert len(result) == 1
        assert result[0].entity_group == "STEUERNUMMER"

    def test_tax_number_slashes(self):
        text = "StNr. 123/4567/8901"
        result = find_tax_number_regex(text)
        assert len(result) == 1

    def test_no_tax_number(self):
        text = "Keine Steuernummer"
        result = find_tax_number_regex(text)
        assert len(result) == 0


# ---------------------------------------------------------------------------
# Birth date tests
# ---------------------------------------------------------------------------
class TestBirthDateRegex:
    """Tests for birth date detection."""

    def test_standard_format(self):
        text = "geboren am 14.03.1987"
        result = find_birth_date_regex(text)
        assert len(result) == 1
        assert result[0].entity_group == "GEBURTSDATUM"
        assert result[0].word == "14.03.1987"

    def test_dash_format(self):
        text = "Geburtsdatum: 01-12-1990"
        result = find_birth_date_regex(text)
        assert len(result) == 1

    def test_slash_format(self):
        text = "Geb.: 5/6/2000"
        result = find_birth_date_regex(text)
        assert len(result) == 1

    def test_single_digit_day_month(self):
        text = "geboren am 1.3.1987"
        result = find_birth_date_regex(text)
        assert len(result) == 1

    def test_invalid_month(self):
        text = "Datum: 01.13.1990"
        result = find_birth_date_regex(text)
        assert len(result) == 0

    def test_invalid_day(self):
        text = "Datum: 32.01.1990"
        result = find_birth_date_regex(text)
        assert len(result) == 0

    def test_future_century_not_matched(self):
        text = "Datum: 01.01.2199"
        result = find_birth_date_regex(text)
        assert len(result) == 0


# ---------------------------------------------------------------------------
# Aktenzahl tests
# ---------------------------------------------------------------------------
class TestAktenzahlRegex:
    """Tests for Austrian Aktenzahlen / Geschaeftszahlen detection."""

    def test_gz_format(self):
        text = "GZ BMI-2024/0815"
        result = find_aktenzahl_regex(text)
        assert len(result) == 1
        assert result[0].entity_group == "AKTENZAHL"
        assert result[0].score == 0.99

    def test_az_format(self):
        text = "AZ BMEIA-AT.3.18/0123"
        result = find_aktenzahl_regex(text)
        assert len(result) == 1

    def test_zl_format(self):
        text = "Zl. BKA-123456/2024"
        result = find_aktenzahl_regex(text)
        assert len(result) == 1

    def test_no_aktenzahl(self):
        text = "Keine Aktenzahl vorhanden"
        result = find_aktenzahl_regex(text)
        assert len(result) == 0


# ---------------------------------------------------------------------------
# Passport tests
# ---------------------------------------------------------------------------
class TestPassportRegex:
    """Tests for Austrian passport number detection (context-gated)."""

    def test_passport_with_context(self):
        text = "Reisepass: P1234567"
        result = find_passport_regex(text)
        assert len(result) == 1
        assert result[0].entity_group == "REISEPASS"
        assert result[0].word == "P1234567"

    def test_passport_pass_nr(self):
        text = "Pass-Nr. A9876543"
        result = find_passport_regex(text)
        assert len(result) == 1

    def test_passport_without_context(self):
        # Should NOT match without context keywords
        text = "Die Nummer A1234567 ist relevant"
        result = find_passport_regex(text)
        assert len(result) == 0

    def test_passport_passnummer(self):
        text = "Passnummer: B7654321"
        result = find_passport_regex(text)
        assert len(result) == 1


# ---------------------------------------------------------------------------
# ID card tests
# ---------------------------------------------------------------------------
class TestIDCardRegex:
    """Tests for Austrian Personalausweis detection (context-gated)."""

    def test_id_with_context(self):
        text = "Personalausweis: AB123456CD"
        result = find_id_card_regex(text)
        assert len(result) == 1
        assert result[0].entity_group == "PERSONALAUSWEIS"

    def test_id_without_context(self):
        text = "Die Nummer AB123456CD"
        result = find_id_card_regex(text)
        assert len(result) == 0


# ---------------------------------------------------------------------------
# License plate tests
# ---------------------------------------------------------------------------
class TestLicensePlateRegex:
    """Tests for Austrian KFZ-Kennzeichen detection."""

    def test_wien(self):
        text = "Kennzeichen W-34567B"
        result = find_license_plate_regex(text)
        assert len(result) == 1
        assert result[0].entity_group == "KFZ"

    def test_wien_space(self):
        text = "Kennzeichen W 12345 A"
        result = find_license_plate_regex(text)
        assert len(result) == 1

    def test_niederoesterreich(self):
        text = "NÖ-1234AB"
        result = find_license_plate_regex(text)
        assert len(result) == 1

    def test_steiermark(self):
        text = "ST-5678CD"
        result = find_license_plate_regex(text)
        assert len(result) == 1

    def test_bezirk_graz_umgebung(self):
        text = "GU-1234A"
        result = find_license_plate_regex(text)
        assert len(result) == 1

    def test_salzburg(self):
        text = "S-98765EF"
        result = find_license_plate_regex(text)
        assert len(result) == 1

    def test_tirol(self):
        text = "T-4567GH"
        result = find_license_plate_regex(text)
        assert len(result) == 1

    def test_kaernten(self):
        text = "K-1234J"
        result = find_license_plate_regex(text)
        assert len(result) == 1

    def test_burgenland(self):
        text = "B-5678K"
        result = find_license_plate_regex(text)
        assert len(result) == 1

    def test_vorarlberg(self):
        text = "V-9012L"
        result = find_license_plate_regex(text)
        assert len(result) == 1


# ---------------------------------------------------------------------------
# Phone number tests
# ---------------------------------------------------------------------------
class TestPhoneRegex:
    """Tests for Austrian phone number detection."""

    def test_international_format(self):
        text = "Tel: +43 664 1234567"
        result = find_phone_regex(text)
        assert len(result) == 1
        assert result[0].entity_group == "TELEFON"

    def test_double_zero_format(self):
        text = "Tel: 0043 1 5880000"
        result = find_phone_regex(text)
        assert len(result) == 1

    def test_mobile_0664(self):
        text = "Mobil: 0664 1234567"
        result = find_phone_regex(text)
        assert len(result) == 1

    def test_mobile_0660(self):
        text = "Handy: 0660 1234567"
        result = find_phone_regex(text)
        assert len(result) == 1

    def test_mobile_0676(self):
        text = "Nr: 0676 1234567"
        result = find_phone_regex(text)
        assert len(result) == 1

    def test_mobile_0699(self):
        text = "Tel: 0699 1234567"
        result = find_phone_regex(text)
        assert len(result) == 1

    def test_landline_wien(self):
        text = "Büro: 01 58800-0"
        result = find_phone_regex(text)
        assert len(result) == 1

    def test_landline_graz(self):
        text = "Kontakt: 0316 8740"
        result = find_phone_regex(text)
        assert len(result) == 1

    def test_no_phone(self):
        text = "Kein Telefon hier"
        result = find_phone_regex(text)
        assert len(result) == 0


# ---------------------------------------------------------------------------
# Address tests
# ---------------------------------------------------------------------------
class TestAddressRegex:
    """Tests for Austrian address detection."""

    def test_street_with_house_number(self):
        text = "wohnhaft in Schottenfeldgasse 29/3"
        result = find_address_regex(text)
        assert len(result) >= 1
        assert any(e.entity_group == "ADRESSE" for e in result)
        assert any("Schottenfeldgasse 29/3" in e.word for e in result)

    def test_strasse_format(self):
        text = "Mariahilfer Straße 45"
        result = find_address_regex(text)
        assert len(result) >= 1
        assert any("Mariahilfer Straße 45" in e.word for e in result)

    def test_weg(self):
        text = "Adresse: Waldweg 7a"
        result = find_address_regex(text)
        assert len(result) >= 1

    def test_platz(self):
        text = "am Stephansplatz 1"
        result = find_address_regex(text)
        assert len(result) >= 1

    def test_ring(self):
        text = "Burgring 12"
        result = find_address_regex(text)
        assert len(result) >= 1

    def test_plz_ort(self):
        text = "Adresse:\nSchottenfeldgasse 29/3, 1070 Wien"
        result = find_address_regex(text)
        # Should find street AND merge with PLZ+Ort
        addr_entities = [e for e in result if e.entity_group == "ADRESSE"]
        assert len(addr_entities) >= 1
        # At least one entity should span the full address
        full = [e for e in addr_entities if "1070" in e.word and "Wien" in e.word]
        assert len(full) >= 1 or len(addr_entities) >= 2  # merged or separate

    def test_standalone_plz_ort(self):
        text = "Zustelladresse:\n8010 Graz"
        result = find_address_regex(text)
        assert len(result) >= 1
        assert any("8010" in e.word and "Graz" in e.word for e in result)

    def test_compound_street_name(self):
        text = "Franz-Josefs-Kai 27"
        result = find_address_regex(text)
        assert len(result) >= 1

    def test_house_number_with_apartment(self):
        text = "Schottenfeldgasse 29/3/17"
        result = find_address_regex(text)
        assert len(result) >= 1

    def test_no_address(self):
        text = "Kein Adresshinweis in diesem Text."
        result = find_address_regex(text)
        assert len(result) == 0


# ---------------------------------------------------------------------------
# Quasi-identifier tests
# ---------------------------------------------------------------------------
class TestQuasiIdentifiers:
    """Tests for quasi-identifier combination detection."""

    def test_role_plus_location_plus_age(self):
        """Classic quasi-identifier: role + location + birth year."""
        from anomyze.pipeline.context_layer import ContextLayer
        from anomyze.pipeline import DetectedEntity
        from anomyze.config.settings import Settings
        from unittest.mock import MagicMock

        text = "der Beschwerdeführer aus Graz, geboren 1985, legte Einspruch ein"
        # Simulate LOC "Graz" already detected by NER
        existing = [
            DetectedEntity(word="Graz", entity_group="LOC", score=0.90,
                           start=28, end=32, source="org"),
        ]

        layer = ContextLayer()
        mock_mlm = MagicMock(side_effect=Exception("no model"))
        result = layer.process(text, existing, mock_mlm, Settings())

        quasi = [e for e in result if e.entity_group == "QUASI_ID"]
        assert len(quasi) >= 1, "Should flag quasi-identifiers"
        assert any("Kombination" in e.context for e in quasi)

    def test_no_quasi_id_when_person_detected(self):
        """No flagging when a PER entity is already in the window."""
        from anomyze.pipeline.context_layer import ContextLayer
        from anomyze.pipeline import DetectedEntity
        from anomyze.config.settings import Settings
        from unittest.mock import MagicMock

        text = "Maria Gruber aus Graz, geboren 1985"
        existing = [
            DetectedEntity(word="Maria Gruber", entity_group="PER", score=0.95,
                           start=0, end=12, source="pii"),
            DetectedEntity(word="Graz", entity_group="LOC", score=0.90,
                           start=17, end=21, source="org"),
        ]

        layer = ContextLayer()
        mock_mlm = MagicMock(side_effect=Exception("no model"))
        result = layer.process(text, existing, mock_mlm, Settings())

        quasi = [e for e in result if e.entity_group == "QUASI_ID"]
        assert len(quasi) == 0, "Should NOT flag when PER entity present"

    def test_single_signal_no_flag(self):
        """A single quasi-identifier alone should not be flagged."""
        from anomyze.pipeline.context_layer import ContextLayer
        from anomyze.pipeline import DetectedEntity
        from anomyze.config.settings import Settings
        from unittest.mock import MagicMock

        text = "der Beschwerdeführer legte Einspruch ein"

        layer = ContextLayer()
        mock_mlm = MagicMock(side_effect=Exception("no model"))
        result = layer.process(text, [], mock_mlm, Settings())

        quasi = [e for e in result if e.entity_group == "QUASI_ID"]
        assert len(quasi) == 0, "Single signal should not trigger"

    def test_age_reference(self):
        """45-jährige + location should flag."""
        from anomyze.pipeline.context_layer import ContextLayer
        from anomyze.pipeline import DetectedEntity
        from anomyze.config.settings import Settings
        from unittest.mock import MagicMock

        text = "die 45-jährige Antragstellerin aus Linz"
        existing = [
            DetectedEntity(word="Linz", entity_group="LOC", score=0.90,
                           start=35, end=39, source="org"),
        ]

        layer = ContextLayer()
        mock_mlm = MagicMock(side_effect=Exception("no model"))
        result = layer.process(text, existing, mock_mlm, Settings())

        quasi = [e for e in result if e.entity_group == "QUASI_ID"]
        assert len(quasi) >= 1


# ---------------------------------------------------------------------------
# RegexLayer integration tests
# ---------------------------------------------------------------------------
class TestRegexLayerIntegration:
    """Integration tests for the full regex layer."""

    def test_sample_document(self):
        """Test against the sample IFG complaint document."""
        fixture_path = Path(__file__).parent / "fixtures" / "sample_documents" / "beschwerde_ifg.txt"
        text = fixture_path.read_text(encoding="utf-8")

        layer = RegexLayer()
        entities = layer.process(text)

        # Extract entity groups found
        groups = {e.entity_group for e in entities}

        # Should detect these PII types
        assert "EMAIL" in groups, "Should detect email"
        assert "IBAN" in groups, "Should detect IBAN"
        assert "AKTENZAHL" in groups, "Should detect Aktenzahl"
        assert "GEBURTSDATUM" in groups, "Should detect birth date"
        assert "SVN" in groups, "Should detect SVNr"
        assert "ADRESSE" in groups, "Should detect address"
        assert "TELEFON" in groups, "Should detect phone number"
        assert "KFZ" in groups, "Should detect license plate"

    def test_no_overlap(self):
        """Ensure regex layer deduplicates overlapping entities."""
        text = "Kontakt: test@example.com, +43 664 1234567"
        layer = RegexLayer()
        entities = layer.process(text)

        # Check no two entities overlap
        for i, e1 in enumerate(entities):
            for e2 in entities[i + 1:]:
                assert e1.end <= e2.start or e2.end <= e1.start, \
                    f"Overlap: {e1.word} [{e1.start}:{e1.end}] and {e2.word} [{e2.start}:{e2.end}]"

    def test_all_entities_have_required_fields(self):
        """Ensure all entities have the required DetectedEntity fields."""
        text = "GZ BMI-2024/0815, IBAN AT61 1904 3002 3457 3201, Tel +43 664 1234567"
        layer = RegexLayer()
        entities = layer.process(text)

        for entity in entities:
            assert entity.word, "word must not be empty"
            assert entity.entity_group, "entity_group must not be empty"
            assert 0.0 <= entity.score <= 1.0, "score must be between 0 and 1"
            assert entity.start >= 0, "start must be non-negative"
            assert entity.end > entity.start, "end must be after start"
            assert entity.source, "source must not be empty"


# ---------------------------------------------------------------------------
# Channel tests
# ---------------------------------------------------------------------------
class TestGovGPTChannel:
    """Tests for GovGPT channel output formatting."""

    def test_basic_placeholder_replacement(self):
        from anomyze.channels.govgpt import GovGPTChannel
        from anomyze.pipeline import DetectedEntity
        from anomyze.config.settings import Settings

        text = "Maria Gruber wohnt in Wien."
        entities = [
            DetectedEntity(word="Maria Gruber", entity_group="PER", score=0.95,
                           start=0, end=12, source="pii"),
            DetectedEntity(word="Wien", entity_group="LOC", score=0.90,
                           start=22, end=26, source="org"),
        ]

        channel = GovGPTChannel()
        result = channel.format_output(text, entities, Settings())

        assert "[PERSON_1]" in result.text
        assert "[ORT_1]" in result.text
        assert "Maria Gruber" not in result.text
        assert "Wien" not in result.text
        assert result.mapping["[PERSON_1]"] == "Maria Gruber"
        assert result.mapping["[ORT_1]"] == "Wien"

    def test_same_entity_gets_same_placeholder(self):
        from anomyze.channels.govgpt import GovGPTChannel
        from anomyze.pipeline import DetectedEntity
        from anomyze.config.settings import Settings

        text = "Maria Gruber schrieb. Gruß, Maria Gruber"
        entities = [
            DetectedEntity(word="Maria Gruber", entity_group="PER", score=0.95,
                           start=0, end=12, source="pii"),
            DetectedEntity(word="Maria Gruber", entity_group="PER", score=0.95,
                           start=28, end=40, source="pii"),
        ]

        channel = GovGPTChannel()
        result = channel.format_output(text, entities, Settings())

        assert result.text.count("[PERSON_1]") == 2
        assert len(result.mapping) == 1


class TestIFGChannel:
    """Tests for IFG channel output formatting."""

    def test_irreversible_redaction(self):
        from anomyze.channels.ifg import IFGChannel
        from anomyze.pipeline import DetectedEntity
        from anomyze.config.settings import Settings

        text = "Maria Gruber, IBAN AT61 1904 3002 3457 3201"
        entities = [
            DetectedEntity(word="Maria Gruber", entity_group="PER", score=0.95,
                           start=0, end=12, source="pii"),
            DetectedEntity(word="AT61 1904 3002 3457 3201", entity_group="IBAN", score=0.99,
                           start=19, end=43, source="regex"),
        ]

        channel = IFGChannel()
        result = channel.format_output(text, entities, Settings())

        # No mapping
        assert not hasattr(result, 'mapping') or not getattr(result, 'mapping', None)
        # No sequential numbering
        assert "[GESCHWÄRZT:PERSON]" in result.text
        assert "[GESCHWÄRZT:IBAN]" in result.text
        # Redaction protocol
        assert len(result.redaction_protocol) == 2
        # Entity words sanitized
        for entity in result.entities:
            assert entity.word == "[REDACTED]"

    def test_no_numbering_prevents_correlation(self):
        from anomyze.channels.ifg import IFGChannel
        from anomyze.pipeline import DetectedEntity
        from anomyze.config.settings import Settings

        text = "Maria Gruber und Hans Müller"
        entities = [
            DetectedEntity(word="Maria Gruber", entity_group="PER", score=0.95,
                           start=0, end=12, source="pii"),
            DetectedEntity(word="Hans Müller", entity_group="PER", score=0.90,
                           start=17, end=28, source="pii"),
        ]

        channel = IFGChannel()
        result = channel.format_output(text, entities, Settings())

        # Both should have the same placeholder (no numbering)
        assert result.text.count("[GESCHWÄRZT:PERSON]") == 2


class TestKAPAChannel:
    """Tests for KAPA channel output formatting."""

    def test_audit_trail(self):
        from anomyze.channels.kapa import KAPAChannel
        from anomyze.pipeline import DetectedEntity
        from anomyze.config.settings import Settings

        text = "Maria Gruber aus Wien"
        entities = [
            DetectedEntity(word="Maria Gruber", entity_group="PER", score=0.95,
                           start=0, end=12, source="pii"),
        ]

        settings = Settings()
        channel = KAPAChannel()
        result = channel.format_output(text, entities, settings)

        assert len(result.audit_entries) == 1
        entry = result.audit_entries[0]
        assert entry.entity_group == "PERSON"
        assert entry.confidence == 0.95
        assert entry.action == "anonymized"
        assert result.document_id

    def test_low_confidence_flagged(self):
        from anomyze.channels.kapa import KAPAChannel
        from anomyze.pipeline import DetectedEntity
        from anomyze.config.settings import Settings

        text = "Kontakt: Firma Unbekannt"
        entities = [
            DetectedEntity(word="Unbekannt", entity_group="ORG_DETECTED", score=0.70,
                           start=15, end=24, source="perplexity"),
        ]

        settings = Settings(kapa_review_threshold=0.85)
        channel = KAPAChannel()
        result = channel.format_output(text, entities, settings)

        # Should be flagged for review
        assert len(result.flagged_for_review) == 1
        assert "PRÜFEN" in result.flagged_for_review[0]
        assert "PRÜFEN" in result.text
        # Audit entry should reflect flagging
        assert result.audit_entries[0].action == "flagged_for_review"
