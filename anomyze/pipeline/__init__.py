"""
Core anonymization pipeline for Anomyze.

Provides the 3-stage detection pipeline (Regex, NER, Context)
and the unified DetectedEntity format used across all layers.
"""

from dataclasses import dataclass


@dataclass
class DetectedEntity:
    """A single detected PII entity from any pipeline layer.

    This is the unified entity format produced by all detection layers
    and consumed by all output channels. Every pipeline layer must
    convert its raw results into this format.

    Attributes:
        word: The original text span that was detected.
        entity_group: Category of the entity (PER, ORG, EMAIL, LOC, SVN,
            IBAN, TELEFON, GEBURTSDATUM, AKTENZAHL, KFZ, REISEPASS,
            PERSONALAUSWEIS, ADRESSE, STEUERNUMMER, ORG_DETECTED).
        score: Confidence score between 0.0 and 1.0.
        start: Character offset of the entity start in the source text.
        end: Character offset of the entity end in the source text.
        source: Which detection layer produced this entity
            (regex, regex_title, regex_label, pii, org, perplexity).
        context: Description of the matching context pattern
            (only populated by the perplexity/context layer).
        anomaly_score: Raw anomaly score from perplexity detection
            (only populated by the context layer).
        placeholder: The placeholder string assigned by the output channel.
            Not set by detection layers.
    """

    word: str
    entity_group: str
    score: float
    start: int
    end: int
    source: str
    context: str = ""
    anomaly_score: float = 0.0
    placeholder: str = ""

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "word": self.word,
            "entity_group": self.entity_group,
            "score": self.score,
            "start": self.start,
            "end": self.end,
            "source": self.source,
            "context": self.context,
            "anomaly_score": self.anomaly_score,
            "placeholder": self.placeholder,
        }


__all__ = ["DetectedEntity"]
