"""Person name detection patterns (titled and labeled)."""

import re

from anomyze.pipeline import DetectedEntity

# Titled names: Herrn Muller, Frau Dr. Elisabeth Steiner
TITLED_NAME_PATTERN = re.compile(
    r'\b(?:Herrn?|Frau)\.?\s+(?:(?:Dr|Prof|Mag|Ing|Dipl|DI|DDr)\.?\s+)*'
    r'([A-ZÄÖÜ][a-zäöüß]+(?:\s+[A-ZÄÖÜ][a-zäöüß]+)?)'
)

# Labeled names: Protokollfuehrer: Max Mustermann
LABELED_NAME_PATTERN = re.compile(
    r'\b(?:Protokollführer|Schriftführer|Verfasser|Autor|Erstellt von|'
    r'Bearbeiter|Verantwortlich|Kontakt)(?:in)?:\s*'
    r'([A-ZÄÖÜ][a-zäöüß]+(?:\s+[A-ZÄÖÜ][a-zäöüß]+)?)'
)


def find_titled_names_regex(text: str) -> list[DetectedEntity]:
    """Find person names with titles like 'Herrn Schmidt', 'Frau Mag. Elisabeth Steiner'."""
    entities = []
    for match in TITLED_NAME_PATTERN.finditer(text):
        name = match.group(1)
        entities.append(DetectedEntity(
            word=name,
            entity_group='PER',
            score=0.95,
            start=match.start(1),
            end=match.end(1),
            source='regex_title',
        ))
    return entities


def find_labeled_names_regex(text: str) -> list[DetectedEntity]:
    """Find person names after labels like 'Protokollfuehrer:', 'Erstellt von:'."""
    entities = []
    for match in LABELED_NAME_PATTERN.finditer(text):
        name = match.group(1)
        entities.append(DetectedEntity(
            word=name,
            entity_group='PER',
            score=0.95,
            start=match.start(1),
            end=match.end(1),
            source='regex_label',
        ))
    return entities
