"""Financial PII detection patterns (IBAN, SVNr, Steuernummer)."""

import re

from anomyze.pipeline import DetectedEntity

# IBAN (international format, AT-optimized)
IBAN_PATTERN = re.compile(r'\b[A-Z]{2}\d{2}\s?(?:\d{4}\s?){3,7}\d{1,4}\b')

# Austrian Sozialversicherungsnummer: XXXX DDMMYY (10 digits)
# First 4 digits are the running number, last 6 are birthdate DDMMYY
SVNR_PATTERN = re.compile(
    r'\b(\d{4})\s?(\d{2})(\d{2})(\d{2})\b'
)

# Austrian Steuernummer: varies by Finanzamt, e.g., 12-345/6789, 123-456/7890
STEUERNUMMER_PATTERN = re.compile(
    r'\b(\d{2,3})[-/](\d{3,4})[-/](\d{4})\b'
)


def _validate_svnr_date(day: str, month: str, year: str) -> bool:
    """Validate the date portion of an Austrian SVNr.

    Args:
        day: DD portion (01-31).
        month: MM portion (01-12).
        year: YY portion.

    Returns:
        True if the date is plausible.
    """
    try:
        d, m = int(day), int(month)
        return 1 <= d <= 31 and 1 <= m <= 12
    except ValueError:
        return False


def find_ibans_regex(text: str) -> list[DetectedEntity]:
    """Find IBAN numbers using regex."""
    entities = []
    for match in IBAN_PATTERN.finditer(text):
        entities.append(DetectedEntity(
            word=match.group(),
            entity_group='IBAN',
            score=0.99,
            start=match.start(),
            end=match.end(),
            source='regex',
        ))
    return entities


def find_svnr_regex(text: str) -> list[DetectedEntity]:
    """Find Austrian Sozialversicherungsnummern (SVNr).

    Format: XXXX DDMMYY -- 4-digit running number + 6-digit birthdate.
    Validates that the date portion is plausible.
    """
    entities = []
    for match in SVNR_PATTERN.finditer(text):
        day, month, year = match.group(2), match.group(3), match.group(4)
        if not _validate_svnr_date(day, month, year):
            continue
        entities.append(DetectedEntity(
            word=match.group(),
            entity_group='SVN',
            score=0.95,
            start=match.start(),
            end=match.end(),
            source='regex',
        ))
    return entities


def find_tax_number_regex(text: str) -> list[DetectedEntity]:
    """Find Austrian Steuernummern.

    Format varies by Finanzamt: XX-XXX/XXXX or XXX-XXXX/XXXX.
    """
    entities = []
    for match in STEUERNUMMER_PATTERN.finditer(text):
        entities.append(DetectedEntity(
            word=match.group(),
            entity_group='STEUERNUMMER',
            score=0.90,
            start=match.start(),
            end=match.end(),
            source='regex',
        ))
    return entities
