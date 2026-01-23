"""
Anomyze - Intelligent PII Anonymizer for German Text
https://anomyze.it

A 3-layer detection system for anonymizing personal information:
- Layer 1: PII Model (names, emails, phones, dates)
- Layer 2: NER Model (organizations, locations)
- Layer 3: Perplexity Anomaly Detection (unknown companies)

100% local - no cloud, no API calls.
"""

__version__ = "1.1.0"
__author__ = "Anomyze Team"
__license__ = "MIT"

from anomyze.core import anonymize, AnonymizeResult
from anomyze.models import load_models, get_device
from anomyze.patterns import (
    COMPANY_CONTEXT_PATTERNS,
    NORMAL_CONTEXT_WORDS,
    ENTITY_BLACKLIST,
)
from anomyze.entities import clean_entity_word, expand_to_word_boundaries
from anomyze.config import Settings, get_settings

__all__ = [
    # Core
    "anonymize",
    "AnonymizeResult",
    # Models
    "load_models",
    "get_device",
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
