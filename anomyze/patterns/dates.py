"""Birth date detection pattern."""

import re

from anomyze.pipeline import DetectedEntity

# Birth dates: DD.MM.YYYY, DD-MM-YYYY, DD/MM/YYYY, D.M.YYYY
BIRTH_DATE_PATTERN = re.compile(
    r'\b(0?[1-9]|[12]\d|3[01])[.\-/](0?[1-9]|1[0-2])[.\-/]((?:19|20)\d{2})\b'
)


def find_birth_date_regex(text: str) -> list[DetectedEntity]:
    """Find birth dates in DD.MM.YYYY format and variants.

    Validates day (1-31) and month (1-12) ranges.
    """
    entities = []
    for match in BIRTH_DATE_PATTERN.finditer(text):
        entities.append(DetectedEntity(
            word=match.group(),
            entity_group='GEBURTSDATUM',
            score=0.95,
            start=match.start(),
            end=match.end(),
            source='regex',
        ))
    return entities
