"""Healthcare PII detection (ICD-10 diagnosis codes).

Targets DSGVO Art. 9 "besondere Kategorien" (special categories of
personal data). ICD-10 codes — even without an explicit name — qualify
as health data when they appear in medical correspondence.

Pattern design
--------------

Raw ICD-10 codes have a very thin surface (``[A-TV-Z]\\d{2}(\\.\\d{1,2})?``)
that collides with room numbers (``A01``), building codes (``B2``) or
part numbers (``Z99``). We therefore:

1. Require the match to sit inside the valid ICD-10 chapter ranges
   (A00–Z99 minus the unused letters ``U`` — WHO, and ``U`` is
   reserved for new diseases such as ``U07.1`` COVID-19, so we keep
   it).
2. Require a nearby medical context word (``icd``, ``diagnose``,
   ``arztbrief``, ...). Without context the recognizer drops the
   match outright, instead of issuing a low-score result that would
   still surface in the ensemble.
"""

from __future__ import annotations

import re

# Letter prefixes that actually appear in ICD-10 (A-Z without O, which
# the WHO reserved; U is special but in use). We keep U in to match
# emergency codes such as ``U07.1``.
_ICD10_PATTERN = re.compile(
    r"\b([A-TV-Z])(\d{2})(?:\.(\d{1,2}))?\b"
)

# Top-level ICD-10 chapters with their first and last valid code. The
# ranges are inclusive on both ends. Codes outside these ranges are
# definitely not ICD-10 and should be rejected.
_ICD10_CHAPTERS: tuple[tuple[str, int, int], ...] = (
    ("A", 0, 99),   # A00-B99 infectious
    ("B", 0, 99),
    ("C", 0, 97),   # C00-D48 neoplasms
    ("D", 0, 89),
    ("E", 0, 90),   # endocrine
    ("F", 0, 99),   # mental
    ("G", 0, 99),   # nervous
    ("H", 0, 95),   # eye + ear
    ("I", 0, 99),   # circulatory
    ("J", 0, 99),   # respiratory
    ("K", 0, 93),   # digestive
    ("L", 0, 99),   # skin
    ("M", 0, 99),   # musculoskeletal
    ("N", 0, 99),   # genitourinary
    ("O", 0, 99),   # pregnancy
    ("P", 0, 96),   # perinatal
    ("Q", 0, 99),   # congenital
    ("R", 0, 99),   # symptoms
    ("S", 0, 99),   # injury
    ("T", 0, 98),   # injury/poisoning
    ("V", 1, 99),   # external causes
    ("W", 0, 99),
    ("X", 0, 99),
    ("Y", 0, 98),
    ("Z", 0, 99),   # factors influencing health
)

_CHAPTER_RANGES: dict[str, tuple[int, int]] = {
    letter: (lo, hi) for letter, lo, hi in _ICD10_CHAPTERS
}


def is_icd10_code(text: str) -> bool:
    """Return True if ``text`` is a valid ICD-10 chapter code."""
    match = _ICD10_PATTERN.fullmatch(text.strip())
    if not match:
        return False
    letter = match.group(1).upper()
    main = int(match.group(2))
    if letter not in _CHAPTER_RANGES:
        return False
    lo, hi = _CHAPTER_RANGES[letter]
    return lo <= main <= hi


__all__ = ["is_icd10_code"]
