"""
Adversarial text normalization for PII detection.

Normalizes text to prevent obfuscation tricks from bypassing
PII detection:
- Zero-width characters that split entity names
- Bidirectional-control overrides (``U+202A``-``U+202E``, ``U+2066``-
  ``U+2069``) that can visually mirror text
- Cyrillic/Greek/mathematical-alphabet lookalikes (homoglyphs)
  replacing Latin chars
- Unicode compatibility forms (fullwidth, ligatures)
- Excessive whitespace
- Hyphenated line-breaks that split a name across two lines
- Leetspeak digit/symbol substitution inside names (opt-in)
"""

import re
import unicodedata

# Zero-width, directional-control, and other invisible characters.
# These all have visible side-effects in rendered text but no
# information content we want to feed into detectors.
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
    # Bidirectional overrides — can be used to reverse-render PII
    '\u202a',  # LRE
    '\u202b',  # RLE
    '\u202c',  # PDF
    '\u202d',  # LRO
    '\u202e',  # RLO (classic "right-to-left override" attack)
    '\u2066',  # LRI
    '\u2067',  # RLI
    '\u2068',  # FSI
    '\u2069',  # PDI
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
    # Armenian small "o"
    '\u0585': 'o',
}

# Leetspeak mapping for selective per-name application. Applied only
# to text following an honorific trigger (``Herr``, ``Frau``, ``Dr.``,
# ``Mag.``, etc.) so we don't destroy numeric IDs like IBAN and SVNR.
_LEET_MAP: dict[str, str] = {
    '0': 'o',
    '1': 'l',
    '3': 'e',
    '4': 'a',
    '5': 's',
    '7': 't',
    '@': 'a',
    '$': 's',
}
_LEET_NAME_WINDOW = re.compile(
    r'((?:Herr|Herrn|Frau|Dr\.|Mag\.|Prof\.|Ing\.|DI|DKFM)\s+)'
    r'([A-Za-zÄÖÜäöüß0-9@\$]{2,30})'
)

# Hyphenated line-break inside a word: "Mü-\nller" → "Müller".
_HYPHENATION = re.compile(r'(\w)-[ \t]*\n(\w)')

# Multiple spaces/tabs → single space (preserves newlines)
_MULTI_SPACE = re.compile(r'[ \t]+')


def remove_invisible(text: str) -> str:
    """Remove zero-width / directional-control Unicode characters."""
    return ''.join(c for c in text if c not in _INVISIBLE_CHARS)


def replace_homoglyphs(text: str) -> str:
    """Replace Cyrillic/Greek/Armenian lookalikes with Latin equivalents."""
    return ''.join(_HOMOGLYPHS.get(c, c) for c in text)


def normalize_unicode(text: str) -> str:
    """Apply NFKC normalization (compatibility decomposition + composition).

    Handles fullwidth characters, compatibility forms, and — crucially
    — the mathematical alphanumeric alphabets (``U+1D400``…``U+1D7FF``)
    which NFKC folds to plain ASCII. ``𝐌𝐨𝐬𝐞𝐫`` therefore becomes
    ``Moser`` after this step.
    """
    return unicodedata.normalize('NFKC', text)


def normalize_whitespace(text: str) -> str:
    """Collapse runs of spaces/tabs to a single space. Preserves newlines."""
    return _MULTI_SPACE.sub(' ', text)


def rejoin_hyphenation(text: str) -> str:
    """Rejoin hyphenated words split across line breaks.

    Example: ``"Mü-\\nller"`` → ``"Müller"``. Conservative: only
    merges when both sides of the hyphen are word characters.
    """
    return _HYPHENATION.sub(r'\1\2', text)


def normalize_leetspeak_in_names(text: str) -> str:
    """Fold leetspeak substitutions in words following an honorific.

    Example: ``"Herr M0s3r"`` → ``"Herr Moser"``. Scoped to names
    (20-char window after Herr/Frau/Dr./Mag./Prof./Ing./DI/DKFM) so
    that IBAN, SVNR, phone-number and other numeric strings remain
    untouched.
    """

    def _fold(match: re.Match[str]) -> str:
        prefix, word = match.group(1), match.group(2)
        folded = ''.join(_LEET_MAP.get(ch, ch) for ch in word)
        return prefix + folded

    return _LEET_NAME_WINDOW.sub(_fold, text)


def normalize_adversarial(text: str, apply_leetspeak: bool = True) -> str:
    """Full adversarial normalization pipeline.

    Order:
    1. Remove invisible / directional-override chars
    2. Rejoin hyphenated line-breaks (before whitespace collapse)
    3. NFKC normalization (fullwidth, ligatures, math alphabets)
    4. Homoglyph replacement (catches composed forms)
    5. Leetspeak folding inside honorific-prefixed names (optional)
    6. Whitespace normalization

    Args:
        text: Input text, potentially containing adversarial tricks.
        apply_leetspeak: Whether to apply the context-gated leetspeak
            fold. Disable for text where numeric tokens must survive
            verbatim even in name contexts (rare).

    Returns:
        Normalized text safe for PII detection.
    """
    text = remove_invisible(text)
    text = rejoin_hyphenation(text)
    text = normalize_unicode(text)
    text = replace_homoglyphs(text)
    if apply_leetspeak:
        text = normalize_leetspeak_in_names(text)
    text = normalize_whitespace(text)
    return text
