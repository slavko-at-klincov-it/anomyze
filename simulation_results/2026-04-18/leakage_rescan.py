"""Phase F — leakage re-scan.

For every anonymized text produced in Phase E, re-run RegexLayer
against it. Filter out expected placeholder patterns (GovGPT/KAPA
'[X_N]', IFG '[GESCHWÄRZT:...]', KAPA '[PRÜFEN:...]').

Any remaining regex hit = real leakage.

Outputs leakage_report.json:
{
  "<doc_id>__<channel>": {
    "channel": "ifg",
    "leaks": [{"type": "EMAIL", "start": 123, "end": 147, "snippet": "...<redacted>..."}],
    "severity": "CRITICAL" | "NONE"
  }
}

Snippets in the report show ONLY the category and a character window
around the position — never the leaked value itself (honesty rule 6).
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from anomyze.config.settings import Settings
from anomyze.pipeline.regex_layer import RegexLayer

OUT_DIR = Path(__file__).resolve().parent
CHANNEL_DIR = OUT_DIR / "channel_comparison"
REPORT_PATH = OUT_DIR / "leakage_report.json"

PLACEHOLDER_PATTERNS = [
    re.compile(r"\[GESCHWÄRZT:[A-ZÄÖÜ_]+\]"),
    re.compile(r"\[PRÜFEN:[A-ZÄÖÜ_]+_\d+\]"),
    re.compile(r"\[[A-ZÄÖÜ_]+_\d+\]"),
]

# A leaked direct identifier is CRITICAL for IFG (public release),
# HIGH for GovGPT/KAPA (reversible but still a bug).
CRITICAL_TYPES = {
    "SVN", "IBAN", "BIC", "UID", "REISEPASS", "PERSONALAUSWEIS",
    "FUEHRERSCHEIN", "KFZ", "ZMR", "FIRMENBUCH",
    "HEALTH_DIAGNOSIS", "HEALTH_MEDICATION", "RELIGION",
    "ETHNICITY", "POLITICAL", "UNION", "SEXUAL_ORIENTATION", "BIOMETRIC",
}


def is_inside_placeholder(text: str, start: int, end: int) -> bool:
    for pat in PLACEHOLDER_PATTERNS:
        for m in pat.finditer(text):
            if m.start() <= start and end <= m.end():
                return True
    return False


def classify_severity(channel: str, leak_type: str) -> str:
    if channel == "ifg" and leak_type in CRITICAL_TYPES:
        return "CRITICAL"
    if channel == "ifg":
        return "HIGH"
    if leak_type in CRITICAL_TYPES:
        return "HIGH"
    return "MEDIUM"


def safe_snippet(text: str, start: int, end: int, window: int = 20) -> str:
    left = max(0, start - window)
    right = min(len(text), end + window)
    before = text[left:start]
    after = text[end:right]
    return f"...{before}<LEAK[{end-start}ch]>{after}..."


def load_gt_lookup() -> dict[str, list[dict]]:
    """Map doc_id -> list of {text, type} from the BKA dataset."""
    ds_path = Path(__file__).resolve().parent.parent.parent / "benchmarks" / "datasets" / "bka_ifg_simulation.json"
    data = json.loads(ds_path.read_text())
    lookup: dict[str, list[dict]] = {}
    for doc in data:
        items = []
        for ent in doc["entities"]:
            value = doc["text"][ent["start"]:ent["end"]]
            items.append({"text": value, "type": ent["type"]})
        lookup[doc["id"]] = items
    return lookup


def gt_verbatim_check(anon_text: str, gt_items: list[dict], channel: str) -> list[dict]:
    """For each ground-truth value, check if it still appears in the anonymized text."""
    leaks = []
    for item in gt_items:
        # Skip very short values (1-2 chars) to avoid false positives like "W" or "AT"
        if len(item["text"]) < 4:
            continue
        if item["text"] in anon_text:
            severity = classify_severity(channel, item["type"])
            leaks.append({
                "type": item["type"],
                "verbatim": True,
                "severity": severity,
                "snippet": f"<GT value of length {len(item['text'])} present in output>",
                "value_length": len(item["text"]),
            })
    return leaks


def main() -> None:
    settings = Settings.from_env()
    rl = RegexLayer()
    gt_lookup = load_gt_lookup()
    report: dict[str, dict] = {}
    overall = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "NONE": 0}

    for path in sorted(CHANNEL_DIR.glob("*.json")):
        if path.name.startswith("_"):
            continue
        data = json.loads(path.read_text())
        channel = data["channel"]
        doc_id = data["doc_id"]
        anon_text = data["result"]["text"]

        entities = rl.process(anon_text)
        regex_leaks: list[dict] = []
        for ent in entities:
            if is_inside_placeholder(anon_text, ent.start, ent.end):
                continue
            regex_leaks.append({
                "type": ent.entity_group,
                "start": ent.start,
                "end": ent.end,
                "score": round(ent.score, 3),
                "severity": classify_severity(channel, ent.entity_group),
                "snippet": safe_snippet(anon_text, ent.start, ent.end),
                "detector": "regex",
            })

        gt_items = gt_lookup.get(doc_id, [])
        gt_leaks = gt_verbatim_check(anon_text, gt_items, channel)
        for leak in gt_leaks:
            leak["detector"] = "ground-truth-verbatim"

        leaks = regex_leaks + gt_leaks

        if leaks:
            max_sev = max(leaks, key=lambda x: ["NONE", "MEDIUM", "HIGH", "CRITICAL"].index(x["severity"]))["severity"]
        else:
            max_sev = "NONE"
        overall[max_sev] = overall.get(max_sev, 0) + 1

        report[path.stem] = {
            "doc_id": doc_id,
            "channel": channel,
            "regex_leak_count": len(regex_leaks),
            "gt_verbatim_leak_count": len(gt_leaks),
            "max_severity": max_sev,
            "leaks": leaks,
        }

    report["_overall"] = overall
    REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2))
    print(f"wrote {REPORT_PATH}")
    print(f"overall: {overall}")


if __name__ == "__main__":
    main()
