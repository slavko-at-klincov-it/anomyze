"""
Stage 3: Context-based anomaly detection.

Two detection mechanisms:

1. **Perplexity-based company detection**: Uses a Masked Language Model (MLM)
   to detect potential company/organization names that are not covered
   by regex or NER models.
   Core idea: In "bei uns in der Küche" → "Küche" is expected.
              In "bei uns in der Siemens" → "Siemens" is unexpected → likely a company.

2. **Quasi-identifier detection**: Identifies passages where combinations
   of individually harmless attributes (role + location + date/age) could
   re-identify a person even without a name being present.
   Example: "der Beschwerdeführer aus Graz, geboren 1985" — no name,
   but potentially identifiable through attribute combination.
"""

import logging
import re
from typing import Any

from anomyze.config.settings import Settings, get_settings
from anomyze.patterns.at_patterns import COMPANY_CONTEXT_PATTERNS, NORMAL_CONTEXT_WORDS
from anomyze.pipeline import DetectedEntity
from anomyze.pipeline.utils import entities_overlap

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Quasi-identifier patterns
# ---------------------------------------------------------------------------

# Role/title words that refer to a specific person without naming them
_QUASI_ROLE_PATTERN = re.compile(
    r'\b(?:der|die|dem|den|des)\s+'
    r'(Beschwerdeführer(?:in)?|Antragsteller(?:in)?|Betroffene[rnm]?'
    r'|Kläger(?:in)?|Beklagte[rnm]?|Berufungswerber(?:in)?'
    r'|Beschuldigte[rnm]?|Verdächtige[rnm]?|Zeugin|Zeuge[n]?'
    r'|Geschädigte[rnm]?|Versicherte[rnm]?|Pensionist(?:in)?'
    r'|Bedienstete[rnm]?|Beamt(?:e[rnm]?|in)'
    r'|Patientin|Patient(?:en)?|Mandantin|Mandant(?:en)?'
    r'|Mieterin|Mieter[sn]?|Bewohner(?:in)?'
    r'|Lehrerin|Lehrer[sn]?|Schüler(?:in)?)\b',
    re.UNICODE
)

# Age/birth year references (not full dates — those are caught by regex layer)
_QUASI_AGE_PATTERN = re.compile(
    r'\b(?:'
    r'(?:geboren|geb\.?)\s+(?:im\s+(?:Jahr\s+)?)?(\d{4})'   # geboren 1985, geb. im Jahr 1985
    r'|(\d{1,3})\s*[-–]?\s*[Jj]ähr(?:ig(?:e[rnms]?)?|ige[rnms]?)'  # 45-jährig, 45-jährige
    r'|[Jj]ahrgang\s+(\d{4})'                                  # Jahrgang 1985
    r'|[Aa]lter\s+(?:von\s+)?(\d{1,3})'                       # Alter von 45
    r')\b'
)

# Gender markers that narrow identification
_QUASI_GENDER_PATTERN = re.compile(
    r'\b(?:die\s+(?:weibliche|männliche)|der\s+(?:männliche|weibliche)'
    r'|(?:eine?\s+)?(?:Frau|Mann|Dame|Herr)'
    r')\b',
    re.UNICODE
)

# Proximity window (characters) within which quasi-identifiers combine
_QUASI_WINDOW = 200


class ContextLayer:
    """Stage 3 of the anonymization pipeline: perplexity-based anomaly detection.

    Scans text for company context patterns, then uses an MLM to determine
    whether the candidate word is expected (normal word) or anomalous
    (likely a company/organization name).
    """

    def process(
        self,
        text: str,
        existing_entities: list[DetectedEntity],
        mlm_pipeline: Any,
        settings: Settings | None = None,
    ) -> list[DetectedEntity]:
        """Detect anomalies and quasi-identifiers.

        Combines two detection mechanisms:
        1. Perplexity-based company name detection via MLM
        2. Quasi-identifier combination detection

        Args:
            text: The input text to analyze.
            existing_entities: Entities already detected by previous layers.
            mlm_pipeline: HuggingFace fill-mask pipeline for perplexity scoring.
            settings: Configuration settings.

        Returns:
            List of new entities detected via anomaly/quasi-identifier analysis.
        """
        if settings is None:
            settings = get_settings()

        # 1. Perplexity-based company detection
        anomalies = self._detect_company_anomalies(
            text, existing_entities, mlm_pipeline, settings
        )

        # 2. Quasi-identifier combination detection
        all_known = list(existing_entities) + anomalies
        quasi_entities = self._detect_quasi_identifiers(text, all_known, settings)
        anomalies.extend(quasi_entities)

        return anomalies

    def _detect_company_anomalies(
        self,
        text: str,
        existing_entities: list[DetectedEntity],
        mlm_pipeline: Any,
        settings: Settings,
    ) -> list[DetectedEntity]:
        """Detect potential company names using perplexity-based anomaly detection."""
        anomalies: list[DetectedEntity] = []

        for pattern, description, include_suffix in COMPANY_CONTEXT_PATTERNS:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                word = match.group(1)
                word_start = match.start(1)
                word_end = match.end(1)

                # If pattern includes suffix (like "Bank"), extend the word
                if include_suffix and match.lastindex is not None and match.lastindex >= 2:
                    suffix = match.group(2)
                    word = word + " " + suffix
                    word_end = match.end(2)

                word_lower = word.lower()

                # Skip normal context words
                if word_lower.split()[0] in NORMAL_CONTEXT_WORDS:
                    continue

                # Skip if already detected with high confidence
                already_detected_well = False
                for e in existing_entities:
                    if entities_overlap(word_start, word_end, e.start, e.end):
                        if e.score >= 0.8:
                            already_detected_well = True
                            break
                if already_detected_well:
                    continue

                if len(word) < 3:
                    continue

                # Check perplexity
                context_start = max(0, match.start() - 30)
                context_end = min(len(text), match.end() + 30)
                context = text[context_start:context_end]

                relative_start = match.start(1) - context_start
                relative_end = match.end(1) - context_start
                masked_context = context[:relative_start] + "[MASK]" + context[relative_end:]

                try:
                    predictions = mlm_pipeline(masked_context)
                    predicted_tokens = [p['token_str'].strip().lower() for p in predictions]

                    first_word = word_lower.split()[0] if ' ' in word_lower else word_lower
                    is_expected = first_word in predicted_tokens

                    if is_expected:
                        position = predicted_tokens.index(first_word)
                        anomaly_score = position / len(predictions)
                    else:
                        anomaly_score = 1.0

                    if anomaly_score > settings.perplexity_threshold and word[0].isupper():
                        entity = DetectedEntity(
                            word=word,
                            entity_group='ORG_DETECTED',
                            score=min(0.95, 0.6 + anomaly_score * 0.35),
                            start=word_start,
                            end=word_end,
                            source='perplexity',
                            context=description,
                            anomaly_score=anomaly_score,
                        )

                        # Final overlap check against all known entities + our own findings
                        all_known = list(existing_entities) + anomalies
                        if not any(
                            entities_overlap(entity.start, entity.end, ex.start, ex.end)
                            for ex in all_known
                        ):
                            anomalies.append(entity)

                except Exception as exc:
                    logger.debug(
                        "Anomaly detection failed for word '%s': %s", word, exc
                    )
                    continue

        return anomalies

    def _detect_quasi_identifiers(
        self,
        text: str,
        existing_entities: list[DetectedEntity],
        settings: Settings,
    ) -> list[DetectedEntity]:
        """Detect passages where quasi-identifier combinations could re-identify a person.

        Scans for co-occurring role references (Beschwerdeführer, Antragsteller),
        location mentions, and age/birth year references. When 2+ quasi-identifier
        types appear within a proximity window without an associated PER entity,
        the undetected attributes are flagged.

        Example: "der Beschwerdeführer aus Graz, geboren 1985"
        → "Graz" already detected as LOC, but the birth year "1985" and the
          role "Beschwerdeführer" in combination make this passage identifying.
        """
        new_entities: list[DetectedEntity] = []

        # Collect quasi-identifier signals with their positions
        signals: list[tuple[int, int, str, str]] = []  # (start, end, type, word)

        for match in _QUASI_ROLE_PATTERN.finditer(text):
            signals.append((match.start(), match.end(), 'role', match.group()))

        for match in _QUASI_AGE_PATTERN.finditer(text):
            signals.append((match.start(), match.end(), 'age', match.group()))

        for match in _QUASI_GENDER_PATTERN.finditer(text):
            signals.append((match.start(), match.end(), 'gender', match.group()))

        # Also count already-detected LOC and GEBURTSDATUM entities as signals
        for entity in existing_entities:
            if entity.entity_group in ('LOC', 'ADRESSE'):
                signals.append((entity.start, entity.end, 'location', entity.word))
            elif entity.entity_group == 'GEBURTSDATUM':
                signals.append((entity.start, entity.end, 'age', entity.word))

        if len(signals) < 2:
            return new_entities

        # Sort signals by position
        signals.sort(key=lambda s: s[0])

        # Sliding window: check for combinations within _QUASI_WINDOW chars
        for i, (s_start, _s_end, s_type, _s_word) in enumerate(signals):
            # Collect all signal types within the window
            window_types: set[str] = {s_type}
            window_end = s_start + _QUASI_WINDOW

            for j in range(i + 1, len(signals)):
                o_start, o_end, o_type, o_word = signals[j]
                if o_start > window_end:
                    break
                window_types.add(o_type)

            # A combination of 2+ different quasi-identifier types is suspicious
            if len(window_types) < 2:
                continue

            # Check if there's already a PER entity in this window
            has_person = any(
                e.entity_group == 'PER'
                and e.start >= s_start - 50
                and e.start <= window_end + 50
                for e in existing_entities
            )

            # If a person name IS detected, the regular anonymization handles it.
            # Quasi-identifier flagging is for cases WITHOUT a detected name.
            if has_person:
                continue

            # Only flag the signals that aren't already detected entities
            for sig_start, sig_end, _sig_type, sig_word in signals[i:]:
                if sig_start > window_end:
                    break

                # Skip if this span is already covered by an existing entity
                if any(
                    entities_overlap(sig_start, sig_end, e.start, e.end)
                    for e in existing_entities
                ):
                    continue

                # Skip if we already flagged this span
                if any(
                    entities_overlap(sig_start, sig_end, e.start, e.end)
                    for e in new_entities
                ):
                    continue

                # Flag this quasi-identifier for review
                new_entities.append(DetectedEntity(
                    word=sig_word,
                    entity_group='QUASI_ID',
                    score=0.70,
                    start=sig_start,
                    end=sig_end,
                    source='quasi_id',
                    context=f"Quasi-Identifikator: {', '.join(sorted(window_types))} in Kombination",
                ))

            # Only flag the first window occurrence to avoid duplicates
            break

        return new_entities
