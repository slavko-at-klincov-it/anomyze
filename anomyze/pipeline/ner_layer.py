"""
Stage 2: NER-based PII detection.

Uses HuggingFace transformer models for token classification:
- PII model: detects names, emails, phone numbers, dates
- NER/ORG model: detects organizations, locations, persons

Entities are cleaned, filtered by threshold and blacklist,
and deduplicated against previously detected entities.
"""

from typing import Any

from anomyze.config.settings import Settings, get_settings
from anomyze.patterns.at_patterns import is_blacklisted
from anomyze.pipeline import DetectedEntity
from anomyze.pipeline.utils import clean_entity_word, entities_overlap


class NERLayer:
    """Stage 2 of the anonymization pipeline: NER model detection.

    Runs two HuggingFace pipelines (PII + ORG/NER) and filters
    results by confidence threshold, blacklist, and overlap
    with previously detected entities.
    """

    def process(
        self,
        text: str,
        existing_entities: list[DetectedEntity],
        pii_pipeline: Any,
        org_pipeline: Any,
        settings: Settings | None = None,
    ) -> list[DetectedEntity]:
        """Run NER models and return filtered, deduplicated entities.

        Args:
            text: The input text to analyze.
            existing_entities: Entities already detected by previous layers.
            pii_pipeline: HuggingFace PII detection pipeline.
            org_pipeline: HuggingFace NER/ORG detection pipeline.
            settings: Configuration settings.

        Returns:
            List of new entities detected by the NER models.
        """
        if settings is None:
            settings = get_settings()

        new_entities: list[DetectedEntity] = []
        all_known = list(existing_entities)

        # Layer 1: PII detection (names, emails, phones, dates)
        pii_entities = pii_pipeline(text)
        for e in pii_entities:
            word, start, end = clean_entity_word(e['word'], text, e['start'], e['end'])

            if e['score'] < settings.pii_threshold:
                continue
            if is_blacklisted(word):
                continue
            if any(entities_overlap(start, end, ex.start, ex.end) for ex in all_known):
                continue

            entity = DetectedEntity(
                word=word,
                entity_group=e['entity_group'],
                score=e['score'],
                start=start,
                end=end,
                source='pii',
            )
            new_entities.append(entity)
            all_known.append(entity)

        # Layer 2: ORG/NER detection (organizations, locations, persons)
        org_entities = org_pipeline(text)
        org_entities = [e for e in org_entities if e['entity_group'] in ('ORG', 'LOC', 'PER')]

        for e in org_entities:
            word, start, end = clean_entity_word(e['word'], text, e['start'], e['end'])

            if is_blacklisted(word):
                continue
            if any(entities_overlap(start, end, ex.start, ex.end) for ex in all_known):
                continue
            if e['score'] < settings.org_threshold:
                continue

            entity = DetectedEntity(
                word=word,
                entity_group=e['entity_group'],
                score=e['score'],
                start=start,
                end=end,
                source='org',
            )
            new_entities.append(entity)
            all_known.append(entity)

        return new_entities
