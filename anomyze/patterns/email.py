"""Email address detection pattern."""

import re

from anomyze.pipeline import DetectedEntity

EMAIL_PATTERN = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')


def find_emails_regex(text: str) -> list[DetectedEntity]:
    """Find email addresses using regex."""
    entities = []
    for match in EMAIL_PATTERN.finditer(text):
        entities.append(DetectedEntity(
            word=match.group(),
            entity_group='EMAIL',
            score=0.99,
            start=match.start(),
            end=match.end(),
            source='regex',
        ))
    return entities
