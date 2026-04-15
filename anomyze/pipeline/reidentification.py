"""
Quasi-identifier / re-identification detection.

Operates independently from the MLM-based perplexity check in
``context_layer.py``. The idea is to catch passages that identify a
person through attribute combinations even when no direct name is
present: ``der 45-jährige Bäcker aus Graz``, ``die Ehefrau des
Bürgermeisters von Linz``.

Signals
-------

* **Role** — impersonal role words (``Beschwerdeführer``,
  ``Zeuge``, ``Patientin``).
* **Profession** — occupation words used as a distinguishing marker
  (``als Ärztin``, ``arbeitet als Polizist``).
* **Relationship** — familial references (``Sohn von Karl Gruber``).
* **Age** — birth year or explicit age (``Jahrgang 1985``,
  ``45-jährig``).
* **Gender** — ``die weibliche``, ``der männliche``, ``Frau``,
  ``Herr``.
* **Location** — LOC / ADRESSE already detected by NER.
* **Date of birth** — GEBURTSDATUM already detected by regex.

When two or more *different* signal types fall inside a configurable
proximity window without a PER entity in the vicinity, every individual
signal is returned as a ``QUASI_ID`` entity so the downstream channel
can flag / redact it. A heuristic k-estimate is attached to the first
flagged entity's ``context`` description for operational reporting.
"""

from __future__ import annotations

import re

from anomyze.config.settings import Settings
from anomyze.pipeline import DetectedEntity
from anomyze.pipeline.utils import entities_overlap

# --- Patterns ---------------------------------------------------------------

# Impersonal role words referring to a specific person without naming them.
_QUASI_ROLE_PATTERN = re.compile(
    r"\b(?:der|die|dem|den|des)\s+"
    r"(Beschwerdeführer(?:in)?|Antragsteller(?:in)?|Betroffene[rnm]?"
    r"|Kläger(?:in)?|Beklagte[rnm]?|Berufungswerber(?:in)?"
    r"|Beschuldigte[rnm]?|Verdächtige[rnm]?|Zeugin|Zeuge[n]?"
    r"|Geschädigte[rnm]?|Versicherte[rnm]?|Pensionist(?:in)?"
    r"|Bedienstete[rnm]?|Beamt(?:e[rnm]?|in)"
    r"|Patientin|Patient(?:en)?|Mandantin|Mandant(?:en)?"
    r"|Mieterin|Mieter[sn]?|Bewohner(?:in)?"
    r"|Lehrerin|Lehrer[sn]?|Schüler(?:in)?)\b",
    re.UNICODE,
)

# Profession / occupation words used as distinguishing attributes.
_QUASI_PROFESSION_PATTERN = re.compile(
    r"\b(?:als|ist|war|arbeitet(?:e)?\s+als|tätig\s+als)\s+"
    r"(Ärzt(?:in|e)|Krankenschwester|Pfleger(?:in)?"
    r"|Polizist(?:in)?|Soldat(?:in)?|Richter(?:in)?|Staatsanwält(?:in|e)"
    r"|Rechtsanwält(?:in|e)|Notar(?:in)?"
    r"|Bäcker(?:in)?|Fleischer(?:in)?|Tischler(?:in)?|Elektriker(?:in)?"
    r"|Landwirt(?:in)?|Gärtner(?:in)?|Bauer|Bäuerin"
    r"|Bürgermeister(?:in)?|Abgeordnete[rnm]?|Minister(?:in)?"
    r"|Priester(?:in)?|Pfarrer(?:in)?|Rabbiner|Imam|Mufti"
    r"|Lehrer(?:in)?|Professor(?:in)?|Universitätsprofessor(?:in)?"
    r"|Direktor(?:in)?|Geschäftsführer(?:in)?)\b",
    re.UNICODE,
)

# Familial relationships that connect an unnamed subject to a known
# (or separately named) person, producing a re-identification chain.
_QUASI_RELATIONSHIP_PATTERN = re.compile(
    r"\b(?:Sohn|Tochter|Bruder|Schwester|Vater|Mutter"
    r"|Ehemann|Ehefrau|Ehegatt(?:e|in)"
    r"|Lebensgefährt(?:e|in)|Partner(?:in)?"
    r"|Cousin(?:e)?|Neffe|Nichte|Onkel|Tante|Großvater|Großmutter"
    r"|Enkel(?:in)?|Urenkel(?:in)?|Stief(?:sohn|tochter|vater|mutter))\s+"
    r"(?:des|der|von)\s+[A-ZÄÖÜ]\w+\b",
    re.UNICODE,
)

# Age / birth year references (full DD.MM.YYYY dates are handled by
# the regex layer separately).
_QUASI_AGE_PATTERN = re.compile(
    r"\b(?:"
    r"(?:geboren|geb\.?)\s+(?:im\s+(?:Jahr\s+)?)?(\d{4})"
    r"|(\d{1,3})\s*[-–]?\s*[Jj]ähr(?:ig(?:e[rnms]?)?|ige[rnms]?)"
    r"|[Jj]ahrgang\s+(\d{4})"
    r"|[Aa]lter\s+(?:von\s+)?(\d{1,3})"
    r")\b"
)

# Gender markers that narrow identification.
_QUASI_GENDER_PATTERN = re.compile(
    r"\b(?:die\s+(?:weibliche|männliche)|der\s+(?:männliche|weibliche)"
    r"|(?:eine?\s+)?(?:Frau|Mann|Dame|Herr)"
    r")\b",
    re.UNICODE,
)

DEFAULT_WINDOW = 200


def _estimate_k(signal_types: set[str]) -> int:
    """Rough anonymity estimate from number of distinct signal types.

    Deterministic heuristic — no external population data involved.
    Every additional attribute type shrinks the plausible cohort.
    """
    return max(1, 6 - len(signal_types))


def detect_quasi_identifiers(
    text: str,
    existing_entities: list[DetectedEntity],
    settings: Settings,
) -> list[DetectedEntity]:
    """Identify re-identifying attribute combinations.

    Args:
        text: Input text after preprocessing.
        existing_entities: Entities already produced by previous
            pipeline layers (used to detect LOC / ADRESSE /
            GEBURTSDATUM signals).
        settings: Pipeline settings; ``quasi_id_window`` controls the
            co-occurrence window in characters.

    Returns:
        New ``DetectedEntity`` objects with ``entity_group='QUASI_ID'``
        for every signal in the first suspicious window. Empty list
        if nothing triggers.
    """
    window = getattr(settings, "quasi_id_window", DEFAULT_WINDOW)

    signals: list[tuple[int, int, str, str]] = []

    for match in _QUASI_ROLE_PATTERN.finditer(text):
        signals.append((match.start(), match.end(), "role", match.group()))
    for match in _QUASI_PROFESSION_PATTERN.finditer(text):
        signals.append((match.start(), match.end(), "profession", match.group()))
    for match in _QUASI_RELATIONSHIP_PATTERN.finditer(text):
        signals.append((match.start(), match.end(), "relationship", match.group()))
    for match in _QUASI_AGE_PATTERN.finditer(text):
        signals.append((match.start(), match.end(), "age", match.group()))
    for match in _QUASI_GENDER_PATTERN.finditer(text):
        signals.append((match.start(), match.end(), "gender", match.group()))

    for entity in existing_entities:
        if entity.entity_group in ("LOC", "ADRESSE"):
            signals.append((entity.start, entity.end, "location", entity.word))
        elif entity.entity_group == "GEBURTSDATUM":
            signals.append((entity.start, entity.end, "age", entity.word))

    if len(signals) < 2:
        return []

    signals.sort(key=lambda s: s[0])

    new_entities: list[DetectedEntity] = []
    for i, (s_start, _s_end, s_type, _s_word) in enumerate(signals):
        window_types: set[str] = {s_type}
        window_end = s_start + window

        for j in range(i + 1, len(signals)):
            o_start, _o_end, o_type, _o_word = signals[j]
            if o_start > window_end:
                break
            window_types.add(o_type)

        if len(window_types) < 2:
            continue

        has_person = any(
            e.entity_group == "PER"
            and e.start >= s_start - 50
            and e.start <= window_end + 50
            for e in existing_entities
        )
        if has_person:
            continue

        k_est = _estimate_k(window_types)
        for sig_start, sig_end, _sig_type, sig_word in signals[i:]:
            if sig_start > window_end:
                break
            if any(
                entities_overlap(sig_start, sig_end, e.start, e.end)
                for e in existing_entities
            ):
                continue
            if any(
                entities_overlap(sig_start, sig_end, e.start, e.end)
                for e in new_entities
            ):
                continue
            new_entities.append(DetectedEntity(
                word=sig_word,
                entity_group="QUASI_ID",
                score=0.70,
                start=sig_start,
                end=sig_end,
                source="quasi_id",
                context=(
                    f"Quasi-Identifikator: {', '.join(sorted(window_types))} "
                    f"in Kombination (k~{k_est})"
                ),
            ))
        break

    return new_entities
