# Changelog

All notable changes are documented in this file.

## [Unreleased]

### Phase 2 — Core Detection, Robustness, Re-Identification, Benchmark

#### Added
- `ART9_SENSITIVE_CATEGORIES` constant in `anomyze/pipeline/__init__.py`
  enumerating DSGVO Art. 9 special categories (health, religion,
  ethnicity, political opinion, union membership, sexual orientation,
  biometric data).
- `anomyze/patterns/healthcare.py` with ICD-10 chapter validation
  (`is_icd10_code`).
- New recognizers in `anomyze/pipeline/recognizers/austrian.py`:
  - `ATICD10Recognizer` — ICD-10 diagnosis codes with chapter-range
    validation; **mandatory medical context** to avoid collisions
    with room numbers and form codes.
  - `ATFuehrerscheinRecognizer` — 8-digit Austrian driving licence
    number (post-2006 Scheckkarten format) with mandatory FS context.
  - `ATZMRRecognizer` — 12-digit ZMR-Kennzahl (Zentrales
    Melderegister), context-only.
  - `ATGerichtsaktenzahlRecognizer` — court docket references in the
    senate-abbreviation format (`3 Ob 123/45`, `14 Os 45/23`).
- `find_long_date_regex` in `anomyze/patterns/dates.py` — long-form
  German dates (`20. Dezember 2023`, supports both `März` and
  `Maerz`).
- New normalizer functions in `anomyze/pipeline/normalizer.py`:
  - `rejoin_hyphenation` — rejoins `Mü-\nller` → `Müller`.
  - `normalize_leetspeak_in_names` — context-gated leet substitution
    (Herr/Frau/Dr./Mag./...) so IBAN/SVNR digits are not destroyed.
  - RTL/bidi-override (`U+202A`-`E`, `U+2066`-`9`) added to
    `_INVISIBLE_CHARS`.
  - Armenian `o` and the mathematical-bold alphabet (via NFKC)
    are now folded to plain ASCII.
- New `anomyze/pipeline/reidentification.py` module containing the
  full quasi-identifier detector. Adds **Profession** patterns
  (Arzt/Lehrer/Polizist/Bürgermeister/...) and **Relationship**
  patterns (Sohn von / Ehefrau des / Cousin von / ...). Heuristic
  k-estimate (`max(1, 6 - #signal_types)`) attached to the
  `context` field of the first flagged signal.
- `anomyze/pipeline/quality_check.py` extended with
  `_check_name_dict_leakage`: post-anonymization rescan against the
  AT name dictionary. Two-tier reporting: adjacent first+last name
  → `leak`, single surname → `warn`. Only runs when at least one
  placeholder is present (avoids second-guessing untouched input).
- New benchmark generator
  `anomyze/benchmark/generators/at.py` (CLI:
  `python -m anomyze.benchmark.generators.at`). Produces deterministic
  synthetic AT samples with checksum-valid SVNR/IBAN/UID via
  `python-stdnum`. No new runtime dependency.
- New benchmark dataset `benchmarks/datasets/smoke_at.json`
  (50 deterministic samples) intended for fast PR-CI runs.

#### Changed
- IFG channel now collapses every Art. 9 entity into a single
  `[GESCHWÄRZT:BESONDERE_KATEGORIE]` placeholder and reports it as a
  single line in the redaction protocol — prevents the public
  protocol from leaking which special category was present.
- KAPA channel now flags **every** Art. 9 entity for human review
  (`[PRÜFEN:...]` + `audit_entries[...].action='flagged_for_review'`)
  regardless of the raw confidence score. Non-Art.9 entities still
  follow the configured `kapa_review_threshold`.
- GovGPT placeholder map extended with new categories: `GESUNDHEIT`,
  `RELIGION`, `HERKUNFT`, `POLITIK`, `GEWERKSCHAFT`,
  `SEXUELLE_ORIENTIERUNG`, `BIOMETRIE`, `FUEHRERSCHEIN`, `ZMR`.
- `Settings`: new `quasi_id_window: int = 200` (configurable proximity
  window for re-identification) and `use_leetspeak_normalization: bool
  = True` (lets adopters opt out of name-context leetspeak folding).
- `ContextLayer._detect_quasi_identifiers` is now a thin shim
  delegating to the new module — old in-line implementation kept as
  `_detect_quasi_identifiers_legacy` for diffability and removed in a
  follow-up cleanup.
- `tests/test_benchmark_datasets.py` validates the new
  `smoke_at.json` and accepts the new `UID`/`BIC` categories.

### Phase 1 — Quick Wins (Detection Quality, Whitelist, Container Hardening)

#### Added
- `python-stdnum>=1.20` as a runtime dependency. Used for real checksum
  validation of IBAN (ISO 13616 MOD-97), Austrian SVNR (MOD-11 weighted
  sum + birth-date portion), Austrian UID (ATU...), and BIC country
  component.
- New recognizers in `anomyze/pipeline/recognizers/austrian.py`:
  - `ATUIDRecognizer` — Austrian VAT identification number (ATU + 8
    digits, MOD-11 check digit via `stdnum.at.uid`). Context: "uid",
    "umsatzsteuer-identifikationsnummer", "ust-id", "ust.-nr", "vat".
  - `ATBICRecognizer` — BIC / SWIFT codes with country-component check
    via `stdnum.bic`. Context-gated because the 8-char all-caps shape
    overlaps with common acronyms.
- `anomyze/patterns/whitelist.py` — Austrian legal-reference whitelist.
  Keeps statute abbreviations (ASVG, DSGVO, StGB, B-VG, ...) and
  well-known federal / regional authorities (BMI, VfGH, ÖGK,
  Statistik Austria, Magistrat, Bezirkshauptmannschaft, ...) in the
  output instead of redacting them. Integrated in the orchestrator
  after `merge_entities()` and before the Context Layer so that
  whitelisted authorities do not inflate quasi-identifier counts.
- New `UID` and `BIC` placeholder mappings in the GovGPT channel.
- Benchmark dataset `real-007-rechnung` covering UID, BIC, IBAN,
  Firmenbuchnummer, email and phone in one realistic invoice.
- `tests/test_whitelist.py` covering paragraph citations, statute
  codes, authority matching, entity-group gating and the
  `filter_whitelisted()` helper. Additional tests in
  `tests/test_recognizers.py` for the new UID / BIC recognizers and
  for the IBAN checksum rejection.

#### Changed
- IBAN / SVNR detection (both the regex layer and the Presidio-compat
  recognizers) now reject matches whose checksum fails, eliminating a
  frequent source of false positives (especially all-zero placeholder
  IBANs in templates).
- GLiNER entity-type list extended with `"austrian vat id"` and
  `"bank identifier code"` so the zero-shot layer sees the new
  categories when enabled.
- `docker-compose.yml` hardened: `read_only: true`, `tmpfs`
  entries for `/tmp` and the HuggingFace cache temp dir,
  `no-new-privileges`, `cap_drop: [ALL]`, memory limit raised from
  6 GB to 10 GB with a 4 GB reservation, and a 4-CPU cap.
- `Dockerfile` `HEALTHCHECK --start-period` raised from 120 s to
  300 s because first-boot model loading regularly exceeded the old
  window.
- All benchmark fixtures and test sample documents updated to use
  SVNR and IBAN values that pass the new checksum validation
  (example: `1234 010180` → `1237 010180`,
  `AT00 0000 0000 0000 0001` → `AT88 0000 0000 0000 0001`).

#### Fixed
- Removed the erroneous `'\u00a7': 'ß'` mapping from the encoding-fix
  table in `orchestrator.py`. `§` (U+00A7) is a valid character in
  Austrian legal text and must not be rewritten to `ß`.

### Notes
- No behavioural change to the KAPA audit trail or the IFG redaction
  protocol in this phase.
- No API contract changes; new entity groups (`UID`, `BIC`) surface in
  the existing `entities` list as additional types.
