"""
Configuration management for Anomyze.

Provides centralized settings for all pipeline components,
channel configuration, audit logging, and API server.
"""

import os
from dataclasses import dataclass


@dataclass
class Settings:
    """Anomyze configuration settings.

    Controls all aspects of the anonymization pipeline including
    model selection, detection thresholds, channel behavior,
    audit logging, and API server configuration.
    """

    # Model settings
    pii_model: str = "HuggingLil/pii-sensitive-ner-german"
    org_model: str = "Davlan/xlm-roberta-large-ner-hrl"
    mlm_model: str = "dbmdz/bert-base-german-cased"
    gliner_model: str = "urchade/gliner_large-v2.1"

    # Detection thresholds
    pii_threshold: float = 0.7
    org_threshold: float = 0.7
    gliner_threshold: float = 0.4
    anomaly_threshold: float = 0.5
    perplexity_threshold: float = 0.3

    # Processing options
    fix_encoding: bool = True
    use_adversarial_normalization: bool = True
    use_regex_fallback: bool = True
    use_anomaly_detection: bool = True
    use_gliner: bool = True

    # GLiNER entity types (zero-shot, configurable)
    gliner_entity_types: tuple[str, ...] = (
        "person name",
        "email address",
        "phone number",
        "physical address",
        "date of birth",
        "organization",
        "company name",
        "social security number",
        "bank account number",
        "license plate number",
    )

    # Device settings (auto-detected if None)
    device: str | None = None

    # Smoothing (Ollama)
    smooth_model: str = "qwen2.5:14b"
    smooth_timeout: int = 120

    # Channel configuration
    default_channel: str = "govgpt"

    # KAPA-specific
    kapa_review_threshold: float = 0.85
    audit_enabled: bool = False
    audit_log_path: str | None = None

    # API configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # Mapping persistence
    mapping_persist_path: str | None = None

    @classmethod
    def from_env(cls) -> "Settings":
        """Create settings from environment variables.

        All settings can be overridden via ANOMYZE_* environment variables.
        """
        return cls(
            pii_model=os.getenv("ANOMYZE_PII_MODEL", cls.pii_model),
            org_model=os.getenv("ANOMYZE_ORG_MODEL", cls.org_model),
            mlm_model=os.getenv("ANOMYZE_MLM_MODEL", cls.mlm_model),
            gliner_model=os.getenv("ANOMYZE_GLINER_MODEL", cls.gliner_model),
            pii_threshold=float(os.getenv("ANOMYZE_PII_THRESHOLD", str(cls.pii_threshold))),
            org_threshold=float(os.getenv("ANOMYZE_ORG_THRESHOLD", str(cls.org_threshold))),
            gliner_threshold=float(
                os.getenv("ANOMYZE_GLINER_THRESHOLD", str(cls.gliner_threshold))
            ),
            anomaly_threshold=float(
                os.getenv("ANOMYZE_ANOMALY_THRESHOLD", str(cls.anomaly_threshold))
            ),
            perplexity_threshold=float(
                os.getenv("ANOMYZE_PERPLEXITY_THRESHOLD", str(cls.perplexity_threshold))
            ),
            use_gliner=os.getenv("ANOMYZE_USE_GLINER", "true").lower() in ("true", "1", "yes"),
            device=os.getenv("ANOMYZE_DEVICE"),
            default_channel=os.getenv("ANOMYZE_DEFAULT_CHANNEL", cls.default_channel),
            kapa_review_threshold=float(
                os.getenv("ANOMYZE_KAPA_REVIEW_THRESHOLD", str(cls.kapa_review_threshold))
            ),
            audit_enabled=os.getenv("ANOMYZE_AUDIT_ENABLED", "").lower() in ("true", "1", "yes"),
            audit_log_path=os.getenv("ANOMYZE_AUDIT_LOG_PATH"),
            api_host=os.getenv("ANOMYZE_API_HOST", cls.api_host),
            api_port=int(os.getenv("ANOMYZE_API_PORT", str(cls.api_port))),
            mapping_persist_path=os.getenv("ANOMYZE_MAPPING_PERSIST_PATH"),
        )


# Global settings instance
_settings: Settings | None = None


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
