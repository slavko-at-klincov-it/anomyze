"""
Presidio-compatible detection layer using local PatternRecognizers.

Implements the same recognizer-based API as Microsoft Presidio without
the presidio-analyzer dependency. Provides context-aware confidence
scoring and Austrian-specific recognizers (including types not covered
by the regex layer, e.g., Firmenbuchnummer).
"""

from anomyze.config.settings import Settings, get_settings
from anomyze.patterns import is_blacklisted
from anomyze.pipeline import DetectedEntity
from anomyze.pipeline.recognizers import (
    ATAktenzahlRecognizer,
    ATBICRecognizer,
    ATFirmenbuchRecognizer,
    ATFuehrerscheinRecognizer,
    ATGerichtsaktenzahlRecognizer,
    ATIBANRecognizer,
    ATICD10Recognizer,
    ATKFZRecognizer,
    ATNameRecognizer,
    ATPassportRecognizer,
    ATSVNRRecognizer,
    ATUIDRecognizer,
    ATZMRRecognizer,
    PatternRecognizer,
)

# Map recognizer entity types to internal entity_group names used by channels
_ENTITY_TYPE_MAP: dict[str, str] = {
    "AT_SVNR": "SVN",
    "AT_IBAN": "IBAN",
    "AT_KFZ": "KFZ",
    "AT_FIRMENBUCH": "FIRMENBUCH",
    "AT_PASSPORT": "REISEPASS",
    "AT_AKTENZAHL": "AKTENZAHL",
    "AT_NAME": "PER",
    "AT_UID": "UID",
    "BIC": "BIC",
    "HEALTH_DIAGNOSIS": "HEALTH_DIAGNOSIS",
    "AT_FUEHRERSCHEIN": "FUEHRERSCHEIN",
    "AT_ZMR": "ZMR",
    "AT_GERICHTSAKTENZAHL": "GERICHTSAKTENZAHL",
}


def _default_recognizers() -> list[PatternRecognizer]:
    return [
        ATSVNRRecognizer(),
        ATIBANRecognizer(),
        ATKFZRecognizer(),
        ATFirmenbuchRecognizer(),
        ATPassportRecognizer(),
        ATAktenzahlRecognizer(),
        ATNameRecognizer(),
        ATUIDRecognizer(),
        ATBICRecognizer(),
        ATICD10Recognizer(),
        ATFuehrerscheinRecognizer(),
        ATZMRRecognizer(),
        ATGerichtsaktenzahlRecognizer(),
    ]


class PresidioCompatLayer:
    """Detection layer using Presidio-compatible local recognizers.

    Provides the same recognizer-based interface as Microsoft Presidio
    without depending on presidio-analyzer. Adds context-aware scoring
    and Austrian-specific recognizers.

    Custom recognizer sets can be supplied via the constructor.
    """

    def __init__(self, recognizers: list[PatternRecognizer] | None = None):
        self.recognizers = (
            recognizers if recognizers is not None else _default_recognizers()
        )

    def process(
        self,
        text: str,
        settings: Settings | None = None,
    ) -> list[DetectedEntity]:
        """Run all recognizers and return matched entities.

        Args:
            text: Input text to analyze.
            settings: Configuration (uses presidio_threshold).

        Returns:
            DetectedEntity list. Threshold and blacklist filtered.
        """
        if settings is None:
            settings = get_settings()

        entities: list[DetectedEntity] = []
        threshold = settings.presidio_threshold

        for recognizer in self.recognizers:
            for result in recognizer.analyze(text):
                if result.score < threshold:
                    continue
                if is_blacklisted(result.text):
                    continue

                entities.append(DetectedEntity(
                    word=result.text,
                    entity_group=_ENTITY_TYPE_MAP.get(
                        result.entity_type, result.entity_type
                    ),
                    score=result.score,
                    start=result.start,
                    end=result.end,
                    source="presidio_compat",
                ))

        return entities
