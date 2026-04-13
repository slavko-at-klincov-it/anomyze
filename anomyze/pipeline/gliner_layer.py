"""
Stage 2b: GLiNER zero-shot NER detection.

Uses GLiNER for flexible, zero-shot named entity recognition.
Entity types are configurable at runtime, allowing detection of
arbitrary PII categories without retraining.
"""

import logging
from typing import Any

from anomyze.config.settings import Settings, get_settings
from anomyze.patterns import is_blacklisted
from anomyze.pipeline import DetectedEntity
from anomyze.pipeline.utils import entities_overlap

logger = logging.getLogger(__name__)

# Mapping from GLiNER entity labels to internal entity groups
_GLINER_LABEL_MAP: dict[str, str] = {
    "person name": "PER",
    "email address": "EMAIL",
    "phone number": "TELEFON",
    "physical address": "ADRESSE",
    "date of birth": "GEBURTSDATUM",
    "organization": "ORG",
    "company name": "ORG",
    "social security number": "SVN",
    "bank account number": "IBAN",
    "license plate number": "KFZ",
}


class GLiNERLayer:
    """Zero-shot NER detection using GLiNER.

    GLiNER can detect arbitrary entity types specified at inference time,
    making it a flexible complement to fixed NER models.
    """

    def process(
        self,
        text: str,
        existing_entities: list[DetectedEntity],
        gliner_model: Any,
        settings: Settings | None = None,
    ) -> list[DetectedEntity]:
        """Run GLiNER zero-shot NER and return filtered entities.

        Args:
            text: The input text to analyze.
            existing_entities: Entities already detected by previous layers.
            gliner_model: Loaded GLiNER model instance.
            settings: Configuration settings.

        Returns:
            List of new entities detected by GLiNER.
        """
        if settings is None:
            settings = get_settings()

        if gliner_model is None:
            return []

        new_entities: list[DetectedEntity] = []
        all_known = list(existing_entities)

        try:
            entities = gliner_model.predict_entities(
                text,
                list(settings.gliner_entity_types),
                threshold=settings.gliner_threshold,
            )
        except Exception:
            logger.warning("GLiNER prediction failed", exc_info=True)
            return []

        for e in entities:
            word = e.get("text", "")
            label = e.get("label", "")
            score = e.get("score", 0.0)
            start = e.get("start", 0)
            end = e.get("end", 0)

            if not word or score < settings.gliner_threshold:
                continue
            if is_blacklisted(word):
                continue

            entity_group = _GLINER_LABEL_MAP.get(label, label.upper())

            if any(entities_overlap(start, end, ex.start, ex.end) for ex in all_known):
                continue

            entity = DetectedEntity(
                word=word,
                entity_group=entity_group,
                score=score,
                start=start,
                end=end,
                source="gliner",
            )
            new_entities.append(entity)
            all_known.append(entity)

        return new_entities
