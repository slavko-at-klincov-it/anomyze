"""Pattern recognizer package (Presidio-compatible API)."""

from anomyze.pipeline.recognizers.austrian import (
    ATAktenzahlRecognizer,
    ATArt9Recognizer,
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
    "ATICD10Recognizer",
    "ATFuehrerscheinRecognizer",
    "ATZMRRecognizer",
    "ATGerichtsaktenzahlRecognizer",
    "ATArt9Recognizer",
]
