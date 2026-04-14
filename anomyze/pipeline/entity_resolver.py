"""
Entity resolution: link different mentions of the same entity.

Detects when "Dr. Maria Huber", "Maria Huber", and "Frau Huber"
all refer to the same person, and assigns them the same canonical
key so the output channel groups them under one placeholder.
"""

import re

from anomyze.pipeline import DetectedEntity
from anomyze.pipeline.phonetic import cologne_phonetic

# Austrian/German personal titles (academic, honorific, aristocratic).
# Tokens are matched case-insensitively after dot/comma stripping.
_TITLES = frozenset({
    # Academic
    'dr', 'dr.in', 'drin',
    'mag', 'mag.a', 'maga',
    'prof', 'prof.in', 'profin',
    'di', 'dipl', 'ing', 'dipl.-ing', 'dipling',
    'phd', 'mba', 'msc', 'bsc', 'ba', 'ma', 'mas',
    # Honorific
    'herr', 'frau', 'fr', 'hr',
    'sir', 'lord', 'lady',
    # Aristocratic / nobility particles (von/zu/van/de NOT stripped:
    # they are part of legal names and stripping risks false matches).
    'baron', 'baronin', 'graf', 'graefin', 'gräfin',
    'fuerst', 'fuerstin', 'fürst', 'fürstin',
    'edler', 'edle', 'ritter',
    # Religious / generational
    'pater', 'sen', 'jr',
})

# Legal forms and generic org descriptors (strip from ORG entities).
_ORG_TOKENS = frozenset({
    # Austrian/German legal forms
    'gmbh', 'ag', 'kg', 'og', 'ohg', 'eu', 'kgaa',
    'gen', 'verein', 'ev', 'eg',
    # International
    'ltd', 'inc', 'corp', 'co', 'llc', 'plc', 'sa', 'sarl',
    # Generic descriptors
    'firma', 'gesellschaft', 'unternehmen', 'konzern',
    'gruppe', 'group', 'company',
    # Connectors
    '&', 'und', 'and',
})

# Articles (German + English).
_ARTICLES = frozenset({
    'der', 'die', 'das', 'dem', 'den', 'des',
    'ein', 'eine', 'einer', 'einen', 'eines', 'einem',
    'the', 'a', 'an',
})


def _tokenize(s: str) -> list[str]:
    """Split on whitespace/comma, lowercase, strip outer punctuation."""
    parts = re.split(r'[\s,]+', s.lower().strip())
    return [p.strip('.,;:!?') for p in parts if p.strip('.,;:!?')]


def _canonical_per(word: str) -> str:
    tokens = _tokenize(word)
    tokens = [t for t in tokens if t not in _ARTICLES and t not in _TITLES]
    return ' '.join(tokens)


def _canonical_org(word: str) -> str:
    tokens = _tokenize(word)
    tokens = [t for t in tokens if t not in _ARTICLES and t not in _ORG_TOKENS]
    return ' '.join(tokens)


def canonical_key(entity: DetectedEntity) -> str:
    """Compute a normalized key for entity matching.

    For PER: strips titles (Dr., Mag., Frau, etc.) and articles.
    For ORG: strips legal forms (GmbH, AG, etc.) and articles.
    For other types: lowercase only.

    If stripping removes all tokens, falls back to the lowercased
    original word so the entity remains identifiable.

    Args:
        entity: The detected entity.

    Returns:
        Canonical key (lowercase). Empty string if entity word is empty.
    """
    word = entity.word.strip()
    if not word:
        return ""

    group = entity.entity_group

    if group == 'PER':
        key = _canonical_per(word)
    elif group in ('ORG', 'ORG_DETECTED'):
        key = _canonical_org(word)
    else:
        key = word.lower().strip()

    return key if key else word.lower()


def _phonetic_tokens(key: str) -> list[str]:
    """Encode each token of a canonical key to its Kölner Phonetik code."""
    return [cologne_phonetic(tok) for tok in key.split() if tok]


def resolve_entities(entities: list[DetectedEntity]) -> list[str]:
    """Compute canonical keys with partial PER matching.

    Three passes:
    1. Compute the canonical key per entity (title/suffix/article stripping).
    2. Link single-token PER mentions to multi-token PER mentions by
       literal substring match, but only when unambiguous.
    3. Phonetic fallback — if literal match failed, compare Kölner
       Phonetik codes so "Mueller" links to "Müller Huber" and
       "Meier" links to "Mayer".

    Args:
        entities: List of detected entities.

    Returns:
        Parallel list of canonical keys (same length as entities).
    """
    keys = [canonical_key(e) for e in entities]

    # Collect distinct multi-token PER keys (full names)
    multi_token_per: list[str] = []
    for i, e in enumerate(entities):
        if e.entity_group == 'PER' and ' ' in keys[i] and keys[i] not in multi_token_per:
            multi_token_per.append(keys[i])

    # Precompute phonetic codes for multi-token keys
    multi_phonetic = {m: _phonetic_tokens(m) for m in multi_token_per}

    # Link single-token PER mentions to a unique multi-token match
    for i, e in enumerate(entities):
        if e.entity_group != 'PER':
            continue
        single = keys[i]
        if not single or ' ' in single:
            continue

        # Literal match first
        candidates = [m for m in multi_token_per if single in m.split()]
        if len(candidates) == 1:
            keys[i] = candidates[0]
            continue
        if len(candidates) > 1:
            continue  # ambiguous — don't link

        # Phonetic fallback: compare encoded codes
        single_code = cologne_phonetic(single)
        if not single_code:
            continue
        phonetic_candidates = [
            m for m, codes in multi_phonetic.items()
            if single_code in codes
        ]
        if len(phonetic_candidates) == 1:
            keys[i] = phonetic_candidates[0]

    return keys
