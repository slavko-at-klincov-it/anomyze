"""Austrian-specific PII recognizers using the Presidio-compatible API.

Includes Austrian PII types not yet covered by the regex layer (e.g.,
Firmenbuchnummer) and demonstrates context-aware confidence scoring.
"""

import re

from stdnum import bic as stdnum_bic
from stdnum import iban as stdnum_iban
from stdnum.at import uid as stdnum_uid
from stdnum.at import vnr as stdnum_vnr

from anomyze.patterns.art9 import ART9_LEXICONS
from anomyze.patterns.at_names import is_at_firstname, is_at_lastname
from anomyze.patterns.healthcare import is_icd10_code
from anomyze.pipeline.recognizers.base import (
    Pattern,
    PatternRecognizer,
    RecognizerResult,
)


class ATSVNRRecognizer(PatternRecognizer):
    """Austrian Sozialversicherungsnummer (10 digits, last 6 = DDMMYY).

    Validation uses the official Austrian check digit algorithm (MOD-11
    weighted sum) via ``stdnum.at.vnr``; invalid birth dates and invalid
    check digits are both rejected.
    """

    supported_entity = "AT_SVNR"
    patterns = [
        Pattern(name="svnr_with_space", regex=r"\b\d{4}\s\d{6}\b", score=0.85),
        Pattern(name="svnr_no_space", regex=r"\b\d{10}\b", score=0.55),
    ]
    context = ["svnr", "sozialversicherung", "versicherungsnummer", "sv-nr"]

    def _is_valid_match(
        self, matched: str, full_text: str, start: int, end: int
    ) -> bool:
        return bool(stdnum_vnr.is_valid(matched))


class ATIBANRecognizer(PatternRecognizer):
    """Austrian IBAN: AT + 2 check digits + 16 digits (BLZ + account).

    Validation uses the ISO 13616 MOD-97 check via ``stdnum.iban`` to
    reject typo'd or fabricated IBANs that happen to match the format.
    """

    supported_entity = "AT_IBAN"
    patterns = [
        Pattern(
            name="at_iban_grouped",
            regex=r"\bAT\d{2}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\b",
            score=0.9,
        ),
    ]
    context = ["iban", "konto", "bankverbindung", "kontonummer"]

    def _is_valid_match(
        self, matched: str, full_text: str, start: int, end: int
    ) -> bool:
        return bool(stdnum_iban.is_valid(matched))


# Austrian Bundesland and Bezirk codes for license plates.
# Source: anomyze.patterns.vehicles
_AT_KFZ_CODES = (
    'W|S|K|B|T|V'
    '|NÖ|OÖ|ST'
    '|AM|BA|BL|BN|BR|BZ|DL|EF|EU|FB|FE|FF|FR|GD|GF|GM|GR|GS|GU'
    '|HA|HB|HE|HF|HO|IL|IM|JE|JO|JU|KB|KF|KG|KI|KL|KO|KR|KS'
    '|LA|LB|LE|LF|LI|LL|LN|LZ|MA|MD|ME|MI|MK|MT|MU|MZ'
    '|NA|NK|ND|OW|OP|PE|PL|PT|RA|RE|RI|RO|SB|SD|SE|SL|SO|SP|SR|SV|SW|SZ'
    '|TA|TU|UU|VB|VI|VK|VL|VO|WB|WE|WK|WL|WN|WT|WU|WY|ZE|ZT|ZW'
)


class ATKFZRecognizer(PatternRecognizer):
    """Austrian license plate (Bundesland/Bezirk code + digits + letters)."""

    supported_entity = "AT_KFZ"
    patterns = [
        Pattern(
            name="kfz",
            regex=r'\b(?:' + _AT_KFZ_CODES + r')\s?[-]?\s?\d{1,6}\s?[A-Z]{1,3}\b',
            score=0.85,
        ),
    ]
    context = ["kennzeichen", "auto", "fahrzeug", "kfz", "wagen"]


class ATUIDRecognizer(PatternRecognizer):
    """Austrian VAT number (UID / Umsatzsteuer-Identifikationsnummer).

    Format: ``ATU`` followed by 8 digits; the last digit is a MOD-11
    check digit. Validated via ``stdnum.at.uid``.
    """

    supported_entity = "AT_UID"
    patterns = [
        Pattern(name="atu", regex=r"\bATU\s?\d{8}\b", score=0.9),
    ]
    context = [
        "uid",
        "umsatzsteuer-identifikationsnummer",
        "ust-id",
        "ust.-nr",
        "vat",
    ]

    def _is_valid_match(
        self, matched: str, full_text: str, start: int, end: int
    ) -> bool:
        return bool(stdnum_uid.is_valid(matched))


class ATBICRecognizer(PatternRecognizer):
    """Business Identifier Code (BIC / SWIFT).

    Format: 4 letters (bank) + 2 letters (country) + 2 alphanumerics
    (location) + optional 3 alphanumerics (branch). Validated via
    ``stdnum.bic``, which checks the country-code component.
    """

    supported_entity = "BIC"
    patterns = [
        Pattern(name="bic", regex=r"\b[A-Z]{4}[A-Z]{2}[A-Z0-9]{2}(?:[A-Z0-9]{3})?\b", score=0.55),
    ]
    # BIC without context is highly prone to FPs because the 8-char
    # all-caps shape overlaps with common acronyms.
    context = ["bic", "swift", "bankleitzahl"]
    context_boost = 0.35

    def _is_valid_match(
        self, matched: str, full_text: str, start: int, end: int
    ) -> bool:
        # BIC codes are always written in uppercase per ISO 9362.
        # Without this gate, IGNORECASE matching causes German words
        # like "Religion" or "Bankhaus" to slip through stdnum's
        # purely structural check (4 letters + valid country code +
        # 2 alphanumerics).
        if matched != matched.upper():
            return False
        return bool(stdnum_bic.is_valid(matched))


class ATFirmenbuchRecognizer(PatternRecognizer):
    """Austrian Firmenbuchnummer: FN + 1-6 digits + check letter (a-z).

    Example: "FN 12345a", "FN 678901z". Used in the Austrian commercial
    register (Firmenbuch). Not previously covered by the regex layer.
    """

    supported_entity = "AT_FIRMENBUCH"
    patterns = [
        Pattern(name="fn_full", regex=r"\bFN\s?\d{1,6}\s?[a-z]\b", score=0.9),
    ]
    # "fn" is NOT a context word: the FN prefix is already part of the
    # match itself, so including it would boost every match.
    context = ["firmenbuch", "handelsregister", "firmenbuchnummer"]


class ATPassportRecognizer(PatternRecognizer):
    """Austrian passport number: 1 letter + 7 digits.

    Example: "P1234567". Without context the score is low because the
    pattern is broad; context words ("Reisepass", "Passnummer") boost it.
    """

    supported_entity = "AT_PASSPORT"
    patterns = [
        Pattern(name="passport", regex=r"\b[A-Z]\d{7}\b", score=0.5),
    ]
    context = ["reisepass", "passnummer", "passport", "pass-nr", "pass nr"]


class ATAktenzahlRecognizer(PatternRecognizer):
    """Austrian Aktenzahl/Geschäftszahl with GZ/Az/Zl prefix.

    Examples: "GZ 2024-1234", "Az. BMI-1/123/2024", "Zl 567/2023".
    """

    supported_entity = "AT_AKTENZAHL"
    patterns = [
        Pattern(
            name="gz",
            regex=r"\b(?:GZ|Az|Zl)\.?\s?[A-Z]?[A-Z0-9]+(?:[-/.][A-Z0-9]+)*\b",
            score=0.85,
        ),
    ]
    context = ["geschäftszahl", "aktenzahl", "akt", "verfahrenszahl"]


class ATFuehrerscheinRecognizer(PatternRecognizer):
    """Austrian driving-licence number (post-2006 scheckkarten format).

    Shape is a bare 8-digit number, so we require medical- or
    administrative-context to avoid collisions with other eight-digit
    identifiers. Match is dropped when no context word is nearby.
    """

    supported_entity = "AT_FUEHRERSCHEIN"
    patterns = [
        Pattern(name="fs_8", regex=r"\b\d{8}\b", score=0.45),
    ]
    context = [
        "führerschein",
        "fuehrerschein",
        "fs-nr",
        "fs nr",
        "lenkberechtigung",
        "driving licence",
        "driver licence",
    ]
    context_boost = 0.4

    def _is_valid_match(
        self, matched: str, full_text: str, start: int, end: int
    ) -> bool:
        return self._has_context(full_text, start, end)


class ATZMRRecognizer(PatternRecognizer):
    """ZMR-Kennzahl (Zentrales Melderegister personal identifier).

    Canonical form is 12 digits, optionally grouped ``XXX XXX XXX XXX``.
    Context-only to avoid collisions with other long numeric strings.
    """

    supported_entity = "AT_ZMR"
    patterns = [
        Pattern(name="zmr_grouped", regex=r"\b\d{3}\s?\d{3}\s?\d{3}\s?\d{3}\b", score=0.55),
    ]
    context = [
        "zmr",
        "zmr-zahl",
        "zmr-kennzahl",
        "melderegister",
        "zentrales melderegister",
        "meldezahl",
    ]
    context_boost = 0.35

    def _is_valid_match(
        self, matched: str, full_text: str, start: int, end: int
    ) -> bool:
        return self._has_context(full_text, start, end)


class ATGerichtsaktenzahlRecognizer(PatternRecognizer):
    """Austrian court docket reference (e.g. ``3 Ob 123/45``).

    Senate-abbreviations in AT jurisprudence: ``Ob`` (Zivilsenat),
    ``ObS`` (Sozialrechtssachen), ``Os`` (Strafsenat), ``Nc`` (nichtige
    Sachen), ``Ra`` (arbeitsrechtliche Sachen), ``Bkd``, ``Bs``, ``Ra``.
    Format: leading docket digit(s), senate abbreviation, docket
    number with year suffix separated by ``/``.
    """

    supported_entity = "AT_GERICHTSAKTENZAHL"
    patterns = [
        Pattern(
            name="court_docket",
            regex=r"\b\d{1,3}\s(?:Ob[SaA]?|Os|Nc|Ra|Bs|Bkd|Präs|AZ)\s\d{1,4}/\d{1,3}\b",
            score=0.9,
        ),
    ]
    context = ["gericht", "urteil", "beschluss", "ogh", "vwgh", "vfgh", "landesgericht"]


class ATICD10Recognizer(PatternRecognizer):
    """ICD-10 diagnosis codes (DSGVO Art. 9 health data).

    The shape of ICD-10 is far too thin to match safely on its own —
    ``A01`` could be a room number, ``F32`` a form code, ``Z99`` a
    postal area. We therefore:

    * validate the match against the official ICD-10 chapter ranges
      (``is_icd10_code``), and
    * require a nearby medical-context word; matches without context
      are dropped entirely rather than emitted with a low score.
    """

    supported_entity = "HEALTH_DIAGNOSIS"
    patterns = [
        Pattern(
            name="icd10",
            regex=r"\b[A-TV-Z]\d{2}(?:\.\d{1,2})?\b",
            score=0.55,
        ),
    ]
    context = [
        "icd",
        "icd-10",
        "diagnose",
        "diagnosen",
        "befund",
        "anamnese",
        "arztbrief",
        "entlassungsbrief",
        "klassifikation",
        "krankheitsbild",
    ]
    context_boost = 0.35

    def _is_valid_match(
        self, matched: str, full_text: str, start: int, end: int
    ) -> bool:
        if not is_icd10_code(matched):
            return False
        # Health data is Art. 9 — require context to reduce FPs on
        # strings like "Raum A01" or part numbers.
        return self._has_context(full_text, start, end)


class ATNameRecognizer(PatternRecognizer):
    """Austrian first/last name recognition using curated name dictionary.

    Scans capitalized words and emits a result only when the word is
    an exact match (case-insensitive) against the AT first- or last-name
    dictionary. Phonetic matching is deliberately NOT applied here —
    it is too broad without context and would flag common verbs like
    "hier" or "dort" that happen to share a Kölner code with a name.
    Phonetic fuzziness is applied during entity resolution instead,
    where full-name context disambiguates matches.
    """

    supported_entity = "AT_NAME"
    patterns = [
        Pattern(
            name="capitalized",
            regex=r"\b[A-ZÄÖÜ][a-zäöüß]{2,}\b",
            score=0.0,  # actual score assigned per-match in analyze()
        ),
    ]
    _EXACT_SCORE = 0.7

    def analyze(self, text: str) -> list[RecognizerResult]:
        """Override to score only literal name-dictionary matches."""
        results: list[RecognizerResult] = []
        for compiled, _pattern in self._compiled:
            for match in compiled.finditer(text):
                word = match.group()
                if not (is_at_firstname(word) or is_at_lastname(word)):
                    continue
                results.append(RecognizerResult(
                    entity_type=self.supported_entity,
                    start=match.start(),
                    end=match.end(),
                    score=self._EXACT_SCORE,
                    text=word,
                    recognizer_name=type(self).__name__,
                ))
        return results


class ATArt9Recognizer(PatternRecognizer):
    """DSGVO Art. 9 lexicon recognizer: religion, political, union.

    Looks up curated Austrian/German term lists from ``patterns.art9``.
    Each lexicon emits its own ``entity_type`` (RELIGION, POLITICAL,
    UNION) so downstream layers — IFG ``BESONDERE_KATEGORIE`` collapse
    and KAPA ``[PRÜFEN:]`` flagging — fire correctly.

    Matching strategy:

    * Whole-word, case-insensitive.
    * Multi-word phrases (e.g. ``römisch katholisch``) are matched
      as adjacent tokens with a flexible internal whitespace pattern
      to tolerate single spaces, hyphens, and non-breaking spaces.
    * Score 0.9 — high confidence because the lexicon is curated and
      a literal hit on, say, ``römisch-katholisch`` is unambiguous.
    """

    supported_entity = "ART9"
    patterns: list[Pattern] = []

    _SCORE = 0.9

    def __init__(self) -> None:
        self._compiled_terms: list[tuple[re.Pattern[str], str]] = []
        for entity_type, terms in ART9_LEXICONS.items():
            for term in terms:
                pattern = self._term_to_regex(term)
                try:
                    compiled = re.compile(pattern, re.IGNORECASE)
                except re.error:
                    continue
                self._compiled_terms.append((compiled, entity_type))

    @staticmethod
    def _term_to_regex(term: str) -> str:
        """Compile a curated phrase into a tolerant whole-word regex."""
        parts = [re.escape(p) for p in term.split()]
        joined = r"[\s\-\u00a0]+".join(parts)
        return rf"(?<![\wäöüÄÖÜß]){joined}(?![\wäöüÄÖÜß])"

    def analyze(self, text: str) -> list[RecognizerResult]:
        results: list[RecognizerResult] = []
        seen: set[tuple[int, int]] = set()
        for compiled, entity_type in self._compiled_terms:
            for match in compiled.finditer(text):
                key = (match.start(), match.end())
                if key in seen:
                    continue
                seen.add(key)
                results.append(RecognizerResult(
                    entity_type=entity_type,
                    start=match.start(),
                    end=match.end(),
                    score=self._SCORE,
                    text=match.group(),
                    recognizer_name=type(self).__name__,
                ))
        return results
