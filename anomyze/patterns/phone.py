"""Austrian phone number detection pattern."""

import re

from anomyze.pipeline import DetectedEntity

# Austrian phone numbers: +43, 0043, or 0XXX formats
PHONE_PATTERN_AT = re.compile(
    r'(?:'
    # International format: +43 or 0043
    r'(?:\+43|0043)\s?[-./]?\s?'
    r'(?:\(?\d{1,4}\)?\s?[-./]?\s?)?'
    r'\d{3,4}\s?[-./]?\s?\d{2,6}'
    r'|'
    # Austrian mobile: 0650, 0660, 0664, 0676, 0680, 0681, 0688, 0699
    r'0(?:650|660|664|67[06]|68[018]|699)\s?[-./]?\s?\d{3,4}\s?[-./]?\s?\d{2,6}'
    r'|'
    # Austrian landline with area code: 01 (Wien), 0316 (Graz), etc.
    r'0[1-9]\d{0,3}\s?[-./]?\s?\d{3,8}'
    r')'
)


def find_phone_regex(text: str) -> list[DetectedEntity]:
    """Find Austrian phone numbers.

    Matches:
    - International: +43 XXX XXXXXXX, 0043 XXX XXXXXXX
    - Mobile: 0650, 0660, 0664, 0676, 0680, 0681, 0688, 0699
    - Landline: 01 (Wien), 0316 (Graz), etc.
    """
    entities = []
    for match in PHONE_PATTERN_AT.finditer(text):
        phone = match.group()
        digits_only = re.sub(r'\D', '', phone)
        if len(digits_only) < 7:
            continue
        entities.append(DetectedEntity(
            word=phone,
            entity_group='TELEFON',
            score=0.95,
            start=match.start(),
            end=match.end(),
            source='regex',
        ))
    return entities
