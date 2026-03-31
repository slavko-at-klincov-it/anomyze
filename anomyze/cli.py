#!/usr/bin/env python3
"""
Command-line interface for Anomyze.

Usage:
    anomyze <input.txt> [output.txt] [--smooth] [--channel govgpt|ifg|kapa]
    anomyze --interactive [--smooth] [--channel govgpt|ifg|kapa]
"""

import sys
import json
from pathlib import Path
from typing import Optional

from anomyze import __version__
from anomyze.pipeline.orchestrator import (
    PipelineOrchestrator,
    AnonymizeResult,
    anonymize,
    smooth_text_with_ollama,
    load_models,
    get_device,
)
from anomyze.config.settings import get_settings

# Try to import prompt_toolkit for better interactive input
try:
    from prompt_toolkit import prompt
    from prompt_toolkit.key_binding import KeyBindings
    from prompt_toolkit.keys import Keys
    PROMPT_TOOLKIT_AVAILABLE = True
except ImportError:
    PROMPT_TOOLKIT_AVAILABLE = False


VALID_CHANNELS = ("govgpt", "ifg", "kapa")


def print_banner():
    """Print Anomyze banner."""
    print("""
    \u2554\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2557
    \u2551                                                           \u2551
    \u2551     \u2588\u2588\u2588\u2588\u2588\u2557 \u2588\u2588\u2588\u2557   \u2588\u2588\u2557 \u2588\u2588\u2588\u2588\u2588\u2588\u2557 \u2588\u2588\u2588\u2557   \u2588\u2588\u2588\u2557\u2588\u2588\u2557   \u2588\u2588\u2557\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2557\u2551
    \u2551    \u2588\u2588\u2554\u2550\u2550\u2588\u2588\u2557\u2588\u2588\u2588\u2588\u2557  \u2588\u2588\u2551\u2588\u2588\u2554\u2550\u2550\u2550\u2588\u2588\u2557\u2588\u2588\u2588\u2588\u2557 \u2588\u2588\u2588\u2588\u2551\u255a\u2588\u2588\u2557 \u2588\u2588\u2554\u255d\u2588\u2588\u2554\u2550\u2550\u2550\u2550\u255d\u2551
    \u2551    \u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2551\u2588\u2588\u2554\u2588\u2588\u2557 \u2588\u2588\u2551\u2588\u2588\u2551   \u2588\u2588\u2551\u2588\u2588\u2554\u2588\u2588\u2588\u2588\u2554\u2588\u2588\u2551 \u255a\u2588\u2588\u2588\u2588\u2554\u255d \u2588\u2588\u2588\u2588\u2588\u2557  \u2551
    \u2551    \u2588\u2588\u2554\u2550\u2550\u2588\u2588\u2551\u2588\u2588\u2551\u255a\u2588\u2588\u2557\u2588\u2588\u2551\u2588\u2588\u2551   \u2588\u2588\u2551\u2588\u2588\u2551\u255a\u2588\u2588\u2554\u255d\u2588\u2588\u2551  \u255a\u2588\u2588\u2554\u255d  \u2588\u2588\u2554\u2550\u2550\u255d  \u2551
    \u2551    \u2588\u2588\u2551  \u2588\u2588\u2551\u2588\u2588\u2551 \u255a\u2588\u2588\u2588\u2588\u2551\u255a\u2588\u2588\u2588\u2588\u2588\u2588\u2554\u255d\u2588\u2588\u2551 \u255a\u2550\u255d \u2588\u2588\u2551   \u2588\u2588\u2551   \u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2557\u2551
    \u2551    \u255a\u2550\u255d  \u255a\u2550\u255d\u255a\u2550\u255d  \u255a\u2550\u2550\u2550\u255d \u255a\u2550\u2550\u2550\u2550\u2550\u255d \u255a\u2550\u255d     \u255a\u2550\u255d   \u255a\u2550\u255d   \u255a\u2550\u2550\u2550\u2550\u2550\u2550\u255d\u2551
    \u2551                                                           \u2551
    \u2551     Souver\u00e4ne KI-Anonymisierungsschicht f\u00fcr \u00d6sterreich    \u2551
    \u2551                    https://anomyze.it                     \u2551
    \u2551                                                           \u2551
    \u255a\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u255d
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


def print_result(result, verbose: bool = True):
    """Print anonymization result."""
    if verbose and hasattr(result, 'entities'):
        print(f"\nDetected {len(result.entities)} entities:")
        for e in result.entities:
            if hasattr(e, 'source'):
                source_info = e.source
                if source_info == 'perplexity':
                    source_info = f"perplexity ({getattr(e, 'context', '')})"
                print(f"  [{e.entity_group:12}] \"{e.word}\" "
                      f"(score: {e.score:.2f}, source: {source_info})")
            else:
                source_info = e.get('source', 'unknown')
                print(f"  [{e.get('entity_group', '?'):12}] \"{e.get('word', '?')}\" "
                      f"(score: {e.get('score', 0):.2f}, source: {source_info})")

    print("\n" + "=" * 60)
    print("MAPPING")
    print("=" * 60)
    mapping = getattr(result, 'mapping', {})
    if mapping:
        for placeholder, original in mapping.items():
            print(f"  {placeholder:30} -> {original}")
    else:
        print("  (no mapping / irreversible redaction)")

    # Show redaction protocol for IFG channel
    if hasattr(result, 'redaction_protocol') and result.redaction_protocol:
        print("\n" + "=" * 60)
        print("REDACTION PROTOCOL")
        print("=" * 60)
        for entry in result.redaction_protocol:
            print(f"  {entry.category:20} {entry.count}x "
                  f"(confidence: {entry.min_confidence:.2f}-{entry.max_confidence:.2f})")

    # Show flagged entities for KAPA channel
    if hasattr(result, 'flagged_for_review') and result.flagged_for_review:
        print("\n" + "=" * 60)
        print("FLAGGED FOR REVIEW")
        print("=" * 60)
        for flag in result.flagged_for_review:
            print(f"  {flag}")

    print("\n" + "=" * 60)
    print("ANONYMIZED TEXT")
    print("=" * 60)
    print(result.text)


def run_interactive(orchestrator: PipelineOrchestrator, channel: str, smooth_enabled: bool):
    """Run interactive mode."""
    print("=" * 60)
    print(f"Interactive Mode — Channel: {channel.upper()}")
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
            result = orchestrator.process(text, channel=channel)
            print_result(result)

            if smooth_enabled and hasattr(result, 'text'):
                settings = get_settings()
                print("\n" + "=" * 60)
                print("SMOOTHING TEXT (Ollama)...")
                print("=" * 60)
                smoothed = smooth_text_with_ollama(
                    result.text, settings.smooth_model, settings.smooth_timeout
                )
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
    orchestrator: PipelineOrchestrator,
    channel: str,
    smooth_enabled: bool,
):
    """Process a file."""
    if not input_path.exists():
        print(f"Error: File not found: {input_path}")
        sys.exit(1)

    mapping_path = output_path.with_suffix('.mapping.json') if output_path else Path("mapping.json")

    print(f"Reading: {input_path}")
    text = input_path.read_text(encoding="utf-8")
    print(f"Text length: {len(text):,} characters")
    print(f"Channel: {channel.upper()}")

    print("Processing...")
    result = orchestrator.process(text, channel=channel)

    mapping = getattr(result, 'mapping', {})
    unique_count = len(mapping) if mapping else 0
    print(f"\nFound {unique_count} unique entities")

    print("\n" + "=" * 60)
    print("MAPPING")
    print("=" * 60)
    if mapping:
        for placeholder, original in mapping.items():
            print(f"  {placeholder:30} -> {original}")
        mapping_path.write_text(
            json.dumps(mapping, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        print(f"\nMapping saved to: {mapping_path}")
    else:
        print("  (irreversible redaction — no mapping)")

    final_text = result.text
    if smooth_enabled:
        settings = get_settings()
        print("\n" + "=" * 60)
        print("SMOOTHING TEXT (Ollama)...")
        print("=" * 60)
        final_text = smooth_text_with_ollama(
            result.text, settings.smooth_model, settings.smooth_timeout
        )
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

    # Parse flags
    smooth_enabled = "--smooth" in args
    if smooth_enabled:
        args.remove("--smooth")

    channel = "govgpt"
    if "--channel" in args:
        idx = args.index("--channel")
        if idx + 1 < len(args):
            channel = args[idx + 1].lower()
            if channel not in VALID_CHANNELS:
                print(f"Error: Invalid channel '{channel}'. Must be one of: {', '.join(VALID_CHANNELS)}")
                sys.exit(1)
            args = args[:idx] + args[idx + 2:]
        else:
            print("Error: --channel requires a value (govgpt, ifg, kapa)")
            sys.exit(1)

    if len(args) < 1:
        print_banner()
        print(f"""
    Version {__version__}

    Usage:
      anomyze <input.txt> [output.txt] [--smooth] [--channel govgpt|ifg|kapa]
      anomyze --interactive [--smooth] [--channel govgpt|ifg|kapa]
      python -m anomyze <input.txt> [output.txt] [--smooth]

    Options:
      --smooth              Smooth text with local LLM (Ollama + Qwen)
      --channel <channel>   Output channel: govgpt (default), ifg, kapa

    Channels:
      govgpt    Reversible placeholders + mapping (for GovGPT/ELAK-KI)
      ifg       Irreversible redaction (for data.gv.at publication)
      kapa      Placeholders + audit trail (for parliamentary inquiries)

    Detection Pipeline:
      1. Regex Patterns   → Austrian-specific formats (SVNr, IBAN, KFZ, ...)
      2. NER Models       → Names, organizations, locations
      3. Anomaly Detection→ Unknown entities via perplexity analysis
        """)
        sys.exit(1)

    print_banner()

    if smooth_enabled:
        print("    Smooth Mode: ON (Ollama + Qwen)\n")
    print(f"    Channel: {channel.upper()}\n")

    # Initialize orchestrator
    orchestrator = PipelineOrchestrator()
    orchestrator.load_models(verbose=True)

    if args[0] == "--interactive":
        run_interactive(orchestrator, channel, smooth_enabled)
    else:
        input_path = Path(args[0])
        output_path = Path(args[1]) if len(args) > 1 else None
        run_file(input_path, output_path, orchestrator, channel, smooth_enabled)


if __name__ == "__main__":
    main()
