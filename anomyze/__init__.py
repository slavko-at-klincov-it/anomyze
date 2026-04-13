"""
Anomyze - Souveräne KI-Anonymisierungsschicht
https://anomyze.it

Output-Filter für die "Public AI"-Initiative der österreichischen
Bundesverwaltung. Die KI-Tools (GovGPT, ELAK-KI, KAPA) arbeiten
intern mit vollen Daten. Anomyze filtert den Output, bevor er
das System verlässt.

3-stage detection pipeline:
- Stage 1: Regex patterns (Austrian-specific formats)
- Stage 2: NER models (names, organizations, locations)
- Stage 3: Perplexity anomaly detection (unknown entities)

3 output channels:
- GovGPT: Reversible placeholders — output filtered before forwarding
- IFG: Irreversible redaction — output filtered before publication
- KAPA: Placeholders + audit trail — output filtered for parliamentary use

100% local — no cloud, no API calls.
"""

__version__ = "2.0.0"
__author__ = "Anomyze Team"
__license__ = "MIT"

# Core pipeline
# Config
from anomyze.config.settings import Settings, get_settings

# Patterns
from anomyze.patterns import (
    COMPANY_CONTEXT_PATTERNS,
    ENTITY_BLACKLIST,
    NORMAL_CONTEXT_WORDS,
)

# Entity format
from anomyze.pipeline import DetectedEntity
from anomyze.pipeline.orchestrator import (
    AnonymizeResult,
    PipelineOrchestrator,
    anonymize,
    fix_encoding,
    get_device,
    load_models,
    smooth_text_with_ollama,
)

# Entity utilities
from anomyze.pipeline.utils import clean_entity_word, expand_to_word_boundaries

__all__ = [
    # Core
    "anonymize",
    "AnonymizeResult",
    "PipelineOrchestrator",
    "DetectedEntity",
    # Models
    "load_models",
    "get_device",
    # Processing
    "fix_encoding",
    "smooth_text_with_ollama",
    # Patterns
    "COMPANY_CONTEXT_PATTERNS",
    "NORMAL_CONTEXT_WORDS",
    "ENTITY_BLACKLIST",
    # Entities
    "clean_entity_word",
    "expand_to_word_boundaries",
    # Config
    "Settings",
    "get_settings",
    # Version
    "__version__",
]
