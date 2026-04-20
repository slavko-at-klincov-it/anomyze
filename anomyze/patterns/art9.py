"""Curated Austrian/German lexicons for DSGVO Art. 9 special categories.

Covers the "besondere Kategorien" that the NER models miss reliably:
religion, political affiliation, union membership.

ETHNICITY is intentionally not included — distinguishing protected
ethnic terms from neutral demonyms is too error-prone for a
dictionary approach and risks both over- and under-detection.
SEXUAL_ORIENTATION and BIOMETRIC are also omitted; both require
context beyond a fixed wordlist to anonymise meaningfully.

Lookup is case-insensitive; multi-word entries are matched as
whole-word phrases.
"""

from __future__ import annotations

# Austrian-recognised confessions and common religious-affiliation
# strings. Includes the legally-recognised "anerkannte Kirchen und
# Religionsgesellschaften" plus everyday self-descriptions.
RELIGION_TERMS: frozenset[str] = frozenset({
    "römisch-katholisch",
    "roemisch-katholisch",
    "römisch katholisch",
    "roemisch katholisch",
    "rk",
    "altkatholisch",
    "evangelisch",
    "evangelisch a.b.",
    "evangelisch h.b.",
    "evangelisch ab",
    "evangelisch hb",
    "evangelisch-lutherisch",
    "evangelisch-reformiert",
    "evangelisch-methodistisch",
    "orthodox",
    "griechisch-orthodox",
    "russisch-orthodox",
    "serbisch-orthodox",
    "rumänisch-orthodox",
    "syrisch-orthodox",
    "koptisch-orthodox",
    "armenisch-apostolisch",
    "muslimisch",
    "moslem",
    "islamisch",
    "alevitisch",
    "schiitisch",
    "sunnitisch",
    "jüdisch",
    "juedisch",
    "israelitisch",
    "buddhistisch",
    "hinduistisch",
    "jehovas zeugen",
    "zeugen jehovas",
    "neuapostolisch",
    "mormonisch",
    "bahai",
    "bahá'í",
    "sikhistisch",
    "ohne bekenntnis",
    "konfessionslos",
    "konfessionsfrei",
    "atheistisch",
    "agnostisch",
    "freikirchlich",
})

# Austrian Nationalrat parties + common membership/voter affiliations.
# Bare three-letter abbreviations are deliberately listed as separate
# tokens; the recognizer's word-boundary match prevents collisions
# with substrings.
POLITICAL_TERMS: frozenset[str] = frozenset({
    "övp",
    "oevp",
    "spö",
    "spoe",
    "fpö",
    "fpoe",
    "neos",
    "die grünen",
    "die gruenen",
    "grüne",
    "gruene",
    "kpö",
    "kpoe",
    "bier",
    "mfg",
    "team kärnten",
    "team kaernten",
    "övp-mitglied",
    "spö-mitglied",
    "fpö-mitglied",
    "neos-mitglied",
    "grüne-mitglied",
    "kpö-mitglied",
    "övp-wähler",
    "spö-wähler",
    "fpö-wähler",
    "neos-wähler",
    "övp-funktionär",
    "spö-funktionär",
    "fpö-funktionär",
    "parteimitglied",
    "parteizugehörigkeit",
})

# Austrian trade unions (Gewerkschaften) and umbrella organisations.
UNION_TERMS: frozenset[str] = frozenset({
    "ögb",
    "oegb",
    "gpa",
    "gpa-djp",
    "vida",
    "göd",
    "goed",
    "younion",
    "younion _ die daseinsgewerkschaft",
    "gbh",
    "pro-ge",
    "proge",
    "gewerkschaft bau-holz",
    "gewerkschaft öffentlicher dienst",
    "ögb-mitglied",
    "gewerkschaftsmitglied",
    "betriebsrat",
    "personalvertretung",
})


# Public mapping (entity_group → terms). Used by the ATArt9Recognizer
# to emit the correct entity type per match.
ART9_LEXICONS: dict[str, frozenset[str]] = {
    "RELIGION": RELIGION_TERMS,
    "POLITICAL": POLITICAL_TERMS,
    "UNION": UNION_TERMS,
}
