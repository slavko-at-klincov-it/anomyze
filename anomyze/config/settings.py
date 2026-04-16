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

    # Optional model revisions (HF git SHA or tag). When set, the
    # ``ModelManager`` pins ``from_pretrained`` to that exact revision
    # for reproducibility — empty string means "track latest" (legacy
    # behaviour, not recommended for production).
    pii_model_revision: str = ""
    org_model_revision: str = ""
    mlm_model_revision: str = ""
    gliner_model_revision: str = ""

    # Hard-fail when a configured pin doesn't match the downloaded
    # checkpoint (after model_integrity check). When False the API
    # falls back to "degraded mode" with regex + Presidio-compat only.
    fail_on_model_integrity_mismatch: bool = False

    # Detection thresholds
    pii_threshold: float = 0.7
    org_threshold: float = 0.7
    gliner_threshold: float = 0.4
    presidio_threshold: float = 0.4
    anomaly_threshold: float = 0.5
    perplexity_threshold: float = 0.3

    # Quasi-identifier proximity window (characters).
    # Controls how close role / profession / relationship / age /
    # gender / location signals must appear to be treated as a
    # combined re-identifying attribute set.
    quasi_id_window: int = 200

    # Processing options
    fix_encoding: bool = True
    use_adversarial_normalization: bool = True
    use_leetspeak_normalization: bool = True
    use_regex_fallback: bool = True
    use_anomaly_detection: bool = True
    use_gliner: bool = True
    use_presidio_compat: bool = True
    run_quality_check: bool = True

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
        "austrian vat id",
        "bank identifier code",
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

    # When True (default), every DSGVO Art. 9 entity is flagged for
    # human review in the KAPA channel regardless of confidence. Set
    # to False to fall back to the regular ``kapa_review_threshold``
    # gate (legacy v1 behaviour).
    always_review_art9: bool = True

    # API configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # Request-size caps. ``max_request_text_chars`` is enforced by the
    # Pydantic validator on ``AnonymizeRequest.text``;
    # ``max_request_body_bytes`` is enforced by ``BodySizeLimitMiddleware``.
    max_request_text_chars: int = 50_000
    max_request_body_bytes: int = 500_000

    # Mapping persistence
    mapping_persist_path: str | None = None

    @classmethod
    def from_env(cls) -> "Settings":
        """Create settings from environment variables.

        All settings can be overridden via ANOMYZE_* environment variables.
        """
        _bool_true = ("true", "1", "yes")
        return cls(
            # Model selection
            pii_model=os.getenv("ANOMYZE_PII_MODEL", cls.pii_model),
            org_model=os.getenv("ANOMYZE_ORG_MODEL", cls.org_model),
            mlm_model=os.getenv("ANOMYZE_MLM_MODEL", cls.mlm_model),
            gliner_model=os.getenv("ANOMYZE_GLINER_MODEL", cls.gliner_model),
            # Model pinning (empty string = track latest)
            pii_model_revision=os.getenv("ANOMYZE_PII_MODEL_REVISION", ""),
            org_model_revision=os.getenv("ANOMYZE_ORG_MODEL_REVISION", ""),
            mlm_model_revision=os.getenv("ANOMYZE_MLM_MODEL_REVISION", ""),
            gliner_model_revision=os.getenv("ANOMYZE_GLINER_MODEL_REVISION", ""),
            fail_on_model_integrity_mismatch=os.getenv(
                "ANOMYZE_FAIL_ON_MODEL_INTEGRITY_MISMATCH", ""
            ).lower() in _bool_true,
            # Detection thresholds
            pii_threshold=float(os.getenv("ANOMYZE_PII_THRESHOLD", str(cls.pii_threshold))),
            org_threshold=float(os.getenv("ANOMYZE_ORG_THRESHOLD", str(cls.org_threshold))),
            gliner_threshold=float(
                os.getenv("ANOMYZE_GLINER_THRESHOLD", str(cls.gliner_threshold))
            ),
            presidio_threshold=float(
                os.getenv("ANOMYZE_PRESIDIO_THRESHOLD", str(cls.presidio_threshold))
            ),
            anomaly_threshold=float(
                os.getenv("ANOMYZE_ANOMALY_THRESHOLD", str(cls.anomaly_threshold))
            ),
            perplexity_threshold=float(
                os.getenv("ANOMYZE_PERPLEXITY_THRESHOLD", str(cls.perplexity_threshold))
            ),
            quasi_id_window=int(
                os.getenv("ANOMYZE_QUASI_ID_WINDOW", str(cls.quasi_id_window))
            ),
            # Processing flags (default True → "true" fallback)
            fix_encoding=os.getenv("ANOMYZE_FIX_ENCODING", "true").lower() in _bool_true,
            use_adversarial_normalization=os.getenv(
                "ANOMYZE_USE_ADVERSARIAL_NORMALIZATION", "true"
            ).lower() in _bool_true,
            use_leetspeak_normalization=os.getenv(
                "ANOMYZE_USE_LEETSPEAK_NORMALIZATION", "true"
            ).lower() in _bool_true,
            use_regex_fallback=os.getenv(
                "ANOMYZE_USE_REGEX_FALLBACK", "true"
            ).lower() in _bool_true,
            use_anomaly_detection=os.getenv(
                "ANOMYZE_USE_ANOMALY_DETECTION", "true"
            ).lower() in _bool_true,
            use_gliner=os.getenv("ANOMYZE_USE_GLINER", "true").lower() in _bool_true,
            use_presidio_compat=os.getenv(
                "ANOMYZE_USE_PRESIDIO_COMPAT", "true"
            ).lower() in _bool_true,
            run_quality_check=os.getenv(
                "ANOMYZE_RUN_QUALITY_CHECK", "true"
            ).lower() in _bool_true,
            # Device
            device=os.getenv("ANOMYZE_DEVICE"),
            # Smoothing (Ollama, optional)
            smooth_model=os.getenv("ANOMYZE_SMOOTH_MODEL", cls.smooth_model),
            smooth_timeout=int(
                os.getenv("ANOMYZE_SMOOTH_TIMEOUT", str(cls.smooth_timeout))
            ),
            # Channel configuration
            default_channel=os.getenv("ANOMYZE_DEFAULT_CHANNEL", cls.default_channel),
            kapa_review_threshold=float(
                os.getenv("ANOMYZE_KAPA_REVIEW_THRESHOLD", str(cls.kapa_review_threshold))
            ),
            audit_enabled=os.getenv("ANOMYZE_AUDIT_ENABLED", "").lower() in _bool_true,
            audit_log_path=os.getenv("ANOMYZE_AUDIT_LOG_PATH"),
            always_review_art9=os.getenv(
                "ANOMYZE_ALWAYS_REVIEW_ART9", "true"
            ).lower() in _bool_true,
            # API
            api_host=os.getenv("ANOMYZE_API_HOST", cls.api_host),
            api_port=int(os.getenv("ANOMYZE_API_PORT", str(cls.api_port))),
            max_request_text_chars=int(
                os.getenv("ANOMYZE_MAX_REQUEST_TEXT_CHARS", str(cls.max_request_text_chars))
            ),
            max_request_body_bytes=int(
                os.getenv("ANOMYZE_MAX_REQUEST_BODY_BYTES", str(cls.max_request_body_bytes))
            ),
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
