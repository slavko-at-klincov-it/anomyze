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
from anomyze.patterns import COMPANY_CONTEXT_PATTERNS, NORMAL_CONTEXT_WORDS
from anomyze.pipeline import DetectedEntity
from anomyze.pipeline.reidentification import detect_quasi_identifiers
from anomyze.pipeline.utils import entities_overlap

logger = logging.getLogger(__name__)


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
        """Delegating shim — the full implementation lives in
        ``anomyze.pipeline.reidentification``. Kept here for
        backwards compatibility with tests / external callers that
        patched the original method.
        """
        return detect_quasi_identifiers(text, existing_entities, settings)
