"""
Adversarial text normalization for PII detection.

Normalizes text to prevent obfuscation tricks from bypassing
PII detection:
- Zero-width characters that split entity names
- Cyrillic/Greek lookalikes (homoglyphs) replacing Latin chars
- Unicode compatibility forms (fullwidth, ligatures)
- Excessive whitespace
"""

import re
import unicodedata

# Zero-width and invisible characters to remove
_INVISIBLE_CHARS = frozenset({
    '\u200b',  # Zero-width space
    '\u200c',  # Zero-width non-joiner
    '\u200d',  # Zero-width joiner
    '\u200e',  # Left-to-right mark
    '\u200f',  # Right-to-left mark
    '\u00ad',  # Soft hyphen
    '\u2060',  # Word joiner
    '\u2061',  # Function application
    '\u2062',  # Invisible times
    '\u2063',  # Invisible separator
    '\u2064',  # Invisible plus
    '\ufeff',  # Zero-width no-break space (BOM)
})

# Cyrillic/Greek → Latin homoglyph mapping
_HOMOGLYPHS: dict[str, str] = {
    # Cyrillic lowercase
    '\u0430': 'a',  # а
    '\u0441': 'c',  # с
    '\u0435': 'e',  # е
    '\u043e': 'o',  # о
    '\u0440': 'p',  # р
    '\u0445': 'x',  # х
    '\u0443': 'y',  # у
    '\u0456': 'i',  # і (Ukrainian)
    '\u0458': 'j',  # ј (Serbian)
    '\u0455': 's',  # ѕ (Macedonian)
    # Cyrillic uppercase
    '\u0410': 'A',  # А
    '\u0412': 'B',  # В
    '\u0421': 'C',  # С
    '\u0415': 'E',  # Е
    '\u041d': 'H',  # Н
    '\u041a': 'K',  # К
    '\u041c': 'M',  # М
    '\u041e': 'O',  # О
    '\u0420': 'P',  # Р
    '\u0422': 'T',  # Т
    '\u0425': 'X',  # Х
    '\u0406': 'I',  # І (Ukrainian)
    '\u0408': 'J',  # Ј (Serbian)
    '\u0405': 'S',  # Ѕ (Macedonian)
    # Greek lookalikes
    '\u03bf': 'o',  # ο (omicron)
    '\u039f': 'O',  # Ο (Omicron)
}

# Multiple spaces/tabs → single space (preserves newlines)
_MULTI_SPACE = re.compile(r'[ \t]+')


def remove_invisible(text: str) -> str:
    """Remove zero-width and invisible Unicode characters."""
    return ''.join(c for c in text if c not in _INVISIBLE_CHARS)


def replace_homoglyphs(text: str) -> str:
    """Replace Cyrillic/Greek lookalikes with Latin equivalents."""
    return ''.join(_HOMOGLYPHS.get(c, c) for c in text)


def normalize_unicode(text: str) -> str:
    """Apply NFKC normalization (compatibility decomposition + composition).

    Handles fullwidth characters, compatibility forms, and composed
    accented characters.
    """
    return unicodedata.normalize('NFKC', text)


def normalize_whitespace(text: str) -> str:
    """Collapse runs of spaces/tabs to a single space. Preserves newlines."""
    return _MULTI_SPACE.sub(' ', text)


def normalize_adversarial(text: str) -> str:
    """Full adversarial normalization pipeline.

    Order:
    1. Remove invisible chars (before they interfere with other steps)
    2. NFKC normalization (fullwidth, ligatures, compatibility forms)
    3. Homoglyph replacement (after NFKC to catch composed forms)
    4. Whitespace normalization

    Args:
        text: Input text, potentially containing adversarial tricks.

    Returns:
        Normalized text safe for PII detection.
    """
    text = remove_invisible(text)
    text = normalize_unicode(text)
    text = replace_homoglyphs(text)
    text = normalize_whitespace(text)
    return text
