"""Austrian address detection patterns."""

import re

from anomyze.pipeline import DetectedEntity

# Street suffixes common in Austrian German (lowercase for embedded matching)
_STREET_SUFFIXES_LOWER = (
    r'stra(?:ß|ss)e|gasse|weg|allee|platz|ring'
    r'|kai|zeile|promenade|damm|steig|stiege'
    r'|gürtel|ufer|brücke|markt|hof'
)
# Street suffixes as standalone capitalized words
_STREET_SUFFIXES_CAP = (
    r'Stra(?:ß|ss)e|Gasse|Weg|Allee|Platz|Ring'
    r'|Kai|Zeile|Promenade|Damm|Steig|Stiege'
    r'|Gürtel|Ufer|Brücke|Markt|Hof'
)

# Pattern A: Suffix embedded in single word (e.g., Schottenfeldgasse, Ringstrasse)
_ADDR_EMBEDDED = re.compile(
    r'\b([A-ZÄÖÜ][a-zäöüß]*(?:' + _STREET_SUFFIXES_LOWER + r'))'
    r'\s+(\d{1,4}[a-z]?(?:\s?/\s?\d{1,4})*)',
    re.UNICODE,
)

# Pattern B: Prefix word(s) + standalone suffix word
# (e.g., Mariahilfer Strasse, Franz-Josefs-Kai, Am Hauptplatz)
_ADDR_MULTIWORD = re.compile(
    r'\b((?:[A-ZÄÖÜ][a-zäöüß]+(?:-[A-ZÄÖÜa-zäöüß]+)*[\s-]){1,3}'
    r'(?:' + _STREET_SUFFIXES_CAP + r'))'
    r'\s+(\d{1,4}[a-z]?(?:\s?/\s?\d{1,4})*)',
    re.UNICODE,
)

# PLZ + Ort: 4-digit Austrian postal code (1010-9999) followed by place name
# Context-gated: only match after comma/newline or at start of line
PLZ_ORT_PATTERN = re.compile(
    r'(?:^|[,\n]\s*)'
    r'(\d{4})\s+'
    r'([A-ZÄÖÜ][a-zäöüß]+(?:\s+(?:am|an|im|bei|ob|unter|in)\s+'
    r'[a-zäöüß]+(?:\s+[A-ZÄÖÜ][a-zäöüß]+)?)?)',
    re.MULTILINE
)


def find_address_regex(text: str) -> list[DetectedEntity]:
    """Find Austrian addresses (street + house number, PLZ + Ort).

    Detects patterns like:
    - Schottenfeldgasse 29/3
    - Mariahilfer Strasse 1a
    - Franz-Josefs-Kai 27
    - 1070 Wien
    - Hauptplatz 12, 8010 Graz

    Combines adjacent street + PLZ/Ort matches into a single ADRESSE entity
    when they appear together (e.g., "Strasse 29/3, 1070 Wien").
    """
    entities: list[DetectedEntity] = []

    # Find street + house number matches from both patterns
    street_spans: list[tuple[int, int, str]] = []
    for match in _ADDR_EMBEDDED.finditer(text):
        street_spans.append((match.start(), match.end(), match.group()))
    for match in _ADDR_MULTIWORD.finditer(text):
        span = (match.start(), match.end(), match.group())
        if not any(s[0] == span[0] for s in street_spans):
            street_spans.append(span)

    # Find PLZ + Ort matches
    plz_spans: list[tuple[int, int, str]] = []
    for match in PLZ_ORT_PATTERN.finditer(text):
        plz_start = match.start(1)
        plz_end = match.end(2)
        plz_word = text[plz_start:plz_end]
        plz_spans.append((plz_start, plz_end, plz_word))

    # Try to merge street + PLZ/Ort if they're adjacent (within ~5 chars)
    used_plz: set[int] = set()
    for s_start, s_end, s_word in street_spans:
        merged = False
        for i, (p_start, p_end, _p_word) in enumerate(plz_spans):
            gap = p_start - s_end
            if 0 <= gap <= 5:
                full_word = text[s_start:p_end]
                entities.append(DetectedEntity(
                    word=full_word,
                    entity_group='ADRESSE',
                    score=0.95,
                    start=s_start,
                    end=p_end,
                    source='regex',
                ))
                used_plz.add(i)
                merged = True
                break
        if not merged:
            entities.append(DetectedEntity(
                word=s_word,
                entity_group='ADRESSE',
                score=0.90,
                start=s_start,
                end=s_end,
                source='regex',
            ))

    # Add standalone PLZ+Ort that weren't merged
    for i, (p_start, p_end, p_word) in enumerate(plz_spans):
        if i not in used_plz:
            entities.append(DetectedEntity(
                word=p_word,
                entity_group='ADRESSE',
                score=0.85,
                start=p_start,
                end=p_end,
                source='regex',
            ))

    return entities
