"""
GovGPT output channel.

Purpose: Filter AI-generated responses and reports before they are
forwarded to federal employees or leave the system.
The AI tools (GovGPT, ELAK-KI) work internally with full data —
Anomyze filters the output.

Behavior: PII is replaced by numbered placeholders ([PERSON_1], [ADRESSE_2]).
A mapping table stores placeholder → original value for re-identification
by authorized users.
"""

from dataclasses import dataclass, field

from anomyze.channels.base import BaseChannel, ChannelResult
from anomyze.config.settings import Settings
from anomyze.pipeline import DetectedEntity
from anomyze.pipeline.entity_resolver import resolve_entities
from anomyze.pipeline.quality_check import check_output

# Map internal entity_group names to user-facing placeholder types
ENTITY_GROUP_TO_PLACEHOLDER = {
    'PER': 'PERSON',
    'ORG': 'ORGANISATION',
    'ORG_DETECTED': 'ORGANISATION',
    'LOC': 'ORT',
    'EMAIL': 'EMAIL',
    'IBAN': 'IBAN',
    'BIC': 'BIC',
    'SVN': 'SVNR',
    'STEUERNUMMER': 'STEUERNUMMER',
    'UID': 'UID',
    'FIRMENBUCH': 'FIRMENBUCH',
    'GEBURTSDATUM': 'GEBURTSDATUM',
    'AKTENZAHL': 'AKTENZAHL',
    'REISEPASS': 'REISEPASS',
    'PERSONALAUSWEIS': 'PERSONALAUSWEIS',
    'KFZ': 'KFZ',
    'TELEFON': 'TELEFON',
    'ADRESSE': 'ADRESSE',
    'QUASI_ID': 'QUASI_ID',
    'DATE': 'DATUM',
    'PHONE': 'TELEFON',
    'HEALTH_DIAGNOSIS': 'GESUNDHEIT',
    'HEALTH_MEDICATION': 'GESUNDHEIT',
    'RELIGION': 'RELIGION',
    'ETHNICITY': 'HERKUNFT',
    'POLITICAL': 'POLITIK',
    'UNION': 'GEWERKSCHAFT',
    'SEXUAL_ORIENTATION': 'SEXUELLE_ORIENTIERUNG',
    'BIOMETRIC': 'BIOMETRIE',
    'FUEHRERSCHEIN': 'FUEHRERSCHEIN',
    'ZMR': 'ZMR',
    'GERICHTSAKTENZAHL': 'AKTENZAHL',
}


@dataclass
class GovGPTResult(ChannelResult):
    """Result from the GovGPT channel.

    Attributes:
        mapping: Placeholder-to-original-value mapping for re-identification.
        original_text: The original text before any processing.
    """

    mapping: dict[str, str] = field(default_factory=dict)
    original_text: str = ""

    @property
    def unique_entity_count(self) -> int:
        """Number of unique entities (by placeholder)."""
        return len(self.mapping)


class GovGPTChannel(BaseChannel):
    """GovGPT output channel: reversible placeholder replacement.

    Replaces PII with numbered placeholders like [PERSON_1], [IBAN_1]
    and maintains a mapping table for re-identification.
    Identical entities get the same placeholder.
    """

    def format_output(
        self,
        text: str,
        entities: list[DetectedEntity],
        settings: Settings,
        original_text: str = "",
    ) -> GovGPTResult:
        """Replace PII with numbered placeholders and build mapping.

        Args:
            text: The preprocessed text.
            entities: All detected entities.
            settings: Configuration settings.
            original_text: Original text before preprocessing.

        Returns:
            GovGPTResult with anonymized text and mapping.
        """
        if not entities:
            quality_report = (
                check_output(text, []) if settings.run_quality_check else None
            )
            return GovGPTResult(
                text=text,
                entities=[],
                channel="govgpt",
                mapping={},
                original_text=original_text,
                quality_report=quality_report,
            )

        # Sort by position
        sorted_entities = sorted(entities, key=lambda e: e.start)

        # Resolve entity references (link variations of the same entity)
        canonical_keys = resolve_entities(sorted_entities)

        # Build placeholder mapping
        type_counters: dict[str, int] = {}
        key_to_placeholder: dict[tuple[str, str], str] = {}
        mapping: dict[str, str] = {}

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

                placeholder = f"[{entity_type}_{type_counters[entity_type]}]"
                key_to_placeholder[lookup] = placeholder
                mapping[placeholder] = original
            else:
                # Keep the longest variant in the mapping (most informative)
                placeholder = key_to_placeholder[lookup]
                if len(original) > len(mapping[placeholder]):
                    mapping[placeholder] = original

            entity.placeholder = key_to_placeholder[lookup]

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

            # Determine if we need spaces
            need_space_before = before and before[-1] not in ' \n\t('
            need_space_after = after and after[0] not in ' \n\t.,;:!?)'

            # Build replacement with proper spacing
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

        return GovGPTResult(
            text=result,
            entities=sorted_entities,
            channel="govgpt",
            mapping=mapping,
            original_text=original_text,
            quality_report=quality_report,
        )
