"""Tests for regex patterns."""

import pytest
from anomyze.patterns import (
    find_emails_regex,
    find_titled_names_regex,
    find_labeled_names_regex,
    is_blacklisted,
    ENTITY_BLACKLIST,
)


class TestEmailRegex:
    """Tests for email detection."""

    def test_simple_email(self):
        text = "Kontakt: test@example.com"
        result = find_emails_regex(text)
        assert len(result) == 1
        assert result[0]['word'] == "test@example.com"
        assert result[0]['entity_group'] == "EMAIL"

    def test_multiple_emails(self):
        text = "Mail an foo@bar.de und baz@qux.at"
        result = find_emails_regex(text)
        assert len(result) == 2

    def test_no_email(self):
        text = "Kein Email hier"
        result = find_emails_regex(text)
        assert len(result) == 0


class TestTitledNames:
    """Tests for titled name detection."""

    def test_herr_name(self):
        text = "Bitte kontaktieren Sie Herrn Müller"
        result = find_titled_names_regex(text)
        assert len(result) == 1
        assert result[0]['word'] == "Müller"

    def test_frau_name(self):
        text = "Frau Schmidt ist erreichbar"
        result = find_titled_names_regex(text)
        assert len(result) == 1
        assert result[0]['word'] == "Schmidt"

    def test_frau_with_title(self):
        text = "Frau Dr. Elisabeth Steiner"
        result = find_titled_names_regex(text)
        assert len(result) == 1
        assert "Elisabeth" in result[0]['word']

    def test_full_name(self):
        text = "Herrn Thomas Müller"
        result = find_titled_names_regex(text)
        assert len(result) == 1
        assert result[0]['word'] == "Thomas Müller"


class TestLabeledNames:
    """Tests for labeled name detection."""

    def test_protokollfuehrer(self):
        text = "Protokollführer: Max Mustermann"
        result = find_labeled_names_regex(text)
        assert len(result) == 1
        assert result[0]['word'] == "Max Mustermann"

    def test_verfasser(self):
        text = "Verfasser: Anna Schmidt"
        result = find_labeled_names_regex(text)
        assert len(result) == 1


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
        # Words less than 3 characters should be blacklisted
        assert is_blacklisted("ab") is True
        assert is_blacklisted("x") is True
