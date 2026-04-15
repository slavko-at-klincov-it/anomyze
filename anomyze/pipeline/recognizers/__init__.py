"""Pattern recognizer package (Presidio-compatible API)."""

from anomyze.pipeline.recognizers.austrian import (
    ATAktenzahlRecognizer,
    ATBICRecognizer,
    ATFirmenbuchRecognizer,
    ATIBANRecognizer,
    ATKFZRecognizer,
    ATNameRecognizer,
    ATPassportRecognizer,
    ATSVNRRecognizer,
    ATUIDRecognizer,
)
from anomyze.pipeline.recognizers.base import (
    Pattern,
    PatternRecognizer,
    RecognizerResult,
)

__all__ = [
    "Pattern",
    "PatternRecognizer",
    "RecognizerResult",
    "ATSVNRRecognizer",
    "ATIBANRecognizer",
    "ATKFZRecognizer",
    "ATFirmenbuchRecognizer",
    "ATPassportRecognizer",
    "ATAktenzahlRecognizer",
    "ATNameRecognizer",
    "ATUIDRecognizer",
    "ATBICRecognizer",
]
