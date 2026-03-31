"""
Stage 1: Regex-based PII detection.

Runs all Austrian-specific regex patterns against the input text
and returns detected entities with high-confidence scores.
This is the first and fastest layer in the pipeline.
"""


from anomyze.patterns.at_patterns import (
    find_address_regex,
    find_aktenzahl_regex,
    find_birth_date_regex,
    find_emails_regex,
    find_ibans_regex,
    find_id_card_regex,
    find_labeled_names_regex,
    find_license_plate_regex,
    find_passport_regex,
    find_phone_regex,
    find_svnr_regex,
    find_tax_number_regex,
    find_titled_names_regex,
)
from anomyze.pipeline import DetectedEntity
from anomyze.pipeline.utils import entities_overlap


class RegexLayer:
    """Stage 1 of the anonymization pipeline: regex-based detection.

    Runs all pattern-matching functions and deduplicates overlapping
    results. Regex detection has the highest precision but is limited
    to known formats.
    """

    def process(self, text: str) -> list[DetectedEntity]:
        """Run all regex-based detectors and return deduplicated entities.

        The order of detectors matters for overlap resolution:
        earlier detectors take priority.

        Args:
            text: The input text to scan.

        Returns:
            List of detected entities, deduplicated by position.
        """
        all_entities: list[DetectedEntity] = []

        # Run all finder functions in priority order
        finders = [
            find_emails_regex,
            find_aktenzahl_regex,
            find_svnr_regex,
            find_ibans_regex,
            find_birth_date_regex,
            find_address_regex,
            find_titled_names_regex,
            find_labeled_names_regex,
            find_license_plate_regex,
            find_phone_regex,
            find_passport_regex,
            find_id_card_regex,
            find_tax_number_regex,
        ]

        for finder in finders:
            new_entities = finder(text)
            for entity in new_entities:
                # Only add if not overlapping with an already-detected entity
                if not any(
                    entities_overlap(entity.start, entity.end, ex.start, ex.end)
                    for ex in all_entities
                ):
                    all_entities.append(entity)

        return all_entities
