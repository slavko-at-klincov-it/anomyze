"""Austrian-specific PII recognizers using the Presidio-compatible API.

Includes Austrian PII types not yet covered by the regex layer (e.g.,
Firmenbuchnummer) and demonstrates context-aware confidence scoring.
"""

import re

from anomyze.patterns.at_names import is_at_firstname, is_at_lastname
from anomyze.pipeline.recognizers.base import (
    Pattern,
    PatternRecognizer,
    RecognizerResult,
)


class ATSVNRRecognizer(PatternRecognizer):
    """Austrian Sozialversicherungsnummer (10 digits, last 6 = DDMMYY)."""

    supported_entity = "AT_SVNR"
    patterns = [
        Pattern(name="svnr_with_space", regex=r"\b\d{4}\s\d{6}\b", score=0.85),
        Pattern(name="svnr_no_space", regex=r"\b\d{10}\b", score=0.55),
    ]
    context = ["svnr", "sozialversicherung", "versicherungsnummer", "sv-nr"]

    def _is_valid_match(
        self, matched: str, full_text: str, start: int, end: int
    ) -> bool:
        digits = re.sub(r"\s", "", matched)
        if len(digits) != 10:
            return False
        try:
            day = int(digits[4:6])
            month = int(digits[6:8])
            return 1 <= day <= 31 and 1 <= month <= 12
        except ValueError:
            return False


class ATIBANRecognizer(PatternRecognizer):
    """Austrian IBAN: AT + 2 check digits + 16 digits (BLZ + account)."""

    supported_entity = "AT_IBAN"
    patterns = [
        Pattern(
            name="at_iban_grouped",
            regex=r"\bAT\d{2}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\b",
            score=0.9,
        ),
    ]
    context = ["iban", "konto", "bankverbindung", "kontonummer"]


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
