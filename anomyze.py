#!/usr/bin/env python3
"""
Anomyze - Souveräne KI-Anonymisierungsschicht

This file is kept for backwards compatibility.
The main code has been refactored into the anomyze/ package.

Usage:
    python anomyze.py <input.txt> [output.txt] [--smooth] [--channel govgpt|ifg|kapa]
    python anomyze.py --interactive [--smooth]

Or install as package:
    pip install -e .
    anomyze <input.txt> [output.txt] [--smooth]
"""

# Import everything from the package for backwards compatibility
from anomyze import (
    __version__,
    anonymize,
    AnonymizeResult,
    PipelineOrchestrator,
    DetectedEntity,
    load_models,
    get_device,
    fix_encoding,
    smooth_text_with_ollama,
    COMPANY_CONTEXT_PATTERNS,
    NORMAL_CONTEXT_WORDS,
    ENTITY_BLACKLIST,
    clean_entity_word,
    expand_to_word_boundaries,
    Settings,
    get_settings,
)

from anomyze.patterns import (
    find_emails_regex,
    find_titled_names_regex,
    find_labeled_names_regex,
    find_ibans_regex,
    find_svnr_regex,
    find_aktenzahl_regex,
    find_license_plate_regex,
    find_phone_regex,
    find_birth_date_regex,
)

# Re-export model names for backwards compatibility
PII_MODEL = "HuggingLil/pii-sensitive-ner-german"
ORG_MODEL = "dslim/bert-base-NER"
MLM_MODEL = "dbmdz/bert-base-german-cased"


def main():
    """Run CLI."""
    from anomyze.cli import main as cli_main
    cli_main()


if __name__ == "__main__":
    main()
