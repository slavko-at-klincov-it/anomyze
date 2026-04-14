"""
Base channel abstraction for Anomyze output formatting.

All output channels (GovGPT, IFG, KAPA) inherit from BaseChannel
and implement their own format_output logic.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass

from anomyze.config.settings import Settings
from anomyze.pipeline import DetectedEntity
from anomyze.pipeline.quality_check import QualityReport


@dataclass
class ChannelResult:
    """Base result type for all channels.

    Attributes:
        text: The processed text with PII replaced.
        entities: List of all detected entities.
        entity_count: Total number of detected entities.
        channel: Name of the channel that produced this result.
        quality_report: Optional post-anonymization quality check report.
    """

    text: str
    entities: list[DetectedEntity]
    channel: str
    quality_report: QualityReport | None = None

    @property
    def entity_count(self) -> int:
        """Total number of detected entities."""
        return len(self.entities)


class BaseChannel(ABC):
    """Abstract base class for output channels.

    Each channel defines how detected PII entities are replaced
    in the output text and what metadata is produced.
    """

    @abstractmethod
    def format_output(
        self,
        text: str,
        entities: list[DetectedEntity],
        settings: Settings,
        original_text: str = "",
    ) -> ChannelResult:
        """Format the text and entities according to channel rules.

        Args:
            text: The preprocessed text (after encoding fixes).
            entities: All detected entities from all pipeline layers.
            settings: Configuration settings.
            original_text: The original text before preprocessing.

        Returns:
            A channel-specific ChannelResult subclass.
        """
        ...
