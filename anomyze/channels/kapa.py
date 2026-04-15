"""
KAPA output channel (Kommission für parlamentarische Anfragen).

Purpose: Filter AI-generated research results before they leave
the system as parliamentary responses. The AI tools work internally
with full data — Anomyze filters the output and provides a full
audit trail for parliamentary accountability.

Behavior:
- Like GovGPT: numbered placeholders + reversible mapping.
- Plus: full audit trail for parliamentary accountability.
- Plus: human-in-the-loop — entities below kapa_review_threshold
  are flagged with [PRÜFEN:TYPE_N] for manual review.
- Every anonymization action is logged with timestamp, confidence,
  source layer, and sanitized context snippet.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone

from anomyze.audit.logger import AuditEntry
from anomyze.channels.base import BaseChannel, ChannelResult
from anomyze.channels.govgpt import ENTITY_GROUP_TO_PLACEHOLDER
from anomyze.config.settings import Settings
from anomyze.pipeline import ART9_SENSITIVE_CATEGORIES, DetectedEntity
from anomyze.pipeline.entity_resolver import resolve_entities
from anomyze.pipeline.quality_check import check_output


@dataclass
class KAPAResult(ChannelResult):
    """Result from the KAPA channel.

    Attributes:
        mapping: Placeholder-to-original-value mapping.
        original_text: The original text before processing.
        flagged_for_review: Placeholders that need human review.
        audit_entries: Full audit trail for this document.
        document_id: Unique document identifier for audit tracking.
    """

    mapping: dict[str, str] = field(default_factory=dict)
    original_text: str = ""
    flagged_for_review: list[str] = field(default_factory=list)
    audit_entries: list[AuditEntry] = field(default_factory=list)
    document_id: str = ""

    @property
    def unique_entity_count(self) -> int:
        """Number of unique entities (by placeholder)."""
        return len(self.mapping)


def _extract_context_snippet(
    text: str, start: int, end: int, placeholder: str, window: int = 30
) -> str:
    """Extract a context snippet around an entity, with PII masked.

    Shows ~30 chars before and after the entity position,
    with the entity itself replaced by its placeholder.

    Args:
        text: The full text.
        start: Entity start position.
        end: Entity end position.
        placeholder: The placeholder to show instead of the entity.
        window: Number of characters before/after to include.

    Returns:
        Sanitized context snippet.
    """
    ctx_start = max(0, start - window)
    ctx_end = min(len(text), end + window)
    before = text[ctx_start:start]
    after = text[end:ctx_end]
    return f"...{before}{placeholder}{after}..."


class KAPAChannel(BaseChannel):
    """KAPA output channel: reversible placeholders with audit trail.

    Combines GovGPT-style placeholder replacement with:
    - Full audit logging for parliamentary accountability
    - Human-in-the-loop flagging for uncertain detections
    """

    def format_output(
        self,
        text: str,
        entities: list[DetectedEntity],
        settings: Settings,
        original_text: str = "",
        document_id: str | None = None,
    ) -> KAPAResult:
        """Replace PII, build audit trail, and flag uncertain entities.

        Args:
            text: The preprocessed text.
            entities: All detected entities.
            settings: Configuration settings.
            original_text: Original text before preprocessing.
            document_id: Unique document ID (auto-generated if None).

        Returns:
            KAPAResult with anonymized text, mapping, and audit trail.
        """
        if document_id is None:
            document_id = str(uuid.uuid4())

        if not entities:
            quality_report = (
                check_output(text, []) if settings.run_quality_check else None
            )
            return KAPAResult(
                text=text,
                entities=[],
                channel="kapa",
                mapping={},
                original_text=original_text,
                flagged_for_review=[],
                audit_entries=[],
                document_id=document_id,
                quality_report=quality_report,
            )

        sorted_entities = sorted(entities, key=lambda e: e.start)
        review_threshold = settings.kapa_review_threshold

        # Resolve entity references (link variations of the same entity)
        canonical_keys = resolve_entities(sorted_entities)

        # Build placeholder mapping (same logic as GovGPT)
        type_counters: dict[str, int] = {}
        key_to_placeholder: dict[tuple[str, str], str] = {}
        mapping: dict[str, str] = {}
        flagged: list[str] = []
        audit_entries: list[AuditEntry] = []

        now = datetime.now(timezone.utc).isoformat()

        for entity, ckey in zip(sorted_entities, canonical_keys, strict=True):
            original = entity.word.strip()
            entity_type = ENTITY_GROUP_TO_PLACEHOLDER.get(
                entity.entity_group, entity.entity_group
            )
            score = entity.score

            if not original or score < settings.anomaly_threshold:
                continue

            lookup = (entity_type, ckey)

            if lookup not in key_to_placeholder:
                if entity_type not in type_counters:
                    type_counters[entity_type] = 0
                type_counters[entity_type] += 1

                base_placeholder = f"{entity_type}_{type_counters[entity_type]}"

                # Flag for human review if confidence is below threshold
                # OR the entity falls under DSGVO Art. 9 (besondere
                # Kategorien) AND ``always_review_art9`` is on. The
                # opt-out lets legacy KAPA workflows that auto-anonymise
                # high-confidence health/religion/etc. entities keep
                # their behaviour by setting ``always_review_art9=False``.
                is_art9 = (
                    entity.entity_group in ART9_SENSITIVE_CATEGORIES
                    and settings.always_review_art9
                )
                if score < review_threshold or is_art9:
                    placeholder = f"[PRÜFEN:{base_placeholder}]"
                    flagged.append(placeholder)
                else:
                    placeholder = f"[{base_placeholder}]"

                key_to_placeholder[lookup] = placeholder
                mapping[placeholder] = original
            else:
                placeholder = key_to_placeholder[lookup]
                # Keep the longest variant in the mapping (most informative)
                if len(original) > len(mapping[placeholder]):
                    mapping[placeholder] = original

            entity.placeholder = key_to_placeholder[lookup]

            # Build audit entry. Mirrors the placeholder gate above so
            # action == flagged_for_review iff the placeholder uses
            # the [PRÜFEN:...] prefix — invariant relied upon by tests
            # and consumers alike.
            is_art9 = (
                entity.entity_group in ART9_SENSITIVE_CATEGORIES
                and settings.always_review_art9
            )
            action = (
                "flagged_for_review"
                if score < review_threshold or is_art9
                else "anonymized"
            )
            context_snippet = _extract_context_snippet(
                text, entity.start, entity.end, entity.placeholder
            )

            audit_entries.append(AuditEntry(
                timestamp=now,
                document_id=document_id,
                entity_word=original,
                entity_group=entity_type,
                confidence=score,
                source_layer=entity.source,
                action=action,
                placeholder=entity.placeholder,
                context_snippet=context_snippet,
            ))

        # Apply replacements (reverse order to preserve positions)
        result = text
        for entity in sorted(sorted_entities, key=lambda e: e.start, reverse=True):
            if not entity.placeholder or entity.score < settings.anomaly_threshold:
                continue

            start = entity.start
            end = entity.end
            placeholder = entity.placeholder

            before = result[:start]
            after = result[end:]

            need_space_before = before and before[-1] not in ' \n\t('
            need_space_after = after and after[0] not in ' \n\t.,;:!?)'

            replacement = ''
            if need_space_before:
                replacement += ' '
            replacement += placeholder
            if need_space_after:
                replacement += ' '

            result = before + replacement + after

        quality_report = (
            check_output(result, sorted_entities)
            if settings.run_quality_check else None
        )

        return KAPAResult(
            text=result,
            entities=sorted_entities,
            channel="kapa",
            mapping=mapping,
            original_text=original_text,
            flagged_for_review=flagged,
            audit_entries=audit_entries,
            document_id=document_id,
            quality_report=quality_report,
        )
