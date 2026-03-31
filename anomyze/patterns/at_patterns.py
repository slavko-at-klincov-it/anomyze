"""
Austrian-specific detection patterns for Anomyze.

Contains:
- Company context patterns for perplexity-based detection
- Normal context words (false positive filter)
- Entity blacklist (words that should never be detected)
- Regex patterns and finder functions for Austrian PII:
  - Email addresses
  - Person names (titled, labeled)
  - IBAN (AT format)
  - Sozialversicherungsnummer (SVNr)
  - Steuernummer
  - Geburtsdatum
  - Aktenzahlen / Geschaeftszahlen
  - Reisepass / Personalausweis
  - KFZ-Kennzeichen
  - Telefonnummern (Austrian formats)
"""

import re
from typing import List, Tuple, Optional, Dict, Any

from anomyze.pipeline import DetectedEntity


# ---------------------------------------------------------------------------
# Company context patterns for perplexity-based detection
# Format: (regex_pattern, description, include_suffix)
# ---------------------------------------------------------------------------
COMPANY_CONTEXT_PATTERNS: List[Tuple[str, str, Optional[str]]] = [
    (r'\b[Bb]ei\s+uns\s+(?:in\s+)?(?:der\s+|dem\s+)?(\w+)', 'nach "bei uns in"', None),
    (r'\b[Aa]rbeite[tn]?\s+(?:bei|für)\s+(?:der\s+|dem\s+)?(\w+)', 'nach "arbeite bei"', None),
    (r'\b[Bb]ei\s+(?:der\s+|dem\s+)?(\w+)\s+(?:arbeite|angestellt|beschäftigt)',
     'vor "arbeite/angestellt"', None),
    (r'\b[Kk]unde[n]?\s+(?:der\s+|dem\s+|von\s+)?(\w+)', 'nach "Kunde"', None),
    (r'\b[Pp]artner\s+(?:der\s+|dem\s+|von\s+)?(\w+)', 'nach "Partner"', None),
    (r'\b[Ll]ieferant(?:en)?\s+(?:der\s+|dem\s+|von\s+)?(\w+)', 'nach "Lieferant"', None),
    (r'\b[Ff]irma\s+(\w+)', 'nach "Firma"', None),
    (r'\b[Uu]nternehmen\s+(\w+)', 'nach "Unternehmen"', None),
    (r'\b(?:der|die|das)\s+(\w+)\s+(?:AG|GmbH|SE|KG|OG|eG)\b', 'vor AG/GmbH/etc', None),
    (r'\b[Vv]on\s+(?:der\s+)?(\w+)\s+(?:bekommen|erhalten|gehört)',
     'nach "von X bekommen"', None),
    (r'\b[Zz]ur\s+(\w+)\s+(?:gewechselt|gegangen|gekommen)',
     'nach "zur X gewechselt"', None),
    (r'\b[Bb]ei\s+(\w+)\s+(?:angefangen|gestartet|begonnen)',
     'nach "bei X angefangen"', None),
    # Stores and shopping patterns
    (r'\b[Bb]ei\s+(\w+)\s+(?:einkaufen|eingekauft|shoppen|kaufen|gekauft)',
     'nach "bei X einkaufen"', None),
    (r'\b[Ii]m\s+(\w+)\s+(?:einkaufen|eingekauft|shoppen|kaufen|gekauft)',
     'nach "im X einkaufen"', None),
    (r'\b[Zz]um\s+(\w+)\s+(?:gehen|gegangen|fahren|gefahren)',
     'nach "zum X gehen"', None),
    # Delivery and business patterns
    (r'\b[Ll]ieferung\s+(?:an|für|nach)\s+(?:die\s+|den\s+|das\s+)?(\w+)',
     'nach "Lieferung an X"', None),
    (r'\b[Bb]estellung\s+(?:von|bei|für)\s+(?:der\s+|dem\s+)?(\w+)',
     'nach "Bestellung von X"', None),
    (r'\b[Aa]n\s+(\w+)\s+(?:liefern|geliefert|senden|geschickt|soll)',
     'nach "an X liefern"', None),
    # Work role patterns
    (r'\b[Bb]ei\s+(\w+)\s+als\s+\w+\s+(?:arbeite|arbeitet|arbeiten|tätig|angestellt)',
     'nach "bei X als [role]"', None),
    (r'\b[Dd]er\s+bei\s+(\w+)\s+(?:arbeite|arbeitet|arbeiten|tätig|angestellt)',
     'nach "der bei X arbeitet"', None),
    (r'\b[Dd]ie\s+bei\s+(\w+)\s+(?:arbeite|arbeitet|arbeiten|tätig|angestellt)',
     'nach "die bei X arbeitet"', None),
    # Banks and financial institutions
    (r'\b(?:der|die|von\s+der)\s+(\w+)\s+([Bb]ank)\b', 'X Bank', 'Bank'),
    (r'\b(\w+)\s+([Bb]ank)\b', 'X Bank', 'Bank'),
    (r'\b(\w+)\s+([Vv]ersicherung)\b', 'X Versicherung', 'Versicherung'),
    (r'\b(\w+)\s+([Ss]parkasse)\b', 'X Sparkasse', 'Sparkasse'),
    (r'\b(\w+)\s+([Zz]entrale)\b', 'X Zentrale', 'Zentrale'),
    # Austrian/German banks without "Bank" suffix
    (r'\b(?:der|die|bei\s+der|in\s+der)\s+'
     r'(Raiffeisen|Erste|BAWAG|Volksbank|Oberbank)\b', 'Bankname', None),
]

# ---------------------------------------------------------------------------
# Normal context words (not company names)
# ---------------------------------------------------------------------------
NORMAL_CONTEXT_WORDS: set = {
    'uns', 'mir', 'dir', 'ihm', 'ihr', 'ihnen', 'euch',
    'hause', 'haus', 'arbeit', 'küche', 'büro', 'office',
    'abteilung', 'team', 'gruppe', 'projekt',
    'stadt', 'land', 'ort', 'gegend', 'region',
    'schule', 'universität', 'uni', 'hochschule',
    'anfang', 'ende', 'mitte', 'zeit',
    'montag', 'dienstag', 'mittwoch', 'donnerstag', 'freitag', 'samstag', 'sonntag',
    'heute', 'morgen', 'gestern',
}

# ---------------------------------------------------------------------------
# Entity blacklist (words that should NEVER be detected)
# ---------------------------------------------------------------------------
ENTITY_BLACKLIST: set = {
    # Common German words often misdetected
    'protokoll', 'workshop', 'meeting', 'termin', 'termine',
    'projektleiter', 'projektleiterin', 'leiter', 'leiterin',
    'abteilung', 'it-abteilung', 'it', 'hr', 'pr',
    'e-mail', 'email', 'mail', 'tel', 'telefon', 'telefonnummer',
    'januar', 'februar', 'märz', 'april', 'mai', 'juni',
    'juli', 'august', 'september', 'oktober', 'november', 'dezember',
    'jan', 'feb', 'mär', 'apr', 'jun', 'jul', 'aug', 'sep', 'okt', 'nov', 'dez',
    'montag', 'dienstag', 'mittwoch', 'donnerstag', 'freitag', 'samstag', 'sonntag',
    'uhr', 'zeit', 'datum', 'tag', 'woche', 'monat', 'jahr',
    'teilnehmer', 'teilnehmerin', 'kunde', 'kundin', 'kunden',
    'kontakt', 'erreichbar', 'büro', 'office', 'zentrale',
    'seine', 'ihre', 'der', 'die', 'das', 'von', 'vom', 'unter',
    # Titles (should not be detected alone)
    'herr', 'herrn', 'frau', 'dr', 'dr.', 'mag', 'mag.', 'prof', 'prof.',
    'ing', 'ing.', 'dipl', 'dipl.', 'dkfm', 'dkfm.',
    # Document/meeting words
    'teambesprechung', 'besprechung', 'sitzung', 'konferenz',
    'protokollführer', 'protokollführerin', 'schriftführer',
    'kontaktdaten', 'ansprechpartner', 'ansprechpartnerin',
    'weiters', 'außerdem', 'zusätzlich', 'ferner',
    # Multi-word false positives
    'protokollderteambesprechung', 'seinekontaktdaten', 'ihrekontaktdaten',
    'meinekontaktdaten', 'unserekontaktdaten',
    # Role words
    'kollege', 'kollegen', 'kollegin', 'kolleginnen',
    'mitarbeiter', 'mitarbeiterin', 'mitarbeiterinnen',
    # Pronouns and common words
    'mein', 'meine', 'meiner', 'meinem', 'meinen',
    'dein', 'deine', 'deiner', 'deinem', 'deinen',
    'sein', 'seine', 'seiner', 'seinem', 'seinen',
    'ihr', 'ihre', 'ihrer', 'ihrem', 'ihren',
    # Common verbs and activities
    'einkaufen', 'arbeiten', 'arbeitet', 'gehen', 'kommen', 'machen',
    'kaufen', 'verkaufen', 'sprechen', 'sagen', 'fragen',
    # E-Mail variations
    'seine e-mail', 'seine e - mail', 'seine email', 'seine mail',
    'seinee-mail', 'seineemail',
    'ihre e-mail', 'ihre email', 'ihreemail',
    'meine e-mail', 'meine email', 'meineemail',
    'e-mail', 'e - mail', 'email', 'mail',
    'nächster', 'nächste', 'nächstes', 'letzter', 'letzte', 'letztes',
    # Short fragments that are often subword errors
    'te', 'er', 'en', 'el', 'ho', 'an', 'in', 'um', 'zu',
    # Austrian administrative terms (should not be detected as PII)
    'bescheid', 'beschwerde', 'stellungnahme', 'verfahren', 'antrag',
    'bundesministerium', 'ministerium', 'republik', 'österreich',
    'landesregierung', 'bezirkshauptmannschaft', 'magistrat',
}


# ---------------------------------------------------------------------------
# Compiled regex patterns
# ---------------------------------------------------------------------------

# Email
EMAIL_PATTERN = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')

# Titled names: Herrn Müller, Frau Dr. Elisabeth Steiner
TITLED_NAME_PATTERN = re.compile(
    r'\b(?:Herrn?|Frau)\.?\s+(?:(?:Dr|Prof|Mag|Ing|Dipl|DI|DDr)\.?\s+)*'
    r'([A-ZÄÖÜ][a-zäöüß]+(?:\s+[A-ZÄÖÜ][a-zäöüß]+)?)'
)

# Labeled names: Protokollführer: Max Mustermann
LABELED_NAME_PATTERN = re.compile(
    r'\b(?:Protokollführer|Schriftführer|Verfasser|Autor|Erstellt von|'
    r'Bearbeiter|Verantwortlich|Kontakt)(?:in)?:\s*'
    r'([A-ZÄÖÜ][a-zäöüß]+(?:\s+[A-ZÄÖÜ][a-zäöüß]+)?)'
)

# IBAN (international format, AT-optimized)
IBAN_PATTERN = re.compile(r'\b[A-Z]{2}\d{2}\s?(?:\d{4}\s?){3,7}\d{1,4}\b')

# Austrian Sozialversicherungsnummer: XXXX DDMMYY (10 digits)
# First 4 digits are the running number, last 6 are birthdate DDMMYY
SVNR_PATTERN = re.compile(
    r'\b(\d{4})\s?(\d{2})(\d{2})(\d{2})\b'
)

# Austrian Steuernummer: varies by Finanzamt, e.g., 12-345/6789, 123-456/7890
STEUERNUMMER_PATTERN = re.compile(
    r'\b(\d{2,3})[-/](\d{3,4})[-/](\d{4})\b'
)

# Birth dates: DD.MM.YYYY, DD-MM-YYYY, DD/MM/YYYY, D.M.YYYY
BIRTH_DATE_PATTERN = re.compile(
    r'\b(0?[1-9]|[12]\d|3[01])[.\-/](0?[1-9]|1[0-2])[.\-/]((?:19|20)\d{2})\b'
)

# Aktenzahlen / Geschaeftszahlen: GZ BMI-2024/0815, AZ BMEIA-AT.3.18/0123-III/2024
AKTENZAHL_PATTERN = re.compile(
    r'\b(?:GZ|Zl\.?|AZ)\s+[A-ZÄÖÜ][A-ZÄÖÜa-zäöü0-9.\-/]+(?:\d{2,4})'
)

# Austrian passport: letter + 7 digits (context-gated)
PASSPORT_PATTERN = re.compile(r'\b([A-Z]\d{7})\b')
PASSPORT_CONTEXT = re.compile(
    r'(?:Reisepass|Pass-?Nr\.?|Passnummer|passport)\s*:?\s*',
    re.IGNORECASE
)

# Austrian Personalausweis (ID card): context-gated
ID_CARD_PATTERN = re.compile(r'\b([A-Z0-9]{8,10})\b')
ID_CARD_CONTEXT = re.compile(
    r'(?:Personalausweis|Ausweis-?Nr\.?|Ausweisnummer|ID-?Nr\.?)\s*:?\s*',
    re.IGNORECASE
)

# Austrian KFZ-Kennzeichen
# Bundesland codes: W (Wien), NÖ, OÖ, S (Salzburg), ST (Steiermark),
# K (Kärnten), B (Burgenland), T (Tirol), V (Vorarlberg)
# Bezirk codes: 1-2 letters (e.g., AM, BA, BL, BN, BR, ...)
# Format: PREFIX-DIGITS+LETTERS or PREFIX DIGITS+LETTERS
_AT_BEZIRK_CODES = (
    # Bundesland single-letter codes
    'W|S|K|B|T|V'
    # Two-letter Bundesland codes
    '|NÖ|OÖ|ST'
    # Common Bezirk codes
    '|AM|BA|BL|BN|BR|BZ|DL|EF|EU|FB|FE|FF|FR|GD|GF|GM|GR|GS|GU'
    '|HA|HB|HE|HF|HO|IL|IM|JE|JO|JU|KB|KF|KG|KI|KL|KO|KR|KS'
    '|LA|LB|LE|LF|LI|LL|LN|LZ|MA|MD|ME|MI|MK|MT|MU|MZ'
    '|NA|NK|ND|OW|OP|PE|PL|PT|RA|RE|RI|RO|SB|SD|SE|SL|SO|SP|SR|SV|SW|SZ'
    '|TA|TU|UU|VB|VI|VK|VL|VO|WB|WE|WK|WL|WN|WT|WU|WY|ZE|ZT|ZW'
)
LICENSE_PLATE_PATTERN = re.compile(
    r'\b(' + _AT_BEZIRK_CODES + r')\s?[-]?\s?(\d{1,6})\s?([A-Z]{1,3})\b'
)

# Austrian addresses: Street + house number, optionally with PLZ + Ort
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

# Pattern A: Suffix embedded in single word (e.g., Schottenfeldgasse, Ringstraße)
_ADDR_EMBEDDED = re.compile(
    r'\b([A-ZÄÖÜ][a-zäöüß]*(?:' + _STREET_SUFFIXES_LOWER + r'))'
    r'\s+(\d{1,4}[a-z]?(?:\s?/\s?\d{1,4})*)',
    re.UNICODE,
)

# Pattern B: Prefix word(s) + standalone suffix word
# (e.g., Mariahilfer Straße, Franz-Josefs-Kai, Am Hauptplatz)
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
    r'([A-ZÄÖÜ][a-zäöüß]+(?:\s+(?:am|an|im|bei|ob|unter|in)\s+[a-zäöüß]+(?:\s+[A-ZÄÖÜ][a-zäöüß]+)?)?)',
    re.MULTILINE
)

# Austrian phone numbers: +43, 0043, or 0XXX formats
PHONE_PATTERN_AT = re.compile(
    r'(?:'
    # International format: +43 or 0043
    r'(?:\+43|0043)\s?[-./]?\s?'
    r'(?:\(?\d{1,4}\)?\s?[-./]?\s?)?'
    r'\d{3,4}\s?[-./]?\s?\d{2,6}'
    r'|'
    # Austrian mobile: 0650, 0660, 0664, 0676, 0680, 0681, 0688, 0699
    r'0(?:650|660|664|67[06]|68[018]|699)\s?[-./]?\s?\d{3,4}\s?[-./]?\s?\d{2,6}'
    r'|'
    # Austrian landline with area code: 01 (Wien), 0316 (Graz), etc.
    r'0[1-9]\d{0,3}\s?[-./]?\s?\d{3,8}'
    r')'
)


# ---------------------------------------------------------------------------
# Finder functions — each returns List[DetectedEntity]
# ---------------------------------------------------------------------------

def find_emails_regex(text: str) -> List[DetectedEntity]:
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


def find_titled_names_regex(text: str) -> List[DetectedEntity]:
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


def find_labeled_names_regex(text: str) -> List[DetectedEntity]:
    """Find person names after labels like 'Protokollführer:', 'Erstellt von:'."""
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


def find_ibans_regex(text: str) -> List[DetectedEntity]:
    """Find IBAN numbers using regex."""
    entities = []
    for match in IBAN_PATTERN.finditer(text):
        entities.append(DetectedEntity(
            word=match.group(),
            entity_group='IBAN',
            score=0.99,
            start=match.start(),
            end=match.end(),
            source='regex',
        ))
    return entities


def _validate_svnr_date(day: str, month: str, year: str) -> bool:
    """Validate the date portion of an Austrian SVNr.

    Args:
        day: DD portion (01-31).
        month: MM portion (01-12).
        year: YY portion.

    Returns:
        True if the date is plausible.
    """
    try:
        d, m = int(day), int(month)
        return 1 <= d <= 31 and 1 <= m <= 12
    except ValueError:
        return False


def find_svnr_regex(text: str) -> List[DetectedEntity]:
    """Find Austrian Sozialversicherungsnummern (SVNr).

    Format: XXXX DDMMYY — 4-digit running number + 6-digit birthdate.
    Validates that the date portion is plausible.
    """
    entities = []
    for match in SVNR_PATTERN.finditer(text):
        day, month, year = match.group(2), match.group(3), match.group(4)
        if not _validate_svnr_date(day, month, year):
            continue
        entities.append(DetectedEntity(
            word=match.group(),
            entity_group='SVN',
            score=0.95,
            start=match.start(),
            end=match.end(),
            source='regex',
        ))
    return entities


def find_tax_number_regex(text: str) -> List[DetectedEntity]:
    """Find Austrian Steuernummern.

    Format varies by Finanzamt: XX-XXX/XXXX or XXX-XXXX/XXXX.
    """
    entities = []
    for match in STEUERNUMMER_PATTERN.finditer(text):
        entities.append(DetectedEntity(
            word=match.group(),
            entity_group='STEUERNUMMER',
            score=0.90,
            start=match.start(),
            end=match.end(),
            source='regex',
        ))
    return entities


def find_birth_date_regex(text: str) -> List[DetectedEntity]:
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


def find_aktenzahl_regex(text: str) -> List[DetectedEntity]:
    """Find Austrian Aktenzahlen / Geschaeftszahlen.

    Matches administrative file numbers like GZ BMI-2024/0815,
    AZ BMEIA-AT.3.18/0123-III/2024, Zl. 12345/2024.
    """
    entities = []
    for match in AKTENZAHL_PATTERN.finditer(text):
        entities.append(DetectedEntity(
            word=match.group(),
            entity_group='AKTENZAHL',
            score=0.99,
            start=match.start(),
            end=match.end(),
            source='regex',
        ))
    return entities


def find_passport_regex(text: str) -> List[DetectedEntity]:
    """Find Austrian passport numbers (context-gated).

    Only matches when preceded by context keywords like 'Reisepass',
    'Pass-Nr', 'Passnummer' to reduce false positives.
    Format: letter + 7 digits (e.g., P1234567).
    """
    entities = []
    for ctx_match in PASSPORT_CONTEXT.finditer(text):
        # Search for passport number immediately after the context keyword
        remaining = text[ctx_match.end():]
        pp_match = PASSPORT_PATTERN.match(remaining)
        if pp_match:
            abs_start = ctx_match.end() + pp_match.start(1)
            abs_end = ctx_match.end() + pp_match.end(1)
            entities.append(DetectedEntity(
                word=pp_match.group(1),
                entity_group='REISEPASS',
                score=0.85,
                start=abs_start,
                end=abs_end,
                source='regex',
            ))
    return entities


def find_id_card_regex(text: str) -> List[DetectedEntity]:
    """Find Austrian Personalausweis numbers (context-gated).

    Only matches when preceded by context keywords like 'Personalausweis',
    'Ausweis-Nr', 'ID-Nr' to reduce false positives.
    """
    entities = []
    for ctx_match in ID_CARD_CONTEXT.finditer(text):
        remaining = text[ctx_match.end():]
        id_match = ID_CARD_PATTERN.match(remaining)
        if id_match:
            abs_start = ctx_match.end() + id_match.start(1)
            abs_end = ctx_match.end() + id_match.end(1)
            entities.append(DetectedEntity(
                word=id_match.group(1),
                entity_group='PERSONALAUSWEIS',
                score=0.85,
                start=abs_start,
                end=abs_end,
                source='regex',
            ))
    return entities


def find_license_plate_regex(text: str) -> List[DetectedEntity]:
    """Find Austrian KFZ-Kennzeichen.

    Matches Austrian license plate formats with Bundesland/Bezirk prefixes.
    Examples: W-12345A, NÖ 1234 AB, GU-567C.
    """
    entities = []
    for match in LICENSE_PLATE_PATTERN.finditer(text):
        entities.append(DetectedEntity(
            word=match.group(),
            entity_group='KFZ',
            score=0.95,
            start=match.start(),
            end=match.end(),
            source='regex',
        ))
    return entities


def find_phone_regex(text: str) -> List[DetectedEntity]:
    """Find Austrian phone numbers.

    Matches:
    - International: +43 XXX XXXXXXX, 0043 XXX XXXXXXX
    - Mobile: 0650, 0660, 0664, 0676, 0680, 0681, 0688, 0699
    - Landline: 01 (Wien), 0316 (Graz), etc.
    """
    entities = []
    for match in PHONE_PATTERN_AT.finditer(text):
        # Filter out very short matches that are likely false positives
        phone = match.group()
        digits_only = re.sub(r'\D', '', phone)
        if len(digits_only) < 7:
            continue
        entities.append(DetectedEntity(
            word=phone,
            entity_group='TELEFON',
            score=0.95,
            start=match.start(),
            end=match.end(),
            source='regex',
        ))
    return entities


def find_address_regex(text: str) -> List[DetectedEntity]:
    """Find Austrian addresses (street + house number, PLZ + Ort).

    Detects patterns like:
    - Schottenfeldgasse 29/3
    - Mariahilfer Straße 1a
    - Franz-Josefs-Kai 27
    - 1070 Wien
    - Hauptplatz 12, 8010 Graz

    Combines adjacent street + PLZ/Ort matches into a single ADRESSE entity
    when they appear together (e.g., "Straße 29/3, 1070 Wien").
    """
    entities: List[DetectedEntity] = []

    # Find street + house number matches from both patterns
    street_spans = []
    for match in _ADDR_EMBEDDED.finditer(text):
        street_spans.append((match.start(), match.end(), match.group()))
    for match in _ADDR_MULTIWORD.finditer(text):
        # Avoid duplicates if both patterns match the same span
        span = (match.start(), match.end(), match.group())
        if not any(s[0] == span[0] for s in street_spans):
            street_spans.append(span)

    # Find PLZ + Ort matches
    plz_spans = []
    for match in PLZ_ORT_PATTERN.finditer(text):
        # The actual PLZ+Ort starts at group(1), skip leading comma/whitespace
        plz_start = match.start(1)
        plz_end = match.end(2)
        plz_word = text[plz_start:plz_end]
        plz_spans.append((plz_start, plz_end, plz_word))

    # Try to merge street + PLZ/Ort if they're adjacent (within ~5 chars)
    used_plz = set()
    for s_start, s_end, s_word in street_spans:
        merged = False
        for i, (p_start, p_end, p_word) in enumerate(plz_spans):
            gap = p_start - s_end
            if 0 <= gap <= 5:
                # Adjacent: merge into one ADRESSE entity
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


def is_blacklisted(word: str) -> bool:
    """Check if a word is in the entity blacklist.

    Also filters words shorter than 3 characters.

    Args:
        word: The word to check.

    Returns:
        True if the word should be excluded from detection.
    """
    word_clean = word.lower().replace(' - ', '-').replace(' ', '')
    return word_clean in ENTITY_BLACKLIST or len(word) < 3
