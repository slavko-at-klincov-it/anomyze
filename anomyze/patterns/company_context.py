"""Company context patterns for perplexity-based detection."""


# Format: (regex_pattern, description, include_suffix)
COMPANY_CONTEXT_PATTERNS: list[tuple[str, str, str | None]] = [
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

# Normal context words (not company names)
NORMAL_CONTEXT_WORDS: set[str] = {
    'uns', 'mir', 'dir', 'ihm', 'ihr', 'ihnen', 'euch',
    'hause', 'haus', 'arbeit', 'küche', 'büro', 'office',
    'abteilung', 'team', 'gruppe', 'projekt',
    'stadt', 'land', 'ort', 'gegend', 'region',
    'schule', 'universität', 'uni', 'hochschule',
    'anfang', 'ende', 'mitte', 'zeit',
    'montag', 'dienstag', 'mittwoch', 'donnerstag', 'freitag', 'samstag', 'sonntag',
    'heute', 'morgen', 'gestern',
}
