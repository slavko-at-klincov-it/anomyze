"""Financial PII detection patterns (IBAN, SVNr, Steuernummer)."""

import re

from stdnum import iban as stdnum_iban
from stdnum.at import vnr as stdnum_vnr

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


def find_ibans_regex(text: str) -> list[DetectedEntity]:
    """Find IBAN numbers using regex + ISO 13616 MOD-97 check."""
    entities = []
    for match in IBAN_PATTERN.finditer(text):
        if not stdnum_iban.is_valid(match.group()):
            continue
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
    Validates the Austrian MOD-11 check digit and the embedded birth
    date via ``stdnum.at.vnr``.
    """
    entities = []
    for match in SVNR_PATTERN.finditer(text):
        if not stdnum_vnr.is_valid(match.group()):
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
