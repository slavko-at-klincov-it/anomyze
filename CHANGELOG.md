# Changelog

All notable changes are documented in this file.

## [Unreleased]

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
