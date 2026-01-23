"""
Core anonymization logic for Anomyze.

This module contains the main anonymization function that combines
all detection layers.
"""

import re
import subprocess
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple

from anomyze.config import get_settings, Settings
from anomyze.patterns import (
    COMPANY_CONTEXT_PATTERNS,
    NORMAL_CONTEXT_WORDS,
    ENTITY_BLACKLIST,
    find_emails_regex,
    find_titled_names_regex,
    find_labeled_names_regex,
    is_blacklisted,
)
from anomyze.entities import clean_entity_word, entities_overlap


@dataclass
class AnonymizeResult:
    """Result of anonymization operation."""
    text: str
    mapping: Dict[str, str]
    entities: List[Dict[str, Any]]
    original_text: str = ""

    @property
    def entity_count(self) -> int:
        return len(self.entities)

    @property
    def unique_entity_count(self) -> int:
        return len(self.mapping)


# Encoding fixes for common transcription software issues
ENCODING_REPLACEMENTS = {
    # German umlauts (various broken encodings)
    '‰': 'ä', 'Š': 'ä',
    '÷': 'ö',
    '¸': 'ü', '³': 'ü',
    'ƒ': 'ä',
    'fl': 'ß', 'fi': 'ß', '§': 'ß',
    'Ð': 'Ä', '⁄': 'Ü',
    # Common OCR/transcription errors
    '´': "'", '`': "'",
    '—': '-', '–': '-',
    '…': '...',
    '"': '"', '"': '"',
    ''': "'", ''': "'",
    '\u00a0': ' ',  # Non-breaking space
    '\ufeff': '',   # BOM
}


def fix_encoding(text: str) -> str:
    """Fix common encoding issues from transcription software."""
    for wrong, correct in ENCODING_REPLACEMENTS.items():
        text = text.replace(wrong, correct)
    return text


def detect_anomalies(
    text: str,
    mlm_pipeline: Any,
    existing_entities: List[Dict[str, Any]],
    settings: Optional[Settings] = None
) -> List[Dict[str, Any]]:
    """
    Detect potential company names using perplexity-based anomaly detection.

    Core idea: In "bei uns in der Küche" → "Küche" is expected
               In "bei uns in der Siemens" → "Siemens" is unexpected → likely a company
    """
    if settings is None:
        settings = get_settings()

    anomalies = []

    for pattern, description, include_suffix in COMPANY_CONTEXT_PATTERNS:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            word = match.group(1)
            word_start = match.start(1)
            word_end = match.end(1)

            # If pattern includes suffix (like "Bank"), extend the word
            if include_suffix and match.lastindex >= 2:
                suffix = match.group(2)
                word = word + " " + suffix
                word_end = match.end(2)

            word_lower = word.lower()

            # Skip normal context words
            if word_lower.split()[0] in NORMAL_CONTEXT_WORDS:
                continue

            # Skip if already detected with high confidence
            already_detected_well = False
            for e in existing_entities:
                if entities_overlap(word_start, word_end, e['start'], e['end']):
                    if e.get('score', 0) >= 0.8:
                        already_detected_well = True
                        break
            if already_detected_well:
                continue

            if len(word) < 3:
                continue

            # Check perplexity
            context_start = max(0, match.start() - 30)
            context_end = min(len(text), match.end() + 30)
            context = text[context_start:context_end]

            relative_start = match.start(1) - context_start
            relative_end = match.end(1) - context_start
            masked_context = context[:relative_start] + "[MASK]" + context[relative_end:]

            try:
                predictions = mlm_pipeline(masked_context)
                predicted_tokens = [p['token_str'].strip().lower() for p in predictions]

                first_word = word_lower.split()[0] if ' ' in word_lower else word_lower
                is_expected = first_word in predicted_tokens

                if is_expected:
                    position = predicted_tokens.index(first_word)
                    anomaly_score = position / len(predictions)
                else:
                    anomaly_score = 1.0

                if anomaly_score > settings.perplexity_threshold and word[0].isupper():
                    anomalies.append({
                        'word': word,
                        'entity_group': 'ORG_DETECTED',
                        'score': min(0.95, 0.6 + anomaly_score * 0.35),
                        'start': word_start,
                        'end': word_end,
                        'source': 'perplexity',
                        'context': description,
                        'anomaly_score': anomaly_score
                    })

            except Exception:
                continue

    return anomalies


def anonymize(
    text: str,
    pii_pipeline: Any,
    org_pipeline: Any,
    mlm_pipeline: Any,
    settings: Optional[Settings] = None
) -> AnonymizeResult:
    """
    Main anonymization function combining all detection methods.

    Args:
        text: Text to anonymize
        pii_pipeline: PII detection pipeline
        org_pipeline: Organization/NER detection pipeline
        mlm_pipeline: MLM pipeline for anomaly detection
        settings: Settings instance (uses global if None)

    Returns:
        AnonymizeResult with anonymized text, mapping, and entities
    """
    if settings is None:
        settings = get_settings()

    original_text = text

    # Fix encoding issues first
    if settings.fix_encoding:
        text = fix_encoding(text)

    all_entities: List[Dict[str, Any]] = []

    # Layer 0: Regex fallback for emails (most reliable)
    if settings.use_regex_fallback:
        email_entities = find_emails_regex(text)
        all_entities.extend(email_entities)

        # Layer 0b: Regex for titled names (Herrn Schmidt, Frau Müller)
        titled_name_entities = find_titled_names_regex(text)
        for e in titled_name_entities:
            if not any(entities_overlap(e['start'], e['end'], ex['start'], ex['end'])
                       for ex in all_entities):
                all_entities.append(e)

        # Layer 0c: Regex for labeled names (Protokollführer: Name)
        labeled_name_entities = find_labeled_names_regex(text)
        for e in labeled_name_entities:
            if not any(entities_overlap(e['start'], e['end'], ex['start'], ex['end'])
                       for ex in all_entities):
                all_entities.append(e)

    # Layer 1: PII detection
    pii_entities = pii_pipeline(text)
    for e in pii_entities:
        word, start, end = clean_entity_word(e['word'], text, e['start'], e['end'])
        if e['score'] < settings.pii_threshold:
            continue
        if is_blacklisted(word):
            continue
        if any(entities_overlap(start, end, ex['start'], ex['end']) for ex in all_entities):
            continue
        all_entities.append({
            'word': word,
            'entity_group': e['entity_group'],
            'score': e['score'],
            'start': start,
            'end': end,
            'source': 'pii'
        })

    # Layer 2: ORG/NER detection
    org_entities = org_pipeline(text)
    org_entities = [e for e in org_entities if e['entity_group'] in ('ORG', 'LOC', 'PER')]
    for e in org_entities:
        word, start, end = clean_entity_word(e['word'], text, e['start'], e['end'])
        if is_blacklisted(word):
            continue
        if any(entities_overlap(start, end, ex['start'], ex['end']) for ex in all_entities):
            continue
        if e['score'] >= settings.org_threshold:
            all_entities.append({
                'word': word,
                'entity_group': e['entity_group'],
                'score': e['score'],
                'start': start,
                'end': end,
                'source': 'org'
            })

    # Layer 3: Anomaly detection
    if settings.use_anomaly_detection:
        anomalies = detect_anomalies(text, mlm_pipeline, all_entities, settings)
        for a in anomalies:
            if not any(entities_overlap(a['start'], a['end'], ex['start'], ex['end'])
                       for ex in all_entities):
                all_entities.append(a)

    if not all_entities:
        return AnonymizeResult(
            text=text,
            mapping={},
            entities=[],
            original_text=original_text
        )

    # Sort by position
    all_entities = sorted(all_entities, key=lambda x: x['start'])

    # Build placeholder mapping
    type_counters: Dict[str, int] = {}
    text_to_placeholder: Dict[str, str] = {}
    mapping: Dict[str, str] = {}

    for entity in all_entities:
        original = entity['word'].strip()
        entity_type = entity['entity_group']
        score = entity['score']

        if not original or score < settings.anomaly_threshold:
            continue

        normalized = original.lower()

        if normalized not in text_to_placeholder:
            if entity_type not in type_counters:
                type_counters[entity_type] = 0
            type_counters[entity_type] += 1

            placeholder = f"[{entity_type}_{type_counters[entity_type]}]"
            text_to_placeholder[normalized] = placeholder
            mapping[placeholder] = original

        entity['placeholder'] = text_to_placeholder[normalized]

    # Apply replacements (reverse order to preserve positions)
    result = text
    for entity in sorted(all_entities, key=lambda x: x['start'], reverse=True):
        if 'placeholder' not in entity or entity['score'] < settings.anomaly_threshold:
            continue

        start = entity['start']
        end = entity['end']
        placeholder = entity['placeholder']

        before = result[:start]
        after = result[end:]

        # Determine if we need spaces
        need_space_before = before and before[-1] not in ' \n\t('
        need_space_after = after and after[0] not in ' \n\t.,;:!?)'

        # Build replacement with proper spacing
        replacement = ''
        if need_space_before:
            replacement += ' '
        replacement += placeholder
        if need_space_after:
            replacement += ' '

        result = before + replacement + after

    return AnonymizeResult(
        text=result,
        mapping=mapping,
        entities=all_entities,
        original_text=original_text
    )


def smooth_text_with_ollama(
    text: str,
    model: str = "qwen2.5:14b",
    timeout: int = 120
) -> str:
    """
    Smooth/rewrite text using local Ollama LLM.
    Protects placeholders like [ORG_1] during processing.
    """
    # Step 1: Protect placeholders by replacing with unique tokens
    placeholder_pattern = r'\[([A-Z_]+_\d+)\]'
    placeholders = re.findall(placeholder_pattern, text)
    protected_text = text

    placeholder_map = {}
    for i, ph in enumerate(set(placeholders)):
        token = f"§§§PLACEHOLDER{i}§§§"
        placeholder_map[token] = f"[{ph}]"
        protected_text = protected_text.replace(f"[{ph}]", token)

    # Step 2: Create prompt for smoothing
    prompt = f"""Du bist ein Texteditor. Glätte den folgenden deutschen Text:

REGELN:
- Entferne Füllwörter (ähm, also, halt, ja, mhm, etc.)
- Korrigiere Grammatik und mache Sätze flüssiger
- Behalte die Bedeutung und alle Fakten exakt bei
- WICHTIG: Alle §§§PLACEHOLDER...§§§ Tokens MÜSSEN exakt unverändert bleiben!
- Entferne keine Informationen
- Behalte Zeitstempel und Sprechernamen

TEXT:
{protected_text}

GEGLÄTTETER TEXT:"""

    # Step 3: Call Ollama
    try:
        result = subprocess.run(
            ["ollama", "run", model, prompt],
            capture_output=True,
            text=True,
            timeout=timeout
        )

        if result.returncode != 0:
            print(f"Ollama error: {result.stderr}")
            return text  # Return original on error

        smoothed = result.stdout.strip()

        # Step 4: Restore placeholders
        for token, original in placeholder_map.items():
            smoothed = smoothed.replace(token, original)

        return smoothed

    except subprocess.TimeoutExpired:
        print("Ollama timeout - Text zu lang oder Model zu langsam")
        return text
    except FileNotFoundError:
        print("Ollama nicht gefunden. Bitte installieren: https://ollama.ai")
        return text
