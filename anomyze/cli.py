#!/usr/bin/env python3
"""
Command-line interface for Anomyze.

Usage:
    anomyze <input.txt> [output.txt] [--smooth]
    anomyze --interactive [--smooth]
"""

import sys
import json
from pathlib import Path
from typing import Optional

from anomyze import __version__
from anomyze.core import anonymize, smooth_text_with_ollama, AnonymizeResult
from anomyze.models import load_models, get_device
from anomyze.config import get_settings

# Try to import prompt_toolkit for better interactive input
try:
    from prompt_toolkit import prompt
    from prompt_toolkit.key_binding import KeyBindings
    from prompt_toolkit.keys import Keys
    PROMPT_TOOLKIT_AVAILABLE = True
except ImportError:
    PROMPT_TOOLKIT_AVAILABLE = False


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


def get_multiline_input() -> Optional[str]:
    """Get multiline input using prompt_toolkit or fallback."""
    if PROMPT_TOOLKIT_AVAILABLE:
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


def print_result(result: AnonymizeResult, verbose: bool = True):
    """Print anonymization result."""
    if verbose:
        print(f"\nDetected {result.entity_count} entities:")
        for e in result.entities:
            source_info = e['source']
            if source_info == 'perplexity':
                source_info = f"perplexity ({e.get('context', '')})"
            print(f"  [{e['entity_group']:12}] \"{e['word']}\" "
                  f"(score: {e['score']:.2f}, source: {source_info})")

    print("\n" + "=" * 60)
    print("MAPPING")
    print("=" * 60)
    if result.mapping:
        for placeholder, original in result.mapping.items():
            print(f"  {placeholder:30} -> {original}")
    else:
        print("  (no PII detected)")

    print("\n" + "=" * 60)
    print("ANONYMIZED TEXT")
    print("=" * 60)
    print(result.text)


def run_interactive(pii_pipeline, org_pipeline, mlm_pipeline, smooth_enabled: bool):
    """Run interactive mode."""
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
            result = anonymize(text, pii_pipeline, org_pipeline, mlm_pipeline)
            print_result(result)

            if smooth_enabled:
                print("\n" + "=" * 60)
                print("SMOOTHING TEXT (Ollama)...")
                print("=" * 60)
                smoothed = smooth_text_with_ollama(result.text)
                print("\n" + "=" * 60)
                print("SMOOTHED TEXT")
                print("=" * 60)
                print(smoothed)

        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            sys.exit(0)


def run_file(
    input_path: Path,
    output_path: Optional[Path],
    pii_pipeline,
    org_pipeline,
    mlm_pipeline,
    smooth_enabled: bool
):
    """Process a file."""
    if not input_path.exists():
        print(f"Error: File not found: {input_path}")
        sys.exit(1)

    mapping_path = output_path.with_suffix('.mapping.json') if output_path else Path("mapping.json")

    print(f"Reading: {input_path}")
    text = input_path.read_text(encoding="utf-8")
    print(f"Text length: {len(text):,} characters")

    print("Processing...")
    result = anonymize(text, pii_pipeline, org_pipeline, mlm_pipeline)

    print(f"\nFound {result.unique_entity_count} unique entities")

    print("\n" + "=" * 60)
    print("MAPPING")
    print("=" * 60)
    for placeholder, original in result.mapping.items():
        print(f"  {placeholder:30} -> {original}")

    mapping_path.write_text(
        json.dumps(result.mapping, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )
    print(f"\nMapping saved to: {mapping_path}")

    final_text = result.text
    if smooth_enabled:
        print("\n" + "=" * 60)
        print("SMOOTHING TEXT (Ollama)...")
        print("=" * 60)
        final_text = smooth_text_with_ollama(result.text)
        print("Smoothing complete.")

    if output_path:
        output_path.write_text(final_text, encoding="utf-8")
        print(f"Output saved to: {output_path}")

        if smooth_enabled:
            raw_path = output_path.with_suffix('.raw.txt')
            raw_path.write_text(result.text, encoding="utf-8")
            print(f"Raw anonymized text saved to: {raw_path}")
    else:
        print("\n" + "=" * 60)
        if smooth_enabled:
            print("SMOOTHED TEXT")
        else:
            print("ANONYMIZED TEXT")
        print("=" * 60)
        print(final_text)


def main():
    """Main entry point for CLI."""
    args = sys.argv[1:]
    smooth_enabled = "--smooth" in args
    if smooth_enabled:
        args.remove("--smooth")

    if len(args) < 1:
        print_banner()
        print(f"""
    Version {__version__}

    Usage:
      anomyze <input.txt> [output.txt] [--smooth]
      anomyze --interactive [--smooth]
      python -m anomyze <input.txt> [output.txt] [--smooth]

    Options:
      --smooth    Smooth text with local LLM (Ollama + Qwen)

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
        run_interactive(pii_pipeline, org_pipeline, mlm_pipeline, smooth_enabled)
    else:
        input_path = Path(args[0])
        output_path = Path(args[1]) if len(args) > 1 else None
        run_file(input_path, output_path, pii_pipeline, org_pipeline, mlm_pipeline, smooth_enabled)


if __name__ == "__main__":
    main()
