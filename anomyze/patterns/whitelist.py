"""Whitelist for Austrian legal references and government bodies.

Entities that match the whitelist are detected normally by NER / regex
but are NOT redacted. They are public-domain references that do not
identify a private individual: paragraph citations, statute
abbreviations, and well-known federal and regional authorities.

Distinction from ``blacklist.py``:

* Blacklist: stop-words that should never be *flagged* as PII in the
  first place (e.g., "Protokoll", "Meeting"). Applied inside
  recognizers / NER filters.
* Whitelist: entities that *were* flagged (often as ORG or LOC) but
  should be left intact in the output (e.g.,
  "Bundesministerium für Inneres", "ASVG"). Applied after the
  ensemble merge, before channel formatting.

Precedence: if a person's name sits *inside* a whitelisted authority
name ("Bundesministerium für Inneres, Karl Nehammer"), the Nehammer
span is still its own PER entity and remains redacted. Whitelist
operates per-entity, not on arbitrary substrings.
"""

from __future__ import annotations

import re

from anomyze.pipeline import DetectedEntity

# Paragraph and article citations: "§ 123", "§ 123a", "§ 123 Abs. 2",
# "§ 123 Abs. 2 Z 3", "Art. 5", "Artikel 5 Abs. 2", etc.
LEGAL_PARAGRAPHS = re.compile(
    r"^§+\s*\d+[a-z]?(?:\s*Abs\.?\s*\d+)?(?:\s*Z(?:iffer|iff\.?)?\s*\d+)?$"
    r"|^Art(?:ikel|\.)\s*\d+[a-z]?(?:\s*Abs\.?\s*\d+)?$",
    re.IGNORECASE,
)

# Austrian statute abbreviations (non-exhaustive, most frequent ones
# used in administrative correspondence and court documents).
LEGAL_CODES: frozenset[str] = frozenset({
    # Verfassung & Grundrechte
    "B-VG", "BVG", "EMRK", "StGG", "EU-GRC",
    # Verwaltung
    "AVG", "VStG", "VwGVG", "VwGG", "VfGG", "DSG", "DSGVO", "IFG", "AuskunftspflichtG",
    # Zivilrecht
    "ABGB", "EheG", "KSchG", "MRG", "WEG", "WGG",
    # Strafrecht
    "StGB", "StPO", "JGG", "FinStrG", "SMG",
    # Sozialversicherung
    "ASVG", "GSVG", "BSVG", "APG", "AlVG", "KBGG",
    # Arbeit
    "ArbVG", "AngG", "ArbZG", "UrlG", "MSchG", "VKG", "KJBG", "BEinstG",
    # Unternehmen/Steuern
    "UGB", "GewO", "EStG", "UStG", "KStG", "BAO", "BWG", "WAG", "VersVG",
    # Fremdenrecht
    "AuslBG", "AsylG", "FPG", "NAG", "BFA-VG", "BFA-G",
    # Verkehr
    "KFG", "StVO", "FSG", "EisenbahnG", "LuftfahrtG",
    # Gesundheit
    "ArzneimittelG", "MedProdG", "GuKG", "KAKuG",
    # Bildung
    "SchOG", "SchUG", "UG", "PHG",
    # Umwelt
    "AWG", "WRG", "ForstG", "NaturschutzG",
})

# Austrian federal/regional authorities. Matched case-insensitively
# against ``entity.word`` (after stripping surrounding whitespace).
AT_AUTHORITIES: frozenset[str] = frozenset(w.lower() for w in {
    # Bundesministerien
    "Bundeskanzleramt",
    "Bundesministerium für Inneres",
    "Bundesministerium für Finanzen",
    "Bundesministerium für Justiz",
    "Bundesministerium für Landesverteidigung",
    "Bundesministerium für Arbeit und Wirtschaft",
    "Bundesministerium für Bildung, Wissenschaft und Forschung",
    "Bundesministerium für Soziales, Gesundheit, Pflege und Konsumentenschutz",
    "Bundesministerium für Kunst, Kultur, öffentlichen Dienst und Sport",
    "Bundesministerium für europäische und internationale Angelegenheiten",
    "Bundesministerium für Klimaschutz, Umwelt, Energie, Mobilität, Innovation und Technologie",
    "Bundesministerium für Land- und Forstwirtschaft, Regionen und Wasserwirtschaft",
    "BMI", "BMF", "BMJ", "BMLV", "BMAW", "BMBWF", "BMSGPK", "BMKÖS",
    "BMEIA", "BMK", "BMLUK", "BKA",
    # Höchstgerichte
    "Verfassungsgerichtshof", "Verwaltungsgerichtshof", "Oberster Gerichtshof",
    "VfGH", "VwGH", "OGH",
    # Unabhängige Kontrollorgane
    "Datenschutzbehörde", "Rechnungshof", "Volksanwaltschaft",
    "DSB", "RH",
    # Verwaltungsgerichte
    "Bundesverwaltungsgericht", "Bundesfinanzgericht",
    "BVwG", "BFG",
    # Exekutive Einrichtungen
    "Bundespolizei", "Bundesamt für Fremdenwesen und Asyl",
    "Bundesamt für Verfassungsschutz und Terrorismusbekämpfung",
    "BFA", "BVT", "DSN",
    # Statistik & Sozialversicherung
    "Statistik Austria",
    "Arbeitsmarktservice", "AMS",
    "Österreichische Gesundheitskasse", "ÖGK",
    "Sozialversicherungsanstalt der Selbständigen", "SVS",
    "Pensionsversicherungsanstalt", "PVA",
    "Allgemeine Unfallversicherungsanstalt", "AUVA",
    # Interessenvertretungen
    "Arbeiterkammer", "AK",
    "Wirtschaftskammer Österreich", "Wirtschaftskammer", "WKO", "WKÖ",
    "Österreichischer Gewerkschaftsbund", "ÖGB",
    "Landwirtschaftskammer", "LKÖ",
    # Generische Verwaltungsstellen (Präfixe reichen i.d.R. nicht —
    # hier nur die wörtlich häufig auftretenden Kurzformen)
    "Landesregierung",
    "Bezirkshauptmannschaft",
    "Magistrat",
    "Gemeindeamt",
    "Finanzamt Österreich",
    "Zollamt Österreich",
})

# Entity groups that are candidates for whitelisting. Names (PER),
# addresses, bank numbers etc. never match the whitelist even if they
# happen to collide with a statute abbreviation string.
_WHITELISTABLE_GROUPS: frozenset[str] = frozenset({
    "ORG", "ORG_DETECTED", "LOC",
})


def is_whitelisted(entity: DetectedEntity) -> bool:
    """Return True if the entity should be left unredacted.

    Applies to ORG / ORG_DETECTED / LOC entities whose textual content
    matches either a known statute abbreviation or a well-known
    Austrian authority. Paragraph citations are handled separately
    because they usually arrive as a substring of a larger match.
    """
    if entity.entity_group not in _WHITELISTABLE_GROUPS:
        return False

    word = entity.word.strip()
    if not word:
        return False

    if word in LEGAL_CODES:
        return True

    # Authority match (case-insensitive exact or suffix match for the
    # common variants ``Magistrat der Stadt X`` / ``Bezirkshauptmannschaft X``).
    lw = word.lower()
    if lw in AT_AUTHORITIES:
        return True
    # Allow regional suffixes for the generic stubs (``Magistrat Wien``,
    # ``Bezirkshauptmannschaft Graz-Umgebung``) without whitelisting
    # arbitrary strings.
    for stub in ("magistrat ", "bezirkshauptmannschaft ", "landesregierung ",
                 "gemeindeamt ", "finanzamt "):
        if lw.startswith(stub):
            return True

    return False


def is_legal_paragraph(text: str) -> bool:
    """Return True if the given fragment is a paragraph/article citation.

    Used by a pre-filter (not the entity-level whitelist) because § and
    Art. citations are typically picked up as generic MISC / ORG spans
    or as noisy substrings rather than clean entities.
    """
    if not text:
        return False
    return bool(LEGAL_PARAGRAPHS.match(text.strip()))


def filter_whitelisted(entities: list[DetectedEntity]) -> list[DetectedEntity]:
    """Drop entities matching the authority/statute whitelist.

    Returns a new list; the input is not mutated.
    """
    return [e for e in entities if not is_whitelisted(e)]
