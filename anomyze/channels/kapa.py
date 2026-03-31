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

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Dict, Optional
import uuid

from anomyze.pipeline import DetectedEntity
from anomyze.channels.base import BaseChannel, ChannelResult
from anomyze.channels.govgpt import ENTITY_GROUP_TO_PLACEHOLDER
from anomyze.audit.logger import AuditLogger, AuditEntry
from anomyze.config.settings import Settings


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

    mapping: Dict[str, str] = field(default_factory=dict)
    original_text: str = ""
    flagged_for_review: List[str] = field(default_factory=list)
    audit_entries: List[AuditEntry] = field(default_factory=list)
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
        entities: List[DetectedEntity],
        settings: Settings,
        original_text: str = "",
        document_id: Optional[str] = None,
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
            return KAPAResult(
                text=text,
                entities=[],
                channel="kapa",
                mapping={},
                original_text=original_text,
                flagged_for_review=[],
                audit_entries=[],
                document_id=document_id,
            )

        sorted_entities = sorted(entities, key=lambda e: e.start)
        review_threshold = settings.kapa_review_threshold

        # Build placeholder mapping (same logic as GovGPT)
        type_counters: Dict[str, int] = {}
        text_to_placeholder: Dict[str, str] = {}
        mapping: Dict[str, str] = {}
        flagged: List[str] = []
        audit_entries: List[AuditEntry] = []

        now = datetime.now(timezone.utc).isoformat()

        for entity in sorted_entities:
            original = entity.word.strip()
            entity_type = ENTITY_GROUP_TO_PLACEHOLDER.get(
                entity.entity_group, entity.entity_group
            )
            score = entity.score

            if not original or score < settings.anomaly_threshold:
                continue

            normalized = original.lower()

            if normalized not in text_to_placeholder:
                if entity_type not in type_counters:
                    type_counters[entity_type] = 0
                type_counters[entity_type] += 1

                base_placeholder = f"{entity_type}_{type_counters[entity_type]}"

                # Flag for human review if confidence is below threshold
                if score < review_threshold:
                    placeholder = f"[PRÜFEN:{base_placeholder}]"
                    flagged.append(placeholder)
                else:
                    placeholder = f"[{base_placeholder}]"

                text_to_placeholder[normalized] = placeholder
                mapping[placeholder] = original

            entity.placeholder = text_to_placeholder[normalized]

            # Build audit entry
            action = "flagged_for_review" if score < review_threshold else "anonymized"
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

        return KAPAResult(
            text=result,
            entities=sorted_entities,
            channel="kapa",
            mapping=mapping,
            original_text=original_text,
            flagged_for_review=flagged,
            audit_entries=audit_entries,
            document_id=document_id,
        )
