"""Consolidate all simulation artifacts into metrics_raw.json.

Aggregates:
- pytest pass/fail counts from pytest_junit.xml
- coverage from coverage.json
- per-dataset benchmark P/R/F1 from benchmark_*.json
- channel comparison timings + entity counts
- leakage re-scan severity counts

Output: metrics_raw.json — single machine-readable summary.
"""
from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from pathlib import Path

OUT = Path(__file__).resolve().parent
RAW = OUT / "metrics_raw.json"


def load_pytest_junit(path: Path) -> dict:
    if not path.exists():
        return {"error": f"missing {path.name}"}
    try:
        tree = ET.parse(path)
        root = tree.getroot()
        ts = root.find("testsuite") if root.tag == "testsuites" else root
        if ts is None:
            return {"error": "no testsuite element"}
        return {
            "tests": int(ts.get("tests", 0)),
            "failures": int(ts.get("failures", 0)),
            "errors": int(ts.get("errors", 0)),
            "skipped": int(ts.get("skipped", 0)),
            "time_s": float(ts.get("time", 0)),
        }
    except Exception as exc:
        return {"error": str(exc)}


def load_coverage(path: Path) -> dict:
    if not path.exists():
        return {"error": f"missing {path.name}"}
    try:
        data = json.loads(path.read_text())
        tot = data.get("totals", {})
        return {
            "percent_covered": round(tot.get("percent_covered", 0), 2),
            "covered_lines": tot.get("covered_lines", 0),
            "num_statements": tot.get("num_statements", 0),
            "missing_lines": tot.get("missing_lines", 0),
        }
    except Exception as exc:
        return {"error": str(exc)}


def load_benchmark(path: Path) -> dict:
    if not path.exists():
        return {"error": f"missing {path.name}"}
    try:
        data = json.loads(path.read_text())
        return {
            "num_samples": data.get("num_samples"),
            "overall": data.get("overall", {}),
            "by_category": data.get("by_category", {}),
            "by_layer": data.get("by_layer", {}),
        }
    except Exception as exc:
        return {"error": str(exc)}


def load_leakage(path: Path) -> dict:
    if not path.exists():
        return {"error": f"missing {path.name}"}
    try:
        return json.loads(path.read_text())
    except Exception as exc:
        return {"error": str(exc)}


def load_channel_summary() -> list[dict]:
    cc = OUT / "channel_comparison"
    rows: list[dict] = []
    for p in sorted(cc.glob("*.json")):
        if p.name.startswith("_"):
            continue
        try:
            d = json.loads(p.read_text())
        except Exception:
            continue
        res = d.get("result", {})
        rows.append({
            "doc_id": d.get("doc_id"),
            "channel": d.get("channel"),
            "elapsed_s": d.get("elapsed_s"),
            "input_chars": d.get("input_chars"),
            "ground_truth_entities": d.get("ground_truth_entity_count"),
            "detected_entities": len(res.get("entities", []) or []),
            "mapping_size": len(res.get("mapping", {}) or {}),
            "redaction_protocol": res.get("redaction_protocol", []),
            "flagged_for_review": res.get("flagged_for_review", []),
            "audit_entries_count": len(res.get("audit_entries", []) or []),
        })
    return rows


def main() -> None:
    out = {
        "pytest": load_pytest_junit(OUT / "pytest_junit.xml"),
        "coverage": load_coverage(OUT / "coverage.json"),
        "benchmarks": {
            "synthetic_at": load_benchmark(OUT / "benchmark_synthetic_at.json"),
            "smoke_at": load_benchmark(OUT / "benchmark_smoke_at.json"),
            "realistic_at": load_benchmark(OUT / "benchmark_realistic_at.json"),
            "bka_ifg": load_benchmark(OUT / "benchmark_bka_ifg.json"),
        },
        "channel_comparison": load_channel_summary(),
        "leakage": load_leakage(OUT / "leakage_report.json"),
    }
    RAW.write_text(json.dumps(out, ensure_ascii=False, indent=2))
    print(f"wrote {RAW}")


if __name__ == "__main__":
    main()
