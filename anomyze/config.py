"""
Configuration management for Anomyze.
"""

from dataclasses import dataclass, field
from typing import Optional
import os


@dataclass
class Settings:
    """Anomyze configuration settings."""

    # Model settings
    pii_model: str = "HuggingLil/pii-sensitive-ner-german"
    org_model: str = "dslim/bert-base-NER"
    mlm_model: str = "dbmdz/bert-base-german-cased"

    # Detection thresholds
    pii_threshold: float = 0.7
    org_threshold: float = 0.7
    anomaly_threshold: float = 0.5
    perplexity_threshold: float = 0.3

    # Processing options
    fix_encoding: bool = True
    use_regex_fallback: bool = True
    use_anomaly_detection: bool = True

    # Device settings (auto-detected if None)
    device: Optional[str] = None

    # Smoothing (Ollama)
    smooth_model: str = "qwen2.5:14b"
    smooth_timeout: int = 120

    @classmethod
    def from_env(cls) -> "Settings":
        """Create settings from environment variables."""
        return cls(
            pii_model=os.getenv("ANOMYZE_PII_MODEL", cls.pii_model),
            org_model=os.getenv("ANOMYZE_ORG_MODEL", cls.org_model),
            mlm_model=os.getenv("ANOMYZE_MLM_MODEL", cls.mlm_model),
            pii_threshold=float(os.getenv("ANOMYZE_PII_THRESHOLD", cls.pii_threshold)),
            org_threshold=float(os.getenv("ANOMYZE_ORG_THRESHOLD", cls.org_threshold)),
            anomaly_threshold=float(os.getenv("ANOMYZE_ANOMALY_THRESHOLD", cls.anomaly_threshold)),
            device=os.getenv("ANOMYZE_DEVICE"),
        )


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get the global settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings.from_env()
    return _settings


def configure(settings: Settings) -> None:
    """Set the global settings instance."""
    global _settings
    _settings = settings
