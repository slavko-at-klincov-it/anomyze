"""Austrian KFZ-Kennzeichen (license plate) detection pattern."""

import re

from anomyze.pipeline import DetectedEntity

# Austrian KFZ-Kennzeichen
# Bundesland codes: W (Wien), NO, OO, S (Salzburg), ST (Steiermark),
# K (Kaernten), B (Burgenland), T (Tirol), V (Vorarlberg)
# Bezirk codes: 1-2 letters (e.g., AM, BA, BL, BN, BR, ...)
_AT_BEZIRK_CODES = (
    # Bundesland single-letter codes
    'W|S|K|B|T|V'
    # Two-letter Bundesland codes
    '|NÖ|OÖ|ST'
    # Common Bezirk codes
    '|AM|BA|BL|BN|BR|BZ|DL|EF|EU|FB|FE|FF|FR|GD|GF|GM|GR|GS|GU'
    '|HA|HB|HE|HF|HO|IL|IM|JE|JO|JU|KB|KF|KG|KI|KL|KO|KR|KS'
    '|LA|LB|LE|LF|LI|LL|LN|LZ|MA|MD|ME|MI|MK|MT|MU|MZ'
    '|NA|NK|ND|OW|OP|PE|PL|PT|RA|RE|RI|RO|SB|SD|SE|SL|SO|SP|SR|SV|SW|SZ'
    '|TA|TU|UU|VB|VI|VK|VL|VO|WB|WE|WK|WL|WN|WT|WU|WY|ZE|ZT|ZW'
)
LICENSE_PLATE_PATTERN = re.compile(
    r'\b(' + _AT_BEZIRK_CODES + r')\s?[-]?\s?(\d{1,6})\s?([A-Z]{1,3})\b'
)


def find_license_plate_regex(text: str) -> list[DetectedEntity]:
    """Find Austrian KFZ-Kennzeichen.

    Matches Austrian license plate formats with Bundesland/Bezirk prefixes.
    Examples: W-12345A, NO 1234 AB, GU-567C.
    """
    entities = []
    for match in LICENSE_PLATE_PATTERN.finditer(text):
        entities.append(DetectedEntity(
            word=match.group(),
            entity_group='KFZ',
            score=0.95,
            start=match.start(),
            end=match.end(),
            source='regex',
        ))
    return entities
