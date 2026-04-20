# Anomyze BKA/IFG Simulation — Verdict Report

- **Date:** 2026-04-18
- **Commit:** `4cf8bdd29096d625ba0d23bc7055ee6d462ca3fc`
- **Runner:** Opus 4.7 (1M context), multi-agent planning (Explore ×3, Plan ×2), with autonomous execution
- **Hardware:** Mac mini M4 16 GB — MPS backend
- **Anomyze version:** 2.0.0

---

## 1. Executive Summary

**Verdict: UNFIT for unattended IFG use.**

Anomyze reliably redacts all regex-detectable direct identifiers (SVNR, IBAN, KFZ, EMAIL, UID, Firmenbuchnummer, Aktenzahl, ICD-10) in the simulated Austrian Bundeskanzleramt corpus. However, one DSGVO Art. 9 "besondere Kategorie" value — the religious affiliation `römisch-katholisch` — passed unredacted through the IFG (public-release) channel in doc-004, because the NER layers did not classify the token as `RELIGION`. Per the pre-registered honesty rule "UNFIT on any single Critical-tier finding," the verdict is UNFIT.

The system is suitable as a first-line filter in a **human-in-the-loop workflow** (KAPA-style), where a legal reviewer inspects every output before release. It is **not suitable** as an unattended redactor for IFG public release in its current configuration. Two fixable issues would raise the verdict to FIT-WITH-CAVEATS: (a) add a curated religion/ethnicity/political lexicon, and (b) tighten the BIC recognizer, which produced 5 spurious BIC redactions in a single 533-character document.

---

## 2. Scope and Methodology

**Corpus simulated:** 5 synthetic BKA bureaucratic documents plus 3 pre-existing benchmark datasets (82 samples total). The 5 BKA documents (`benchmarks/datasets/bka_ifg_simulation.json`) were purpose-built for this simulation, each stressing a distinct surface (Bescheid, Ministerratsvortrag, Bürgeranfrage-Antwort, interministerielle Mitteilung, parlamentarische Anfrage); all PII is synthetic, all SVNR/IBAN/UID values are checksum-valid via `stdnum`.

**Disclaimer — indicative, not exhaustive.** A 5-document sample cannot validate "every bureaucratic document." Coverage of the real BKA document population is unknown; no claim of completeness is made or supported. With n ≤ 50 per dataset, 95% confidence intervals on P/R/F1 are wide (roughly ±10pp or more) and are not reported per-figure.

**Phases run:**
- A. Environment pre-flight (venv, imports, model pre-fetch)
- B. `pytest tests/` (493 tests, serial, `-p no:xdist`)
- C. Benchmark harness on `synthetic_at` / `smoke_at` / `realistic_at` (full pipeline: regex + NER + GLiNER + Presidio-compat + MLM anomaly + context)
- D. Benchmark harness on the 5 BKA documents
- E. Channel comparison driver: 5 docs × 3 channels = 15 outputs, one `PipelineOrchestrator` instance reused
- F. Leakage re-scan — regex layer on anonymized outputs + verbatim presence check of every ground-truth value

**Settings used:** all defaults (Settings.from_env()), MPS backend, all layers enabled. Models unpinned (latest HF revisions); see Reproducibility §11.

---

## 3. Test Suite Results

| Metric | Value |
|---|---|
| Tests | 493 |
| Passed | 492 |
| Failed | 1 |
| Errors | 0 |
| Wall time | 382 s |
| Coverage | 76.9% (1999/2599 lines) |

The single failure is `tests/test_api_metrics.py::TestChannelCounter::test_two_requests_two_increments` — a Prometheus-counter state issue, flagged as environmental (counters accumulate across test cases); not a functional defect. No other regression observed.

---

## 4. Detection Accuracy by Entity Type

### 4.1 Aggregate per dataset (IoU ≥ 0.5, type-exact)

| Dataset | n | TP | FP | FN | Precision | Recall | F1 |
|---|---:|---:|---:|---:|---:|---:|---:|
| synthetic_at | 25 | 25 | 23 | 7 | 0.521 | 0.781 | 0.625 |
| smoke_at | 50 | 171 | 101 | 54 | 0.629 | 0.760 | 0.688 |
| realistic_at | 7 | 37 | 33 | 10 | 0.529 | 0.787 | 0.632 |
| bka_ifg_simulation | 5 | 23 | 22 | 12 | 0.511 | 0.657 | 0.575 |

Recall dominates precision across all datasets — the system over-detects rather than under-detects, which is the correct trade-off for a privacy filter. A large portion of the FP count is **label-alias mismatches**: the pipeline emits `TELEPHONENUM`, `DATEOFBIRTH`, `DRIVERLICENSENUM`, `SURNAME` while the gold datasets use `TELEFON`, `GEBURTSDATUM`, `FUEHRERSCHEIN`, `PER`. These are benchmark-schema disagreements, not real detection failures — after collapsing aliases, effective precision is materially higher. This was not formally re-computed.

### 4.2 BKA simulation per-category (n=5)

| Category | P | R | F1 | TP | FP | FN | Note |
|---|---:|---:|---:|---:|---:|---:|---|
| AKTENZAHL | 1.00 | 1.00 | 1.00 | 3 | 0 | 0 | MUST — perfect |
| EMAIL | 1.00 | 1.00 | 1.00 | 2 | 0 | 0 | MUST — perfect |
| IBAN | 1.00 | 1.00 | 1.00 | 2 | 0 | 0 | MUST — perfect |
| UID | 1.00 | 1.00 | 1.00 | 1 | 0 | 0 | MUST — perfect |
| KFZ | 1.00 | 1.00 | 1.00 | 1 | 0 | 0 | MUST — perfect |
| FIRMENBUCH | 1.00 | 1.00 | 1.00 | 1 | 0 | 0 | MUST — perfect |
| HEALTH_DIAGNOSIS | 1.00 | 1.00 | 1.00 | 1 | 0 | 0 | Art. 9 — caught |
| SVN | 0.50 | 1.00 | 0.67 | 1 | 1 | 0 | recall perfect; one FP |
| PER | 1.00 | 0.88 | 0.93 | 7 | 0 | 1 | MUST (≥0.90) — below threshold |
| ORG | 0.60 | 0.38 | 0.46 | 3 | 2 | 5 | whitelisted authority names suppressed |
| BIC | 0.10 | 1.00 | 0.18 | 1 | 9 | 0 | 9 FP — known issue, confirmed |
| ADRESSE | 0.00 | 0.00 | 0.00 | 0 | 0 | 2 | both addresses missed entirely |
| FUEHRERSCHEIN | 0.00 | 0.00 | 0.00 | 0 | 0 | 1 | context-gated miss (as predicted) |
| ZMR | 0.00 | 0.00 | 0.00 | 0 | 0 | 1 | context-gated miss (as predicted) |
| TELEFON | 0.00 | 0.00 | 0.00 | 0 | 0 | 1 | label alias: system emits `TELEPHONENUM` |
| RELIGION | 0.00 | 0.00 | 0.00 | 0 | 0 | 1 | **Art. 9 miss — CRITICAL** |

---

## 5. Channel-Specific Assessment

### 5.1 IFG channel (irreversible public release)

| Criterion | Result |
|---|---|
| No mapping stored | PASS (0 mappings in every IFG output) |
| Redaction protocol produced | PASS (5-9 categories per doc) |
| Category-only placeholders `[GESCHWÄRZT:TYPE]` | PASS |
| Art. 9 collapses to `[GESCHWÄRZT:BESONDERE_KATEGORIE]` | PARTIAL — collapses the detected Art. 9 values (HEALTH_DIAGNOSIS in doc-004 was mapped correctly), but RELIGION was never detected so never collapsed |
| Zero Art. 9 leakage in output text | **FAIL** — `römisch-katholisch` present verbatim in doc-004 IFG output |

### 5.2 KAPA channel (parliamentary, audit + review)

| Criterion | Result |
|---|---|
| Mapping present for every anonymized entity | PASS |
| Audit entries count = detected entities | PASS (11/11, 9/9, 9/9, 10/10, 6/6) |
| Art. 9 entities flagged for human review (`always_review_art9=True`) | PARTIAL — HEALTH_DIAGNOSIS flagged in doc-004; RELIGION not detected so not flagged |
| Flags follow confidence threshold (<0.85) | PASS (2/9, 2/9, 4/10, 1/6 flags) |

### 5.3 GovGPT channel (reversible, internal)

| Criterion | Result |
|---|---|
| Bijective mapping (each placeholder → unique original) | PASS (5/5 docs) |
| Deterministic placeholder numbering | PASS |
| No human-review flags | PASS (0 across all docs) |

---

## 6. IFG-Specific Risks — Leakage Re-scan

Two independent checks were run on every anonymized output:

1. **Regex re-scan**: run `RegexLayer` on the anonymized text; any hit not contained within a placeholder token is a format-level leak.
2. **Ground-truth verbatim**: for every original PII value from the gold annotations, check whether it still appears verbatim (substring) in the anonymized output.

| Channel | Docs | Regex leaks | GT-verbatim leaks | Max severity |
|---|---:|---:|---:|---|
| GovGPT | 5 | 0 | 4 (3 ORG × authorities, 1 RELIGION) | MEDIUM |
| IFG | 5 | 0 | 6 (5 ORG × authorities, 1 RELIGION) | **CRITICAL** |
| KAPA | 5 | 0 | 4 (3 ORG × authorities, 1 RELIGION) | HIGH |

The regex re-scan is clean — every direct-identifier format that regex can match is absent from every output. The remaining leaks come from ground-truth values that are NER-only categories (names, organizations, religion). Of those:

- **Austrian authority names** — `Bundeskanzleramt`, `Bundesministerium für Inneres`, `Bundesministerium für Finanzen`, `Bundeskanzler` — are **intentionally whitelisted** by `anomyze/patterns/whitelist.py`. Public-authority identity is not private information and appears unredacted by design. Whether this is appropriate for IFG output is a policy decision, not a pipeline defect.
- **The `römisch-katholisch` leak in doc-004** is a **genuine Art. 9 DSGVO violation**. The word was not matched by any regex, not recognized by the PII NER model at ≥0.5 confidence, not recognized by GLiNER, and not on any Austrian-specific recognizer. It survives into IFG output verbatim.

### Doc-004 IFG output fragment (raw)

> `[GESCHWÄRZT:BIC] (mittelgradige depressive Episode) wird die vorzeitige Ruhestandsversetzung beantragt. Die Glaubensgemeinschaft des Beamten - [GESCHWÄRZT:BIC]: römisch-katholisch - ist für die seelsorgerische Betreuung im Krankenstand [GESCHWÄRZT:BIC].`

Two observations from this fragment: (a) the ICD-10 code `F32.1` was redacted, but as `[GESCHWÄRZT:BIC]` (wrong category — should be `BESONDERE_KATEGORIE`); (b) the label word "Religion" was also redacted as `[GESCHWÄRZT:BIC]`, while the actual religious-affiliation value survived.

---

## 7. Failure Case Analysis

No plain-text PII values are reproduced below. Positions are relative to the sample `text` field.

1. **doc-004, offset ≈380–398, category RELIGION (length 18 chars).** Not detected by any layer. Remains verbatim in all three channel outputs. Critical in IFG channel.
2. **doc-004, multiple offsets, spurious BIC detections (5×).** BIC recognizer's broad 8-char alphanumeric pattern triggers on short German words and an ICD-10 code, producing `[GESCHWÄRZT:BIC]` replacements that destroy surrounding context. Not a privacy leak but reduces document utility and misclassifies one Art. 9 health entity.
3. **doc-002, doc-003, category ADRESSE, 2 occurrences total.** Both Austrian addresses missed in the BKA benchmark (`Donaufelder Straße 247, 1220 Wien` and `Mariahilfer Straße 318/14, 1150 Wien` were in ground truth). Per the channel outputs the individual components (PLZ, Strasse) were partially caught, but the IoU≥0.5 match against the full address span failed. Under-redaction risk: low street numbers may still identify residents.
4. **doc-003, category FUEHRERSCHEIN, 1 occurrence.** Context-gated recognizer did not trigger despite the keyword "Führerschein-Nummer" immediately preceding. Re-identification risk: medium (driving-licence number is a direct identifier).
5. **doc-002, category ZMR, 1 occurrence.** Context-gated recognizer did not trigger despite the keyword "ZMR-Zahl" preceding. Re-identification risk: high (ZMR ties to the Central Population Register).

---

## 8. Known Architectural Gaps (from pre-simulation audit, carried forward)

These gaps were identified before running the simulation and are restated here verbatim — absence of evidence in the 5-doc sample is not evidence of absence:

- Person-name recognizer uses a dictionary of ~70 Austrian names plus NER fallback; rare or non-Austrian names rely entirely on NER.
- Context-gated recognizers (ICD-10, Führerschein, ZMR, Personalausweis) silently drop isolated occurrences when keywords are absent or far away. **Confirmed triggered** for Führerschein and ZMR in §7.
- Firmenbuchnummer lacks checksum validation; format-match only.
- BIC recognizer is false-positive prone. **Confirmed: 9 BIC FPs in the 5-doc corpus.**
- Organization detection is unoptimized for Austrian ministry/agency names; whitelist suppresses authority names by design (see §6).
- No hardcoded religion / ethnicity / political lexicon — reliance on NER. **Confirmed triggered** for RELIGION in §7.
- Model revisions are unpinned by default (see `ModelManager._hf_kwargs` warning) — detection behaviour will drift as HuggingFace releases new snapshots.

---

## 9. Recommendations & Required Follow-ups

1. **Blocker for IFG:** add a curated Austrian religion / ethnicity / political-party / union lexicon, or fine-tune the PII NER model on Art. 9 categories, so that values like `römisch-katholisch`, `evangelisch A.B.`, `ÖGB`, `SPÖ-Mitglied` are always redacted. Until this lands, IFG output must not leave the system without human review.
2. **High:** constrain the BIC recognizer — require a checksum-valid `stdnum.bic.is_valid` and nearby banking context, or raise the base score to 0.9 so only certain hits fire.
3. **High:** broaden context-gated recognizers (Führerschein, ZMR) — at minimum, treat presence of the category keyword anywhere in the same sentence as sufficient context; today the keyword must be immediately adjacent.
4. **Medium:** improve the ADRESSE regex to handle the format `Strasse Hausnr/Stiege, PLZ Ort` (slash-separated door numbers). Both Austrian addresses with this structure were missed.
5. **Medium:** align benchmark-schema labels to the runtime emit set, or add an explicit alias table, so false-positive counts are not inflated by `TELEPHONENUM` vs `TELEFON` etc.
6. **Medium:** revisit the whitelist for IFG channel. Even if `Bundeskanzleramt` is a public authority, leaking the unredacted name in a file marked for public release is a policy decision that should be explicit.
7. **Low:** pin model revisions (`ANOMYZE_*_MODEL_REVISION`) for reproducibility.

---

## 10. Verdict Matrix

| ID | Tier | Criterion | Result | Notes |
|---|---|---|---|---|
| M1 | MUST | Zero direct-identifier leakage in IFG | **PASS** | Regex re-scan: 0 hits across all 15 outputs |
| M2 | MUST | Zero Art. 9 leakage in IFG | **FAIL** | `römisch-katholisch` leaked in doc-004 |
| M3 | MUST | GovGPT mapping bijective | **PASS** | 5/5 docs |
| M4 | MUST | KAPA Art. 9 flagged when `always_review_art9=True` | PARTIAL | Detected Art. 9 flagged; undetected Art. 9 (RELIGION) cannot be flagged |
| M5 | MUST | Person-name recall ≥ 0.90 (BKA sample) | **FAIL** | 0.88, n=8 (1 miss) |
| S1 | SHOULD | realistic_at F1 ≥ 0.85 | FAIL | F1=0.63 |
| S2 | SHOULD | Quasi-ID F1 ≥ 0.75 | UNTESTED | No quasi-ID gold labels in the 5-doc sample |
| S3 | SHOULD | Throughput ≥ 1 page/sec | PASS | Mean 0.35 s per 500-char doc on MPS |
| S4 | SHOULD | KAPA audit log lossless | PASS | audit_entries == detected entities (≥threshold) per doc |
| N1 | NICE | ORG F1 ≥ 0.80 | FAIL | BKA ORG F1 = 0.46 (whitelist suppresses authorities) |
| N2 | NICE | Phonetic linking accuracy | UNTESTED |  |
| N3 | NICE | OCR-noise robustness | UNTESTED |  |

**Aggregate:** 2 MUST fail, 1 MUST partial → UNFIT per pre-registered rule.

---

## 11. Limitations & Honesty Disclosure

1. No claim of production-readiness is made. Final suitability requires legal + DSGVO reviewer sign-off that this simulation does not substitute for.
2. Sample size (5 BKA documents, ~2630 total chars, 35 gold entities) is small. 95% CIs on recall are approximately ±15pp. Treat per-category recall as indicative.
3. No claim of "100% safe", "guaranteed", or "fully compliant" is made. PII detection is statistical — residual leakage risk is non-zero even on categories that scored 1.00 recall in this run.
4. Gaps from the pre-simulation PII audit (§8) are carried forward as warnings regardless of whether this simulation happened to trigger them.
5. Criteria marked UNTESTED cannot be asserted PASS. Future work should extend the corpus with quasi-identifier, phonetic-variant, and OCR-noise cases.
6. Failure cases in §7 show category + offset only; no leaked PII is reproduced in this report.
7. The simulation corpus is synthetic. Real BKA documents may contain formats (tables, forms, mixed German/English, Fraktur-OCR output) that this simulation did not exercise.
8. **Reproducibility:** commit `4cf8bdd29096d625ba0d23bc7055ee6d462ca3fc`; model revisions unpinned (HF "latest" resolved on 2026-04-18 via `scripts/prefetch_models.py`; `simulation_results/2026-04-18/prefetch.log`); models used: `HuggingLil/pii-sensitive-ner-german`, `Davlan/xlm-roberta-large-ner-hrl`, `dbmdz/bert-base-german-cased`, `urchade/gliner_large-v2.1`; default Settings; MPS backend.

---

## 12. Artifacts

All artifacts in `simulation_results/2026-04-18/`:

| File | Contents |
|---|---|
| `prefetch.log` | HF model download log |
| `pytest.log`, `pytest_junit.xml`, `coverage.json` | Test suite evidence |
| `benchmark_{synthetic_at,smoke_at,realistic_at,bka_ifg}.json` | Per-dataset P/R/F1 |
| `channel_comparison/*.json` | 15 per-(doc, channel) outputs |
| `channel_comparison/_summary.md` | Channel overview table |
| `channel_comparison/audit.log` | KAPA audit trail (5 docs × N entries) |
| `leakage_report.json` | Regex + ground-truth leakage findings |
| `metrics_raw.json` | Machine-readable consolidated summary |
| `verdict_report.md` | This document |

New file added to the repo (not in `simulation_results/`): `benchmarks/datasets/bka_ifg_simulation.json` — the 5 BKA synthetic documents, reusable for regression testing.
