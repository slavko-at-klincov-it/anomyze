"""
IFG output channel (Informationsfreiheitsgesetz / data.gv.at).

Purpose: Filter AI-generated outputs before publication on the Austrian
information register (data.gv.at). The AI tools work internally with
full data — Anomyze irreversibly redacts PII from the output before
it leaves the system.

Behavior:
- PII is irreversibly removed — no mapping, no way back.
- Placeholders use category-only format without sequential numbering
  to prevent correlation: [GESCHWÄRZT:PERSON], [GESCHWÄRZT:ADRESSE].
- A redaction protocol documents what categories were removed and how
  many instances, but never the original values.
- original_text is NOT populated (DSGVO — no reversibility through
  the channel result).
"""

from dataclasses import dataclass, field

from anomyze.channels.base import BaseChannel, ChannelResult
from anomyze.channels.govgpt import ENTITY_GROUP_TO_PLACEHOLDER
from anomyze.config.settings import Settings
from anomyze.pipeline import DetectedEntity
from anomyze.pipeline.quality_check import check_output


@dataclass
class RedactionEntry:
    """A single entry in the redaction protocol.

    Attributes:
        category: The PII category (e.g., PERSON, IBAN).
        count: Number of instances redacted.
        min_confidence: Lowest confidence score in this category.
        max_confidence: Highest confidence score in this category.
    """

    category: str
    count: int
    min_confidence: float
    max_confidence: float

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "category": self.category,
            "count": self.count,
            "min_confidence": round(self.min_confidence, 3),
            "max_confidence": round(self.max_confidence, 3),
        }


@dataclass
class IFGResult(ChannelResult):
    """Result from the IFG channel.

    Note: No mapping, no original_text — irreversible by design.

    Attributes:
        redaction_protocol: Summary of redacted categories.
    """

    redaction_protocol: list[RedactionEntry] = field(default_factory=list)


class IFGChannel(BaseChannel):
    """IFG output channel: irreversible redaction for public disclosure.

    Replaces PII with non-numbered category placeholders and produces
    a redaction protocol. No mapping is stored or returned.
    """

    def format_output(
        self,
        text: str,
        entities: list[DetectedEntity],
        settings: Settings,
        original_text: str = "",
    ) -> IFGResult:
        """Irreversibly redact PII and produce a redaction protocol.

        Args:
            text: The preprocessed text.
            entities: All detected entities.
            settings: Configuration settings.
            original_text: Ignored — not stored for DSGVO compliance.

        Returns:
            IFGResult with redacted text and protocol.
        """
        if not entities:
            return IFGResult(
                text=text,
                entities=[],
                channel="ifg",
                redaction_protocol=[],
            )

        # Filter entities by threshold
        valid_entities = [e for e in entities if e.score >= settings.anomaly_threshold]

        # Build redaction protocol (category stats)
        category_stats: dict[str, dict] = {}
        for entity in valid_entities:
            category = ENTITY_GROUP_TO_PLACEHOLDER.get(
                entity.entity_group, entity.entity_group
            )
            if category not in category_stats:
                category_stats[category] = {
                    "count": 0,
                    "min_confidence": entity.score,
                    "max_confidence": entity.score,
                }
            stats = category_stats[category]
            stats["count"] += 1
            stats["min_confidence"] = min(stats["min_confidence"], entity.score)
            stats["max_confidence"] = max(stats["max_confidence"], entity.score)

        protocol = [
            RedactionEntry(
                category=cat,
                count=stats["count"],
                min_confidence=stats["min_confidence"],
                max_confidence=stats["max_confidence"],
            )
            for cat, stats in sorted(category_stats.items())
        ]

        # Apply redactions (reverse order to preserve positions)
        # Use category-only placeholders without numbering to prevent correlation
        result = text
        for entity in sorted(valid_entities, key=lambda e: e.start, reverse=True):
            category = ENTITY_GROUP_TO_PLACEHOLDER.get(
                entity.entity_group, entity.entity_group
            )
            placeholder = f"[GESCHWÄRZT:{category}]"
            entity.placeholder = placeholder

            start = entity.start
            end = entity.end

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

        # Quality check runs on the pre-sanitized entities so it can
        # verify original words are no longer present in the output.
        quality_report = (
            check_output(result, valid_entities)
            if settings.run_quality_check else None
        )

        # Clear entity words from result entities for DSGVO compliance
        # The protocol has category counts but never the original values
        sanitized_entities = []
        for entity in valid_entities:
            sanitized_entities.append(DetectedEntity(
                word="[REDACTED]",
                entity_group=entity.entity_group,
                score=entity.score,
                start=entity.start,
                end=entity.end,
                source=entity.source,
                placeholder=entity.placeholder,
            ))

        return IFGResult(
            text=result,
            entities=sanitized_entities,
            channel="ifg",
            redaction_protocol=protocol,
            quality_report=quality_report,
        )
