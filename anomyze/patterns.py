"""
Detection patterns for Anomyze.

Contains:
- Company context patterns for perplexity-based detection
- Normal context words (false positive filter)
- Entity blacklist (words that should never be detected)
- Regex patterns for emails, titles, labels
"""

import re
from typing import List, Tuple, Optional, Dict, Any

# Patterns that often precede company names
# Format: (regex_pattern, description, include_suffix)
COMPANY_CONTEXT_PATTERNS: List[Tuple[str, str, Optional[str]]] = [
    (r'\b[Bb]ei\s+uns\s+(?:in\s+)?(?:der\s+|dem\s+)?(\w+)', 'nach "bei uns in"', None),
    (r'\b[Aa]rbeite[tn]?\s+(?:bei|für)\s+(?:der\s+|dem\s+)?(\w+)', 'nach "arbeite bei"', None),
    (r'\b[Bb]ei\s+(?:der\s+|dem\s+)?(\w+)\s+(?:arbeite|angestellt|beschäftigt)', 'vor "arbeite/angestellt"', None),
    (r'\b[Kk]unde[n]?\s+(?:der\s+|dem\s+|von\s+)?(\w+)', 'nach "Kunde"', None),
    (r'\b[Pp]artner\s+(?:der\s+|dem\s+|von\s+)?(\w+)', 'nach "Partner"', None),
    (r'\b[Ll]ieferant(?:en)?\s+(?:der\s+|dem\s+|von\s+)?(\w+)', 'nach "Lieferant"', None),
    (r'\b[Ff]irma\s+(\w+)', 'nach "Firma"', None),
    (r'\b[Uu]nternehmen\s+(\w+)', 'nach "Unternehmen"', None),
    (r'\b(?:der|die|das)\s+(\w+)\s+(?:AG|GmbH|SE|KG|OG|eG)\b', 'vor AG/GmbH/etc', None),
    (r'\b[Vv]on\s+(?:der\s+)?(\w+)\s+(?:bekommen|erhalten|gehört)', 'nach "von X bekommen"', None),
    (r'\b[Zz]ur\s+(\w+)\s+(?:gewechselt|gegangen|gekommen)', 'nach "zur X gewechselt"', None),
    (r'\b[Bb]ei\s+(\w+)\s+(?:angefangen|gestartet|begonnen)', 'nach "bei X angefangen"', None),
    # Stores and shopping patterns
    (r'\b[Bb]ei\s+(\w+)\s+(?:einkaufen|eingekauft|shoppen|kaufen|gekauft)', 'nach "bei X einkaufen"', None),
    (r'\b[Ii]m\s+(\w+)\s+(?:einkaufen|eingekauft|shoppen|kaufen|gekauft)', 'nach "im X einkaufen"', None),
    (r'\b[Zz]um\s+(\w+)\s+(?:gehen|gegangen|fahren|gefahren)', 'nach "zum X gehen"', None),
    # Delivery and business patterns
    (r'\b[Ll]ieferung\s+(?:an|für|nach)\s+(?:die\s+|den\s+|das\s+)?(\w+)', 'nach "Lieferung an X"', None),
    (r'\b[Bb]estellung\s+(?:von|bei|für)\s+(?:der\s+|dem\s+)?(\w+)', 'nach "Bestellung von X"', None),
    (r'\b[Aa]n\s+(\w+)\s+(?:liefern|geliefert|senden|geschickt|soll)', 'nach "an X liefern"', None),
    # Work role patterns
    (r'\b[Bb]ei\s+(\w+)\s+als\s+\w+\s+(?:arbeite|arbeitet|arbeiten|tätig|angestellt)', 'nach "bei X als [role]"', None),
    (r'\b[Dd]er\s+bei\s+(\w+)\s+(?:arbeite|arbeitet|arbeiten|tätig|angestellt)', 'nach "der bei X arbeitet"', None),
    (r'\b[Dd]ie\s+bei\s+(\w+)\s+(?:arbeite|arbeitet|arbeiten|tätig|angestellt)', 'nach "die bei X arbeitet"', None),
    # Banks and financial institutions
    (r'\b(?:der|die|von\s+der)\s+(\w+)\s+([Bb]ank)\b', 'X Bank', 'Bank'),
    (r'\b(\w+)\s+([Bb]ank)\b', 'X Bank', 'Bank'),
    (r'\b(\w+)\s+([Vv]ersicherung)\b', 'X Versicherung', 'Versicherung'),
    (r'\b(\w+)\s+([Ss]parkasse)\b', 'X Sparkasse', 'Sparkasse'),
    (r'\b(\w+)\s+([Zz]entrale)\b', 'X Zentrale', 'Zentrale'),
    # Austrian/German banks without "Bank" suffix
    (r'\b(?:der|die|bei\s+der|in\s+der)\s+(Raiffeisen|Erste|BAWAG|Volksbank|Oberbank)\b', 'Bankname', None),
]

# Words that are normal in these contexts (not company names)
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

# Words that should NEVER be detected as entities (false positive filter)
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
    # Multi-word false positives (without spaces for matching after space removal)
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
    # E-Mail variations (with various spacing)
    'seine e-mail', 'seine e - mail', 'seine email', 'seine mail',
    'seinee-mail', 'seineemail',
    'ihre e-mail', 'ihre email', 'ihreemail',
    'meine e-mail', 'meine email', 'meineemail',
    'e-mail', 'e - mail', 'email', 'mail',
    'nächster', 'nächste', 'nächstes', 'letzter', 'letzte', 'letztes',
    # Short fragments that are often subword errors
    'te', 'er', 'en', 'el', 'ho', 'an', 'in', 'um', 'zu',
}


# Compiled regex patterns for performance
EMAIL_PATTERN = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')

TITLED_NAME_PATTERN = re.compile(
    r'\b(?:Herrn?|Frau)\.?\s+(?:(?:Dr|Prof|Mag|Ing|Dipl|DI|DDr)\.?\s+)*'
    r'([A-ZÄÖÜ][a-zäöüß]+(?:\s+[A-ZÄÖÜ][a-zäöüß]+)?)'
)

LABELED_NAME_PATTERN = re.compile(
    r'\b(?:Protokollführer|Schriftführer|Verfasser|Autor|Erstellt von|'
    r'Bearbeiter|Verantwortlich|Kontakt)(?:in)?:\s*'
    r'([A-ZÄÖÜ][a-zäöüß]+(?:\s+[A-ZÄÖÜ][a-zäöüß]+)?)'
)

# IBAN pattern (German/Austrian format)
IBAN_PATTERN = re.compile(r'\b[A-Z]{2}\d{2}\s?(?:\d{4}\s?){4,7}\d{1,4}\b')

# Phone patterns (German/Austrian)
PHONE_PATTERN = re.compile(
    r'(?:\+\d{1,3}[\s.-]?)?\(?\d{2,5}\)?[\s.-]?\d{3,10}(?:[\s.-]?\d{2,10})?'
)


def find_emails_regex(text: str) -> List[Dict[str, Any]]:
    """Find email addresses using regex."""
    entities = []
    for match in EMAIL_PATTERN.finditer(text):
        entities.append({
            'word': match.group(),
            'entity_group': 'EMAIL',
            'score': 0.99,
            'start': match.start(),
            'end': match.end(),
            'source': 'regex'
        })
    return entities


def find_titled_names_regex(text: str) -> List[Dict[str, Any]]:
    """Find person names with titles like 'Herrn Schmidt', 'Frau Mag. Elisabeth Steiner'."""
    entities = []
    for match in TITLED_NAME_PATTERN.finditer(text):
        name = match.group(1)
        entities.append({
            'word': name,
            'entity_group': 'PER',
            'score': 0.95,
            'start': match.start(1),
            'end': match.end(1),
            'source': 'regex_title'
        })
    return entities


def find_labeled_names_regex(text: str) -> List[Dict[str, Any]]:
    """Find person names after labels like 'Protokollführer:', 'Teilnehmer:'."""
    entities = []
    for match in LABELED_NAME_PATTERN.finditer(text):
        name = match.group(1)
        entities.append({
            'word': name,
            'entity_group': 'PER',
            'score': 0.95,
            'start': match.start(1),
            'end': match.end(1),
            'source': 'regex_label'
        })
    return entities


def find_ibans_regex(text: str) -> List[Dict[str, Any]]:
    """Find IBAN numbers using regex."""
    entities = []
    for match in IBAN_PATTERN.finditer(text):
        entities.append({
            'word': match.group(),
            'entity_group': 'IBAN',
            'score': 0.99,
            'start': match.start(),
            'end': match.end(),
            'source': 'regex'
        })
    return entities


def is_blacklisted(word: str) -> bool:
    """Check if a word is in the entity blacklist."""
    word_clean = word.lower().replace(' - ', '-').replace(' ', '')
    return word_clean in ENTITY_BLACKLIST or len(word) < 3
