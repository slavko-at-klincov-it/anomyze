#!/usr/bin/env python3
"""
Anomyze - Intelligent PII Anonymizer for German Text
https://anomyze.it

Features:
- 3-layer detection: PII Model + NER Model + Perplexity Anomaly Detection
- Finds unknown company names through language model analysis
- Optimized for Apple Silicon (MPS)
- 100% local - no cloud, no API calls
"""

import sys
import json
import re
import subprocess
import torch
from transformers import pipeline
from pathlib import Path

# For better interactive input
try:
    from prompt_toolkit import prompt
    from prompt_toolkit.key_binding import KeyBindings
    from prompt_toolkit.keys import Keys
    PROMPT_TOOLKIT_AVAILABLE = True
except ImportError:
    PROMPT_TOOLKIT_AVAILABLE = False

__version__ = "1.0.0"

PII_MODEL = "HuggingLil/pii-sensitive-ner-german"
ORG_MODEL = "dslim/bert-base-NER"
MLM_MODEL = "dbmdz/bert-base-german-cased"

# Patterns that often precede company names
# Format: (regex_pattern, description, include_suffix)
COMPANY_CONTEXT_PATTERNS = [
    (r'\b[Bb]ei\s+uns\s+(?:in\s+)?(?:der\s+|dem\s+)?(\w+)', 'nach "bei uns in"', None),
    (r'\b[Aa]rbeite[tn]?\s+(?:bei|für)\s+(?:der\s+|dem\s+)?(\w+)', 'nach "arbeite bei"', None),
    (r'\b[Bb]ei\s+(?:der\s+|dem\s+)?(\w+)\s+(?:arbeite|angestellt|beschäftigt)', 'vor "arbeite/angestellt"', None),
    (r'\b[Kk]unde[n]?\s+(?:der\s+|dem\s+|von\s+)?(\w+)', 'nach "Kunde"', None),
    (r'\b[Pp]artner\s+(?:der\s+|dem\s+|von\s+)?(\w+)', 'nach "Partner"', None),
    (r'\b[Ll]ieferant(?:en)?\s+(?:der\s+|dem\s+|von\s+)?(\w+)', 'nach "Lieferant"', None),
    (r'\b[Ff]irma\s+(\w+)', 'nach "Firma"', None),
    (r'\b[Uu]nternehmen\s+(\w+)', 'nach "Unternehmen"', None),
    (r'\b(?:der|die|das)\s+(\w+)\s+(?:AG|GmbH|SE|KG|OG|eG)\b', 'vor AG/GmbH/etc', None),
    (r'\b[Vv]on\s+(?:der\s+)?(\w+)\s+(?:bekommen|erhalten|gehört)', 'nach "von X bekommen"', None),
    (r'\b[Zz]ur\s+(\w+)\s+(?:gewechselt|gegangen|gekommen)', 'nach "zur X gewechselt"', None),
    (r'\b[Bb]ei\s+(\w+)\s+(?:angefangen|gestartet|begonnen)', 'nach "bei X angefangen"', None),
    # Banks and financial institutions
    (r'\b(?:der|die|von\s+der)\s+(\w+)\s+([Bb]ank)\b', 'X Bank', 'Bank'),
    (r'\b(\w+)\s+([Bb]ank)\b', 'X Bank', 'Bank'),
    (r'\b(\w+)\s+([Vv]ersicherung)\b', 'X Versicherung', 'Versicherung'),
    (r'\b(\w+)\s+([Ss]parkasse)\b', 'X Sparkasse', 'Sparkasse'),
    (r'\b(\w+)\s+([Zz]entrale)\b', 'X Zentrale', 'Zentrale'),
    # Austrian/German banks without "Bank" suffix
    (r'\b(?:der|die|bei\s+der|in\s+der)\s+(Raiffeisen|Erste|BAWAG|Volksbank|Oberbank)\b', 'Bankname', None),
]

# Words that are normal in these contexts (not company names)
NORMAL_CONTEXT_WORDS = {
    'uns', 'mir', 'dir', 'ihm', 'ihr', 'ihnen', 'euch',
    'hause', 'haus', 'arbeit', 'küche', 'büro', 'office',
    'abteilung', 'team', 'gruppe', 'projekt',
    'stadt', 'land', 'ort', 'gegend', 'region',
    'schule', 'universität', 'uni', 'hochschule',
    'anfang', 'ende', 'mitte', 'zeit',
    'montag', 'dienstag', 'mittwoch', 'donnerstag', 'freitag', 'samstag', 'sonntag',
    'heute', 'morgen', 'gestern',
}

# Words that should NEVER be detected as entities (false positive filter)
ENTITY_BLACKLIST = {
    # Common German words often misdetected
    'protokoll', 'workshop', 'meeting', 'termin', 'termine',
    'projektleiter', 'projektleiterin', 'leiter', 'leiterin',
    'abteilung', 'it-abteilung', 'it', 'hr', 'pr',
    'e-mail', 'email', 'mail', 'tel', 'telefon',
    'januar', 'februar', 'märz', 'april', 'mai', 'juni',
    'juli', 'august', 'september', 'oktober', 'november', 'dezember',
    'jan', 'feb', 'mär', 'apr', 'jun', 'jul', 'aug', 'sep', 'okt', 'nov', 'dez',
    'montag', 'dienstag', 'mittwoch', 'donnerstag', 'freitag', 'samstag', 'sonntag',
    'uhr', 'zeit', 'datum', 'tag', 'woche', 'monat', 'jahr',
    'teilnehmer', 'teilnehmerin', 'kunde', 'kundin', 'kunden',
    'kontakt', 'erreichbar', 'büro', 'office', 'zentrale',
    'seine', 'ihre', 'der', 'die', 'das', 'von', 'vom', 'unter',
    # E-Mail variations (with various spacing)
    'seine e-mail', 'seine e - mail', 'seine email', 'seine mail',
    'seinee-mail', 'seineemail',  # after space removal
    'ihre e-mail', 'ihre email', 'ihreemail',
    'meine e-mail', 'meine email', 'meineemail',
    'e-mail', 'e - mail', 'email', 'mail',
    'nächster', 'nächste', 'nächstes', 'letzter', 'letzte', 'letztes',
    # Short fragments that are often subword errors
    'te', 'er', 'en', 'el', 'ho', 'an', 'in', 'um', 'zu',
}


def smooth_text_with_ollama(text, model="qwen2.5:14b"):
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
            timeout=120  # 2 minute timeout
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


def fix_encoding(text):
    """Fix common encoding issues from transcription software."""
    replacements = {
        # German umlauts (various broken encodings)
        '‰': 'ä', 'Š': 'ä',
        '÷': 'ö', '÷': 'ö',
        '¸': 'ü', '³': 'ü',
        'ƒ': 'ä', '÷': 'ö',
        'ﬂ': 'ß', 'ﬁ': 'ß', '§': 'ß',
        'Ð': 'Ä', '÷': 'Ö', '⁄': 'Ü',
        # Common OCR/transcription errors
        '´': "'", '`': "'",
        '—': '-', '–': '-',
        '…': '...',
        '"': '"', '"': '"',
        ''': "'", ''': "'",
        '\u00a0': ' ',  # Non-breaking space
        '\ufeff': '',   # BOM
    }

    for wrong, correct in replacements.items():
        text = text.replace(wrong, correct)

    return text


def get_device():
    """Detect best available device."""
    if torch.backends.mps.is_available():
        return "mps", "Apple Silicon GPU (MPS)"
    elif torch.cuda.is_available():
        return "cuda", "CUDA GPU"
    else:
        return "cpu", "CPU"


def load_models(device):
    """Load all three detection models."""
    print(f"Loading PII model...")
    pii_pipeline = pipeline(
        "token-classification",
        model=PII_MODEL,
        aggregation_strategy="simple",
        device=device
    )

    print(f"Loading NER model...")
    org_pipeline = pipeline(
        "token-classification",
        model=ORG_MODEL,
        aggregation_strategy="simple",
        device=device
    )

    print(f"Loading anomaly detection model...")
    mlm_pipeline = pipeline(
        "fill-mask",
        model=MLM_MODEL,
        device=device,
        top_k=50
    )

    print("All models loaded.\n")
    return pii_pipeline, org_pipeline, mlm_pipeline


def expand_to_word_boundaries(text, start, end):
    """Expand start/end to cover the full word, not just a subword token."""
    while start > 0 and text[start - 1].isalnum():
        start -= 1
    while end < len(text) and text[end].isalnum():
        end += 1
    return start, end


def clean_entity_word(word, text, start, end):
    """Fix subword tokens and clean up entity boundaries."""
    # Always expand to full word boundaries
    new_start, new_end = expand_to_word_boundaries(text, start, end)
    expanded_word = text[new_start:new_end]

    # If expanded word is different and longer, use it
    if len(expanded_word) > len(word.strip()) and expanded_word.strip():
        word = expanded_word
        start = new_start
        end = new_end

    # Strip leading/trailing whitespace and adjust positions
    original_word = word
    word = word.strip()
    if word != original_word:
        # Find actual start position of stripped word in text
        offset = original_word.index(word) if word in original_word else 0
        start = start + offset
        end = start + len(word)

    # Remove leading articles
    for prefix in ['der ', 'die ', 'das ', 'dem ', 'den ', 'von ', 'vom ', 'unter ']:
        if word.lower().startswith(prefix):
            word = word[len(prefix):]
            start = start + len(prefix)
            break

    # Remove trailing punctuation that got included
    while word and word[-1] in '.,;:!?)':
        word = word[:-1]
        end -= 1

    return word, start, end


def detect_anomalies(text, mlm_pipeline, existing_entities):
    """
    Detect potential company names using perplexity-based anomaly detection.

    Core idea: In "bei uns in der Küche" → "Küche" is expected
               In "bei uns in der Siemens" → "Siemens" is unexpected → likely a company
    """
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
                if not (word_end <= e['start'] or word_start >= e['end']):
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

                if anomaly_score > 0.3 and word[0].isupper():
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


def find_emails_regex(text):
    """Find email addresses using regex as fallback."""
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    emails = []
    for match in re.finditer(email_pattern, text):
        emails.append({
            'word': match.group(),
            'entity_group': 'EMAIL',
            'score': 0.99,
            'start': match.start(),
            'end': match.end(),
            'source': 'regex'
        })
    return emails


def anonymize(text, pii_pipeline, org_pipeline, mlm_pipeline):
    """Main anonymization function combining all detection methods."""

    # Fix encoding issues first
    text = fix_encoding(text)

    # Layer 0: Regex fallback for emails (most reliable)
    email_entities = find_emails_regex(text)

    # Layer 1: PII detection
    pii_entities = pii_pipeline(text)

    # Layer 2: ORG/NER detection
    org_entities = org_pipeline(text)
    org_entities = [e for e in org_entities if e['entity_group'] in ('ORG', 'LOC', 'PER')]

    all_entities = []

    # Add regex-detected emails first (highest priority)
    for e in email_entities:
        all_entities.append(e)

    for e in pii_entities:
        word, start, end = clean_entity_word(e['word'], text, e['start'], e['end'])
        if e['score'] < 0.7:
            continue
        # Skip blacklisted words
        word_clean = word.lower().replace(' - ', '-').replace(' ', '')
        if word_clean in ENTITY_BLACKLIST or len(word) < 3:
            continue
        # Skip if overlapping with already detected entity (e.g., email)
        overlaps = False
        for existing in all_entities:
            if not (end <= existing['start'] or start >= existing['end']):
                overlaps = True
                break
        if overlaps:
            continue
        all_entities.append({
            'word': word,
            'entity_group': e['entity_group'],
            'score': e['score'],
            'start': start,
            'end': end,
            'source': 'pii'
        })

    for e in org_entities:
        word, start, end = clean_entity_word(e['word'], text, e['start'], e['end'])

        # Skip blacklisted words
        word_clean = word.lower().replace(' - ', '-').replace(' ', '')
        if word_clean in ENTITY_BLACKLIST or len(word) < 3:
            continue

        overlaps = False
        for existing in all_entities:
            if not (end <= existing['start'] or start >= existing['end']):
                overlaps = True
                break
        if not overlaps and e['score'] >= 0.7:
            all_entities.append({
                'word': word,
                'entity_group': e['entity_group'],
                'score': e['score'],
                'start': start,
                'end': end,
                'source': 'org'
            })

    # Layer 3: Anomaly detection
    anomalies = detect_anomalies(text, mlm_pipeline, all_entities)
    for a in anomalies:
        overlaps = False
        for existing in all_entities:
            if not (a['end'] <= existing['start'] or a['start'] >= existing['end']):
                overlaps = True
                break
        if not overlaps:
            all_entities.append(a)

    if not all_entities:
        return text, {}, []

    all_entities = sorted(all_entities, key=lambda x: x['start'])

    # Build placeholder mapping
    type_counters = {}
    text_to_placeholder = {}
    mapping = {}

    for entity in all_entities:
        original = entity['word'].strip()
        entity_type = entity['entity_group']
        score = entity['score']

        if not original or score < 0.5:
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

    # Apply replacements
    result = text
    for entity in sorted(all_entities, key=lambda x: x['start'], reverse=True):
        if 'placeholder' in entity and entity['score'] >= 0.5:
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

    return result, mapping, all_entities


def get_multiline_input():
    """Get multiline input using prompt_toolkit or fallback."""
    if PROMPT_TOOLKIT_AVAILABLE:
        # Custom key bindings
        bindings = KeyBindings()

        @bindings.add(Keys.Enter)
        def _(event):
            """Enter submits the text."""
            event.current_buffer.validate_and_handle()

        @bindings.add(Keys.Escape, Keys.Enter)
        def _(event):
            """Escape+Enter inserts a newline."""
            event.current_buffer.insert_text('\n')

        @bindings.add('c-c')
        def _(event):
            """Ctrl+C to cancel."""
            event.app.exit(result=None)

        try:
            text = prompt(
                '> ',
                multiline=True,
                key_bindings=bindings,
                prompt_continuation='  ',
            )
            return text
        except (EOFError, KeyboardInterrupt):
            return None
    else:
        # Fallback to old method
        print("(prompt_toolkit nicht verfügbar - nutze END zum Absenden)")
        lines = []
        while True:
            try:
                line = input()
            except EOFError:
                break
            if line.strip().upper() == "END":
                break
            lines.append(line)
        return "\n".join(lines)


def print_banner():
    """Print Anomyze banner."""
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║     █████╗ ███╗   ██╗ ██████╗ ███╗   ███╗██╗   ██╗███████╗║
    ║    ██╔══██╗████╗  ██║██╔═══██╗████╗ ████║╚██╗ ██╔╝██╔════╝║
    ║    ███████║██╔██╗ ██║██║   ██║██╔████╔██║ ╚████╔╝ █████╗  ║
    ║    ██╔══██║██║╚██╗██║██║   ██║██║╚██╔╝██║  ╚██╔╝  ██╔══╝  ║
    ║    ██║  ██║██║ ╚████║╚██████╔╝██║ ╚═╝ ██║   ██║   ███████╗║
    ║    ╚═╝  ╚═╝╚═╝  ╚═══╝ ╚═════╝ ╚═╝     ╚═╝   ╚═╝   ╚══════╝║
    ║                                                           ║
    ║           Intelligent PII Anonymizer for German           ║
    ║                    https://anomyze.it                     ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝
    """)


def main():
    # Parse arguments
    args = sys.argv[1:]
    smooth_enabled = "--smooth" in args
    if smooth_enabled:
        args.remove("--smooth")

    if len(args) < 1:
        print_banner()
        print(f"""
    Version {__version__}

    Usage:
      python anomyze.py <input.txt> [output.txt] [--smooth]
      python anomyze.py --interactive [--smooth]

    Options:
      --smooth    Glätte Text mit lokalem LLM (Ollama + Qwen)

    Detection Layers:
      1. PII Model      → Names, emails, phone numbers
      2. NER Model      → Known companies, locations
      3. Anomaly Check  → Unknown companies via perplexity
        """)
        sys.exit(1)

    print_banner()

    if smooth_enabled:
        print("    Smooth Mode: ON (Ollama + Qwen)\n")

    device, device_name = get_device()
    print(f"    Device: {device_name}\n")

    pii_pipeline, org_pipeline, mlm_pipeline = load_models(device)

    if args[0] == "--interactive":
        print("=" * 60)
        print("Interactive Mode")
        if PROMPT_TOOLKIT_AVAILABLE:
            print("Enter        → Text absenden")
            print("Esc + Enter  → Neue Zeile")
            print("Ctrl+C       → Beenden")
        else:
            print("Paste text, then type END on a new line.")
            print("Type 'quit' or 'exit' to close.")
        print("=" * 60)

        while True:
            try:
                print("\n[Text eingeben]")

                text = get_multiline_input()

                if text is None:
                    print("\nGoodbye!")
                    sys.exit(0)

                text = text.strip()

                if text.lower() in ('quit', 'exit'):
                    print("Goodbye!")
                    sys.exit(0)

                if not text:
                    continue

                print("\nProcessing...")

                anonymized, mapping, all_entities = anonymize(text, pii_pipeline, org_pipeline, mlm_pipeline)

                print(f"\nDetected {len(all_entities)} entities:")
                for e in all_entities:
                    source_info = e['source']
                    if source_info == 'perplexity':
                        source_info = f"perplexity ({e.get('context', '')})"
                    print(f"  [{e['entity_group']:12}] \"{e['word']}\" (score: {e['score']:.2f}, source: {source_info})")

                print("\n" + "=" * 60)
                print("MAPPING")
                print("=" * 60)
                if mapping:
                    for placeholder, original in mapping.items():
                        print(f"  {placeholder:30} -> {original}")
                else:
                    print("  (no PII detected)")

                print("\n" + "=" * 60)
                print("ANONYMIZED TEXT")
                print("=" * 60)
                print(anonymized)

                # Optional: Smooth with local LLM
                if smooth_enabled:
                    print("\n" + "=" * 60)
                    print("SMOOTHING TEXT (Ollama)...")
                    print("=" * 60)
                    smoothed = smooth_text_with_ollama(anonymized)
                    print("\n" + "=" * 60)
                    print("SMOOTHED TEXT")
                    print("=" * 60)
                    print(smoothed)

            except KeyboardInterrupt:
                print("\n\nGoodbye!")
                sys.exit(0)

    else:
        input_path = Path(args[0])

        if not input_path.exists():
            print(f"Error: File not found: {input_path}")
            sys.exit(1)

        output_path = Path(args[1]) if len(args) > 1 else None
        mapping_path = output_path.with_suffix('.mapping.json') if output_path else Path("mapping.json")

        print(f"Reading: {input_path}")
        text = input_path.read_text(encoding="utf-8")
        print(f"Text length: {len(text):,} characters")

        print("Processing...")
        anonymized, mapping, all_entities = anonymize(text, pii_pipeline, org_pipeline, mlm_pipeline)

        print(f"\nFound {len(mapping)} unique entities")

        print("\n" + "=" * 60)
        print("MAPPING")
        print("=" * 60)
        for placeholder, original in mapping.items():
            print(f"  {placeholder:30} -> {original}")

        mapping_path.write_text(json.dumps(mapping, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"\nMapping saved to: {mapping_path}")

        # Optional: Smooth with local LLM
        final_text = anonymized
        if smooth_enabled:
            print("\n" + "=" * 60)
            print("SMOOTHING TEXT (Ollama)...")
            print("=" * 60)
            final_text = smooth_text_with_ollama(anonymized)
            print("Smoothing complete.")

        if output_path:
            output_path.write_text(final_text, encoding="utf-8")
            print(f"Output saved to: {output_path}")

            # Also save original anonymized version if smoothing was applied
            if smooth_enabled:
                raw_path = output_path.with_suffix('.raw.txt')
                raw_path.write_text(anonymized, encoding="utf-8")
                print(f"Raw anonymized text saved to: {raw_path}")
        else:
            print("\n" + "=" * 60)
            if smooth_enabled:
                print("SMOOTHED TEXT")
            else:
                print("ANONYMIZED TEXT")
            print("=" * 60)
            print(final_text)


if __name__ == "__main__":
    main()
