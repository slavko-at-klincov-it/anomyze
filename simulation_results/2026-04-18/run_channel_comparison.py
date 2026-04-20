"""Channel comparison driver: run 5 BKA docs through IFG, KAPA, GovGPT.

Loads the PipelineOrchestrator ONCE and reuses it across all 15
(doc, channel) pairs to avoid repeated 8 GB model loads.

Outputs:
  channel_comparison/<doc_id>__<channel>.json   (15 files)
  channel_comparison/_summary.md                (overview table)
  channel_comparison/audit.log                  (KAPA audit trail)
"""
from __future__ import annotations

import json
import time
from dataclasses import asdict, is_dataclass
from pathlib import Path

from anomyze.benchmark.loader import load_dataset
from anomyze.config.settings import Settings
from anomyze.pipeline.orchestrator import PipelineOrchestrator

OUT_DIR = Path(__file__).resolve().parent / "channel_comparison"
DATASET = Path(__file__).resolve().parent.parent.parent / "benchmarks" / "datasets" / "bka_ifg_simulation.json"


class _JSONFallback(json.JSONEncoder):
    def default(self, o):
        if hasattr(o, "item"):
            try:
                return o.item()
            except Exception:
                pass
        if hasattr(o, "tolist"):
            return o.tolist()
        if is_dataclass(o) and not isinstance(o, type):
            return asdict(o)
        return repr(o)


def serialize(obj):
    if is_dataclass(obj) and not isinstance(obj, type):
        return asdict(obj)
    return obj


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    settings = Settings.from_env()
    orch = PipelineOrchestrator(settings)
    print("Loading models...")
    t0 = time.perf_counter()
    orch.load_models(verbose=True)
    print(f"Models loaded in {time.perf_counter()-t0:.1f}s")

    samples = load_dataset(DATASET)
    print(f"Loaded {len(samples)} BKA documents")

    summary_rows: list[dict] = []
    audit_lines: list[str] = []

    for sample in samples:
        for channel in ("govgpt", "ifg", "kapa"):
            t0 = time.perf_counter()
            result = orch.process(sample.text, channel=channel)
            elapsed = time.perf_counter() - t0

            payload = {
                "doc_id": sample.id,
                "channel": channel,
                "elapsed_s": round(elapsed, 3),
                "input_chars": len(sample.text),
                "ground_truth_entity_count": len(sample.entities),
                "result": serialize(result),
            }
            out_path = OUT_DIR / f"{sample.id}__{channel}.json"
            out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, cls=_JSONFallback))

            row = {
                "doc_id": sample.id,
                "channel": channel,
                "elapsed_s": elapsed,
                "detected_entities": len(getattr(result, "entities", []) or []),
                "mapping_size": len(getattr(result, "mapping", {}) or {}),
                "redaction_categories": len(getattr(result, "redaction_protocol", []) or []),
                "flagged_for_review": len(getattr(result, "flagged_for_review", []) or []),
                "audit_entries": len(getattr(result, "audit_entries", []) or []),
            }
            summary_rows.append(row)

            if channel == "kapa":
                for ae in getattr(result, "audit_entries", []) or []:
                    audit_lines.append(json.dumps({
                        "doc_id": sample.id,
                        **{k: v for k, v in asdict(ae).items() if k != "entity_word"},
                    }, ensure_ascii=False, cls=_JSONFallback))

            print(f"  {sample.id}/{channel}: {row['detected_entities']} entities, {elapsed:.2f}s")

    # Summary markdown
    md_lines = ["# Channel Comparison Summary\n",
                "| Doc ID | Channel | Detected | Mapping | RedCats | Flagged | AuditEntries | Elapsed (s) |",
                "|---|---|---:|---:|---:|---:|---:|---:|"]
    for r in summary_rows:
        md_lines.append(
            f"| {r['doc_id']} | {r['channel']} | {r['detected_entities']} | "
            f"{r['mapping_size']} | {r['redaction_categories']} | "
            f"{r['flagged_for_review']} | {r['audit_entries']} | {r['elapsed_s']:.2f} |"
        )
    (OUT_DIR / "_summary.md").write_text("\n".join(md_lines))

    (OUT_DIR / "audit.log").write_text("\n".join(audit_lines))

    print(f"\nWrote {len(summary_rows)} channel results to {OUT_DIR}")


if __name__ == "__main__":
    main()
