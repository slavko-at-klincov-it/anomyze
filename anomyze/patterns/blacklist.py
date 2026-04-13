"""Entity blacklist for filtering false positive detections."""


ENTITY_BLACKLIST: set[str] = {
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
    'sein', 'seiner', 'seinem', 'seinen',
    'ihr', 'ihrer', 'ihrem', 'ihren',
    # Common verbs and activities
    'einkaufen', 'arbeiten', 'arbeitet', 'gehen', 'kommen', 'machen',
    'kaufen', 'verkaufen', 'sprechen', 'sagen', 'fragen',
    # E-Mail variations
    'seine e-mail', 'seine e - mail', 'seine email', 'seine mail',
    'seinee-mail', 'seineemail',
    'ihre e-mail', 'ihre email', 'ihreemail',
    'meine e-mail', 'meine email', 'meineemail',
    'e - mail', 'nächster', 'nächste', 'nächstes', 'letzter', 'letzte', 'letztes',
    # Short fragments that are often subword errors
    'te', 'er', 'en', 'el', 'ho', 'an', 'in', 'um', 'zu',
    # Austrian administrative terms (should not be detected as PII)
    'bescheid', 'beschwerde', 'stellungnahme', 'verfahren', 'antrag',
    'bundesministerium', 'ministerium', 'republik', 'österreich',
    'landesregierung', 'bezirkshauptmannschaft', 'magistrat',
}


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
