"""
Report formatting for benchmark framework.

format_text produces a human-readable table, format_json a
machine-readable serialization of a BenchmarkReport.
"""

import json
from dataclasses import asdict

from anomyze.benchmark.metrics import BenchmarkReport, CategoryMetrics


def _row(label: str, m: CategoryMetrics, width: int) -> str:
    return (
        f"{label:<{width}} "
        f"{m.tp:>5} "
        f"{m.fp:>5} "
        f"{m.fn:>5} "
        f"{m.precision:>8.3f} "
        f"{m.recall:>8.3f} "
        f"{m.f1:>8.3f}"
    )


def _table(title: str, rows: dict[str, CategoryMetrics], width: int) -> list[str]:
    lines = [title, "-" * (width + 50)]
    header = (
        f"{'Bucket':<{width}} "
        f"{'TP':>5} {'FP':>5} {'FN':>5} "
        f"{'Precision':>8} {'Recall':>8} {'F1':>8}"
    )
    lines.append(header)
    lines.append("-" * (width + 50))
    for key in sorted(rows.keys()):
        lines.append(_row(key, rows[key], width))
    return lines


def format_text(report: BenchmarkReport) -> str:
    """Format a BenchmarkReport as a human-readable tabular string."""
    width = max(
        10,
        *(len(k) for k in report.by_category.keys()),
        *(len(k) for k in report.by_layer.keys()),
    )

    lines: list[str] = []
    lines.append(f"Benchmark-Report ({report.num_samples} Samples)")
    lines.append("=" * (width + 50))
    lines.append("")

    lines.append(_row("Overall".ljust(width), report.overall, width))
    lines.append(
        f"  TP={report.overall.tp}  FP={report.overall.fp}  FN={report.overall.fn}"
    )
    lines.append("")

    if report.by_category:
        lines.extend(_table("Per Category", report.by_category, width))
        lines.append("")

    if report.by_layer:
        lines.extend(_table("Per Layer (entity.source)", report.by_layer, width))
        lines.append("")

    return "\n".join(lines)


def format_json(report: BenchmarkReport) -> str:
    """Format a BenchmarkReport as a JSON string."""
    payload = {
        "num_samples": report.num_samples,
        "overall": asdict(report.overall),
        "by_category": {k: asdict(v) for k, v in report.by_category.items()},
        "by_layer": {k: asdict(v) for k, v in report.by_layer.items()},
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)
