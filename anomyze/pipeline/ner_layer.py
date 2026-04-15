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
from anomyze.patterns import is_blacklisted
from anomyze.pipeline import DetectedEntity
from anomyze.pipeline.utils import clean_entity_word


def _resolve_offsets(
    text: str,
    raw_word: str,
    start: int | None,
    end: int | None,
) -> tuple[int, int] | None:
    """Return (start, end) offsets, falling back to ``text.find`` when the
    tokenizer did not emit character positions.

    Slow tokenizers (``use_fast=False``) — which we are forced to use
    for SentencePiece models in transformers 4.x — do not populate the
    ``start``/``end`` fields of pipeline outputs. Look up the raw word
    in ``text`` as a best-effort fallback; return ``None`` if the word
    cannot be located (entity is dropped).
    """
    if start is not None and end is not None:
        return int(start), int(end)
    # SentencePiece emits "▁word" for whitespace-prefixed tokens; strip
    # it before searching.
    needle = raw_word.lstrip("▁ ").strip()
    if not needle:
        return None
    idx = text.find(needle)
    if idx == -1:
        return None
    return idx, idx + len(needle)

# Label normalization: different NER models use different label schemes.
# xlm-roberta-large-ner-hrl uses B-PER/I-PER, dslim uses PER, etc.
_LABEL_NORMALIZE: dict[str, str] = {
    "B-PER": "PER",
    "I-PER": "PER",
    "B-ORG": "ORG",
    "I-ORG": "ORG",
    "B-LOC": "LOC",
    "I-LOC": "LOC",
    "B-MISC": "MISC",
    "I-MISC": "MISC",
    "USERNAME": "EMAIL",
}

_ACCEPTED_ORG_LABELS = frozenset({"ORG", "LOC", "PER"})


def _normalize_label(label: str) -> str:
    """Normalize entity label across different model schemes."""
    return _LABEL_NORMALIZE.get(label, label)


class NERLayer:
    """Stage 2 of the anonymization pipeline: NER model detection.

    Runs two HuggingFace pipelines (PII + ORG/NER) and filters
    results by confidence threshold, blacklist, and overlap
    with previously detected entities.
    """

    def process(
        self,
        text: str,
        pii_pipeline: Any,
        org_pipeline: Any,
        settings: Settings | None = None,
    ) -> list[DetectedEntity]:
        """Run NER models and return detected entities.

        Returns all entities that pass threshold and blacklist checks.
        Overlap deduplication is handled by the ensemble layer.

        Args:
            text: The input text to analyze.
            pii_pipeline: HuggingFace PII detection pipeline.
            org_pipeline: HuggingFace NER/ORG detection pipeline.
            settings: Configuration settings.

        Returns:
            List of entities detected by the NER models.
        """
        if settings is None:
            settings = get_settings()

        new_entities: list[DetectedEntity] = []

        # Layer 1: PII detection (names, emails, phones, dates)
        pii_entities = pii_pipeline(text)
        for e in pii_entities:
            offsets = _resolve_offsets(text, e['word'], e.get('start'), e.get('end'))
            if offsets is None:
                continue
            word, start, end = clean_entity_word(e['word'], text, offsets[0], offsets[1])

            if e['score'] < settings.pii_threshold:
                continue
            if is_blacklisted(word):
                continue

            entity = DetectedEntity(
                word=word,
                entity_group=_normalize_label(e['entity_group']),
                score=e['score'],
                start=start,
                end=end,
                source='pii',
            )
            new_entities.append(entity)

        # Layer 2: ORG/NER detection (organizations, locations, persons)
        org_entities = org_pipeline(text)
        org_entities = [
            e for e in org_entities
            if _normalize_label(e['entity_group']) in _ACCEPTED_ORG_LABELS
        ]

        for e in org_entities:
            offsets = _resolve_offsets(text, e['word'], e.get('start'), e.get('end'))
            if offsets is None:
                continue
            word, start, end = clean_entity_word(e['word'], text, offsets[0], offsets[1])

            if is_blacklisted(word):
                continue
            if e['score'] < settings.org_threshold:
                continue

            entity = DetectedEntity(
                word=word,
                entity_group=_normalize_label(e['entity_group']),
                score=e['score'],
                start=start,
                end=end,
                source='org',
            )
            new_entities.append(entity)

        return new_entities
