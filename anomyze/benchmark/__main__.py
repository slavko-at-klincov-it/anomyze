"""Command-line interface for the benchmark framework.

Usage:
    python -m anomyze.benchmark <dataset.json> [--json] [--device cpu]

By default runs a fast configuration (regex + NER + Presidio-compat,
without MLM anomaly detection and without GLiNER). Flags enable the
heavier layers.
"""

import argparse
import sys
from pathlib import Path

from anomyze.benchmark.evaluator import Evaluator
from anomyze.benchmark.loader import DatasetLoadError, load_dataset
from anomyze.benchmark.reporter import format_json, format_text
from anomyze.config.settings import Settings, configure
from anomyze.pipeline.orchestrator import PipelineOrchestrator


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m anomyze.benchmark",
        description="Run the Anomyze detection pipeline on a ground-truth dataset "
        "and report precision, recall, F1.",
    )
    parser.add_argument("dataset", type=Path, help="Path to the dataset JSON file.")
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit report as JSON instead of a human-readable table.",
    )
    parser.add_argument(
        "--device",
        choices=("cpu", "mps", "cuda"),
        default=None,
        help="Force a specific compute device (default: auto).",
    )
    parser.add_argument(
        "--iou-threshold",
        type=float,
        default=0.5,
        help="Minimum IoU for a match (default: 0.5).",
    )
    parser.add_argument(
        "--with-mlm",
        action="store_true",
        help="Enable context/anomaly layer (slower).",
    )
    parser.add_argument(
        "--with-gliner",
        action="store_true",
        help="Enable GLiNER zero-shot layer (slower).",
    )
    parser.add_argument(
        "--no-presidio",
        action="store_true",
        help="Disable the Presidio-compatible recognizer layer.",
    )
    parser.add_argument(
        "--no-regex",
        action="store_true",
        help="Disable the regex layer.",
    )
    parser.add_argument(
        "--no-quality-check",
        action="store_true",
        help="Disable the post-anonymization quality check (not used during detect).",
    )
    return parser


def _build_settings(args: argparse.Namespace) -> Settings:
    settings = Settings.from_env()
    if args.device:
        settings.device = args.device
    settings.use_anomaly_detection = args.with_mlm
    settings.use_gliner = args.with_gliner
    settings.use_presidio_compat = not args.no_presidio
    settings.use_regex_fallback = not args.no_regex
    settings.run_quality_check = not args.no_quality_check
    return settings


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        samples = load_dataset(args.dataset)
    except FileNotFoundError:
        print(f"Dataset not found: {args.dataset}", file=sys.stderr)
        return 2
    except DatasetLoadError as err:
        print(f"Invalid dataset: {err}", file=sys.stderr)
        return 2

    if not samples:
        print("Dataset is empty.", file=sys.stderr)
        return 1

    settings = _build_settings(args)
    configure(settings)

    orchestrator = PipelineOrchestrator(settings)
    orchestrator.load_models(verbose=not args.json)

    report = Evaluator(orchestrator, samples, args.iou_threshold).run()

    output = format_json(report) if args.json else format_text(report)
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
