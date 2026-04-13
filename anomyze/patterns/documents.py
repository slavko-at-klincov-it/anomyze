"""Document number detection patterns (Aktenzahl, Reisepass, Personalausweis)."""

import re

from anomyze.pipeline import DetectedEntity

# Aktenzahlen / Geschaeftszahlen: GZ BMI-2024/0815, AZ BMEIA-AT.3.18/0123-III/2024
AKTENZAHL_PATTERN = re.compile(
    r'\b(?:GZ|Zl\.?|AZ)\s+[A-ZÄÖÜ][A-ZÄÖÜa-zäöü0-9.\-/]+(?:\d{2,4})'
)

# Austrian passport: letter + 7 digits (context-gated)
PASSPORT_PATTERN = re.compile(r'\b([A-Z]\d{7})\b')
PASSPORT_CONTEXT = re.compile(
    r'(?:Reisepass|Pass-?Nr\.?|Passnummer|passport)\s*:?\s*',
    re.IGNORECASE
)

# Austrian Personalausweis (ID card): context-gated
ID_CARD_PATTERN = re.compile(r'\b([A-Z0-9]{8,10})\b')
ID_CARD_CONTEXT = re.compile(
    r'(?:Personalausweis|Ausweis-?Nr\.?|Ausweisnummer|ID-?Nr\.?)\s*:?\s*',
    re.IGNORECASE
)


def find_aktenzahl_regex(text: str) -> list[DetectedEntity]:
    """Find Austrian Aktenzahlen / Geschaeftszahlen.

    Matches administrative file numbers like GZ BMI-2024/0815,
    AZ BMEIA-AT.3.18/0123-III/2024, Zl. 12345/2024.
    """
    entities = []
    for match in AKTENZAHL_PATTERN.finditer(text):
        entities.append(DetectedEntity(
            word=match.group(),
            entity_group='AKTENZAHL',
            score=0.99,
            start=match.start(),
            end=match.end(),
            source='regex',
        ))
    return entities


def find_passport_regex(text: str) -> list[DetectedEntity]:
    """Find Austrian passport numbers (context-gated).

    Only matches when preceded by context keywords like 'Reisepass',
    'Pass-Nr', 'Passnummer' to reduce false positives.
    Format: letter + 7 digits (e.g., P1234567).
    """
    entities = []
    for ctx_match in PASSPORT_CONTEXT.finditer(text):
        remaining = text[ctx_match.end():]
        pp_match = PASSPORT_PATTERN.match(remaining)
        if pp_match:
            abs_start = ctx_match.end() + pp_match.start(1)
            abs_end = ctx_match.end() + pp_match.end(1)
            entities.append(DetectedEntity(
                word=pp_match.group(1),
                entity_group='REISEPASS',
                score=0.85,
                start=abs_start,
                end=abs_end,
                source='regex',
            ))
    return entities


def find_id_card_regex(text: str) -> list[DetectedEntity]:
    """Find Austrian Personalausweis numbers (context-gated).

    Only matches when preceded by context keywords like 'Personalausweis',
    'Ausweis-Nr', 'ID-Nr' to reduce false positives.
    """
    entities = []
    for ctx_match in ID_CARD_CONTEXT.finditer(text):
        remaining = text[ctx_match.end():]
        id_match = ID_CARD_PATTERN.match(remaining)
        if id_match:
            abs_start = ctx_match.end() + id_match.start(1)
            abs_end = ctx_match.end() + id_match.end(1)
            entities.append(DetectedEntity(
                word=id_match.group(1),
                entity_group='PERSONALAUSWEIS',
                score=0.85,
                start=abs_start,
                end=abs_end,
                source='regex',
            ))
    return entities
