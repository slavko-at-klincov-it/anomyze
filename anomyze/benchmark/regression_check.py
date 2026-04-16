"""Benchmark regression gate.

Compares a fresh ``benchmark`` JSON report against a baseline. Exits
with a non-zero status when:

* overall F1 drops by more than ``--abs-drop`` (absolute, default 0.02),
* overall F1 drops by more than ``--rel-drop`` (relative, default 0.05),
* recall for any *critical* category (``SVN``, ``IBAN``, ``EMAIL`` by
  default) falls below ``--critical-min-recall`` (default 0.95).

Used by the ``benchmark.yml`` GitHub workflow as a release-gate.

CLI:

    python -m anomyze.benchmark.regression_check baseline.json current.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

DEFAULT_CRITICAL = ("SVN", "IBAN", "EMAIL")


def _load(path: Path) -> dict:
    data = json.loads(path.read_text())
    assert isinstance(data, dict)
    return data


def compare(
    baseline: dict,
    current: dict,
    *,
    abs_drop: float = 0.02,
    rel_drop: float = 0.05,
    critical: tuple[str, ...] = DEFAULT_CRITICAL,
    critical_min_recall: float = 0.95,
) -> tuple[bool, list[str]]:
    """Return ``(passed, reasons)`` for the comparison."""
    problems: list[str] = []

    base_f1 = baseline.get("overall", {}).get("f1", 0.0)
    cur_f1 = current.get("overall", {}).get("f1", 0.0)
    abs_delta = base_f1 - cur_f1
    rel_delta = abs_delta / base_f1 if base_f1 > 0 else 0.0

    if abs_delta > abs_drop:
        problems.append(
            f"overall F1 dropped by {abs_delta:.3f} (>{abs_drop}) "
            f"baseline={base_f1:.3f} current={cur_f1:.3f}"
        )
    if rel_delta > rel_drop:
        problems.append(
            f"overall F1 dropped by {rel_delta:.1%} (>{rel_drop:.0%})"
        )

    cur_cats = current.get("by_category", {})
    for cat in critical:
        recall = cur_cats.get(cat, {}).get("recall", 0.0)
        if recall < critical_min_recall:
            problems.append(
                f"critical category {cat!r} recall {recall:.3f} "
                f"< {critical_min_recall}"
            )

    return not problems, problems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("baseline", type=Path)
    parser.add_argument("current", type=Path)
    parser.add_argument("--abs-drop", type=float, default=0.02)
    parser.add_argument("--rel-drop", type=float, default=0.05)
    parser.add_argument("--critical-min-recall", type=float, default=0.95)
    parser.add_argument(
        "--critical",
        nargs="*",
        default=list(DEFAULT_CRITICAL),
        help="Categories whose recall must stay above the minimum",
    )
    args = parser.parse_args()

    baseline = _load(args.baseline)
    current = _load(args.current)

    ok, problems = compare(
        baseline,
        current,
        abs_drop=args.abs_drop,
        rel_drop=args.rel_drop,
        critical=tuple(args.critical),
        critical_min_recall=args.critical_min_recall,
    )

    if ok:
        print("OK: benchmark within tolerance")
        return 0

    print("REGRESSION DETECTED:")
    for problem in problems:
        print(f"  - {problem}")
    return 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
