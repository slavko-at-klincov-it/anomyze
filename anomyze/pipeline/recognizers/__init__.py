"""Pattern recognizer package (Presidio-compatible API)."""

from anomyze.pipeline.recognizers.austrian import (
    ATAktenzahlRecognizer,
    ATFirmenbuchRecognizer,
    ATIBANRecognizer,
    ATKFZRecognizer,
    ATPassportRecognizer,
    ATSVNRRecognizer,
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
]
