#!/usr/bin/env python3
"""
Anomyze - Intelligent PII Anonymizer for German Text

This file is kept for backwards compatibility.
The main code has been refactored into the anomyze/ package.

Usage:
    python anomyze.py <input.txt> [output.txt] [--smooth]
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
    load_models,
    get_device,
    COMPANY_CONTEXT_PATTERNS,
    NORMAL_CONTEXT_WORDS,
    ENTITY_BLACKLIST,
    clean_entity_word,
    expand_to_word_boundaries,
    Settings,
    get_settings,
)

from anomyze.core import (
    fix_encoding,
    detect_anomalies,
    smooth_text_with_ollama,
)

from anomyze.patterns import (
    find_emails_regex,
    find_titled_names_regex,
    find_labeled_names_regex,
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
