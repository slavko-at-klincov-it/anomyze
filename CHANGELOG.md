# Changelog

All notable changes are documented in this file.

## [Unreleased]

### Phase D — Art. 9 Lexikon, BIC-Fix, BKA/IFG-Simulation

#### Added
- `anomyze/patterns/art9.py` — kuratierte österreichische Lexika für
  DSGVO Art. 9 Kategorien `RELIGION` (anerkannte Kirchen und
  Religionsgesellschaften + Alltagsformen), `POLITICAL` (Nationalrats-
  parteien + Mitgliedschafts-/Wähler-Affiliationen) und `UNION`
  (ÖGB + Teilgewerkschaften). Case-insensitive mit flexibler
  Mehrwort-Matcher (Bindestriche, Leerzeichen, NBSP). `ETHNICITY`,
  `SEXUAL_ORIENTATION`, `BIOMETRIC` bewusst nicht als Wortliste
  aufgenommen — zu fehleranfällig.
- `ATArt9Recognizer` in `anomyze/pipeline/recognizers/austrian.py` —
  neuer Presidio-kompatibler Recognizer, der die Lexika auswertet
  und pro Treffer den passenden Entity-Type (`RELIGION` /
  `POLITICAL` / `UNION`) emittiert. Score 0.9. Zusammen mit IFG's
  `BESONDERE_KATEGORIE`-Collapse und KAPA's `always_review_art9`
  schließt das die von der Simulation gefundene Lücke, in der
  `römisch-katholisch` unredigiert durch den IFG-Kanal rutschte.
- `benchmarks/datasets/bka_ifg_simulation.json` — 5 synthetische
  BKA-Dokumente (IFG-Bescheid, Ministerratsvortrag, Bürgeranfrage,
  interministerielle Mitteilung, parlamentarische Anfrage) mit
  prüfsummen-validen SVNR/IBAN/UID (via `stdnum`). Dient als
  Regressionsbasis für die Art. 9 / Adress / Kontext-Recognizer-
  Abdeckung.
- `simulation_results/2026-04-18/verdict_report.md` — Vollständiger
  BKA/IFG-Verdict-Report mit MUST/SHOULD/NICE-Matrix, Per-Entity-
  Recall-Werten und expliziter Auflistung der noch zu behebenden
  Gaps (Adresse, Führerschein, ZMR, Organisationen).

#### Fixed
- `ATBICRecognizer._is_valid_match` — das bisherige IGNORECASE-
  Regex-Matching erlaubte deutschen Wörtern wie „Religion" oder
  „Diagnose" durch die rein strukturelle `stdnum.bic.is_valid`-
  Prüfung zu schlüpfen (die Buchstabenpaare GI/DI entsprechen
  gültigen ISO-Länderkürzeln — Gibraltar/Dominikanische Republik).
  Neue Zusatzbedingung: der Match muss bereits im Quelltext
  vollständig uppercase sein. BIC-False-Positives im BKA-Korpus:
  9 → 1. Kein Recall-Verlust bei echten BICs.

#### Changed
- `anomyze/pipeline/presidio_compat_layer.py` — `ATArt9Recognizer`
  in den Default-Satz aufgenommen; `_ENTITY_TYPE_MAP` um die
  Einträge `RELIGION`, `POLITICAL`, `UNION` erweitert (direkte
  Passthrough-Mapping zum channel-intern erwarteten entity_group).
- `anomyze/pipeline/recognizers/__init__.py` — `ATArt9Recognizer`
  exportiert.

#### Docs
- README.md — neue Zeilen RELIGION/POLITIK/GEWERKSCHAFT in der
  PII-Tabelle, `Art. 9 Lexikon` in der Stage-2c-Recognizer-Liste
  der Pipeline-Übersicht, neue Sektion „Wann ist menschliche
  Prüfung erforderlich?" mit den Recall-Werten aus der Simulation.
- docs/architecture.md — `patterns/art9.py` in Package-Tree;
  `ATArt9Recognizer` in der Recognizer-Liste.
- docs/PROJECT-TODO.md — Art. 9 Lexikon und BKA/IFG-Simulation als
  abgeschlossene Meilensteine markiert.

### Phase C — Docker Verification, Deploy Templates, Tokenizer Fix

#### Added
- `deploy/` directory with production deployment templates:
  nginx TLS reverse-proxy, oauth2-proxy OIDC config, systemd
  retention/backup timers, env-var reference, backup/restore scripts.
- `docker-compose.local.yml` overlay for local smoke-testing with
  the host HF cache mounted rw.
- `scripts/docker_smoke.sh` — automated build + up + health + 3
  channels + /metrics scrape + down.
- `scripts/gen_model_manifest.py` — walks HF cache snapshots and
  emits SHA256 hashes (follows symlinks) for model integrity checks.

#### Fixed
- `transformers` pinned `<5.0` in `pyproject.toml` — transformers
  5.x funnels every SentencePiece tokenizer through
  `convert_to_native_format` which crashes on xlm-roberta's
  `.bpe.model` file regardless of `use_fast=False`.
- `sentencepiece>=0.2.0` added as runtime dependency (was only
  transitively present in some environments).
- `ModelManager` now pre-loads the slow tokenizer via
  `AutoTokenizer(use_fast=False)` and injects it into `hf_pipeline`
  — the pipeline's own `use_fast` kwarg is not forwarded internally.
- `ner_layer.py` resilient against `start=None`/`end=None` from
  slow tokenizers — new `_resolve_offsets` falls back to
  `text.find()`.
- `docker-compose.yml`: removed nested tmpfs under the HF cache
  volume (caused "read-only filesystem" on container start).
- `secure` 1.x API: `Secure.with_default_headers().set_headers()`
  replaces the removed `.framework.fastapi()`.
- `Dockerfile` pip install gets `--timeout 300 --retries 5`.

### Phase B — Verification (API Middleware Tests, Model Integrity)

#### Added
- `tests/test_api_hardening.py` (6 tests) — body-size 413,
  security headers, rate-limit smoke, graceful degradation.
- `tests/test_api_metrics.py` (5 tests) — `/metrics` endpoint,
  counter increments, no PII in labels.
- `tests/test_api_logging.py` (4 tests) — JSON format,
  structlog/stdlib fallback, no PII in logs.
- `config/model_hashes.json` — SHA256 manifest for the four
  default models. Regenerate with `scripts/gen_model_manifest.py`.

### Phase A — Post-Phase-3 Backwards-Compat & Compliance Fixes

#### Added
- `Settings.always_review_art9` (default `True`) — opt-out for KAPA's
  unconditional Art. 9 flagging via
  `ANOMYZE_ALWAYS_REVIEW_ART9=false`. Restores Phase 1/2 semantics
  where Art. 9 entities with scores above `kapa_review_threshold`
  are auto-anonymised.
- `Settings.max_request_text_chars` (default 50 000) — configurable
  via `ANOMYZE_MAX_REQUEST_TEXT_CHARS`. Replaces the hard-coded
  Pydantic `Field(max_length=50_000)` from Phase 3.
- `Settings.max_request_body_bytes` (default 500 000) — configurable
  via `ANOMYZE_MAX_REQUEST_BODY_BYTES`. Threaded through to
  `BodySizeLimitMiddleware`.
- `DELETE /api/v1/documents/{document_id}` — single call for DSGVO
  Art. 17 that clears both `mapping_store` and `audit_logger`.
- Regression-guard tests for the whitelist/PER collision
  (`tests/test_whitelist_collisions.py`) and for the Art. 9 opt-out
  invariant (`tests/test_kapa_art9_optout.py`).
- `ModelManager._hf_kwargs("")` now logs a WARNING when the model
  revision is unset so operators notice unpinned deployments.

#### Changed
- `Dockerfile` installs `".[api,observability,hardening]"` so the
  Phase 3 metrics/rate-limit/security-header middleware is actually
  active in the container. Previously only `.[api]` was installed
  and the middleware silently no-op'd.
- Removed the dead `ContextLayer._detect_quasi_identifiers_legacy`
  helper (pragma: no cover). The quasi-identifier implementation
  lives in `anomyze/pipeline/reidentification.py`; the shim in
  `context_layer.py` still delegates there.

#### Breaking Changes (consumer-visible)
- Pydantic error emitted on oversized `AnonymizeRequest.text`
  changes from `string_too_long` to `value_error`. Clients that
  parse API errors by `type` need to accommodate both.
- Phase 2's IFG channel collapses every DSGVO Art. 9 entity into a
  single `[GESCHWÄRZT:BESONDERE_KATEGORIE]` placeholder — by design,
  to keep the public redaction protocol from back-inferring the
  special category. Consumers that expected individual
  `HEALTH_DIAGNOSIS` / `RELIGION` / ... entries must migrate.
- Phase 2's KAPA channel flagged **every** Art. 9 entity for review
  regardless of score. Phase A makes this opt-out via
  `ANOMYZE_ALWAYS_REVIEW_ART9=false`; default remains opt-in.
- Phase 1 removed the erroneous `U+00A7 → ß` mapping from
  `fix_encoding`. Pipelines that fed intentionally obfuscated
  `§`-as-`ß` text need to pre-process such inputs externally
  (commit `ffa05f9`).

### Phase 3 — Production Readiness, Compliance, Benchmark CI

#### Added
- Optional dependency groups in `pyproject.toml`:
  - `observability` — `structlog>=24.1.0`,
    `prometheus-fastapi-instrumentator>=7.0.0`.
  - `hardening` — `slowapi>=0.1.9`, `secure>=0.3.0`.
- `anomyze/api/logging_config.py` — structlog-based JSON logger that
  falls back to stdlib logging when structlog is not installed. Never
  emits raw text or entity words; only `document_id`, `channel`,
  `entity_count`, `duration_ms`, `layer`.
- `anomyze/api/metrics.py` — Prometheus instrumentation (no-op without
  the optional dep). Exposes `/metrics` and emits:
  - `anomyze_entity_detected_total{category,layer,channel}`
  - `anomyze_pipeline_stage_duration_seconds{stage}`
  - `anomyze_confidence_score{category,layer}`
  - `anomyze_channel_requests_total{channel}`
  - `anomyze_model_loaded`
- `anomyze/api/hardening.py` — opt-in API hardening: `slowapi`
  rate-limit middleware, `secure` security headers, and an always-on
  `BodySizeLimitMiddleware` (default 500 KB).
- Per-stage timing (`time.perf_counter()`) wrapped around every
  pipeline stage in `orchestrator.py` and forwarded to the Prometheus
  histogram.
- `anomyze/pipeline/model_integrity.py` — SHA256 manifest validator
  (`config/model_hashes.json`) for the cached HuggingFace snapshots.
- `scripts/prefetch_models.py` — air-gap-friendly pre-fetcher for the
  configured pii / org / mlm / gliner models with optional revision
  pinning.
- `anomyze/benchmark/regression_check.py` — release gate. Compares a
  fresh JSON benchmark report against a baseline; fails when overall
  F1 drops by more than the configured absolute / relative threshold
  or when any critical category (default `SVN, IBAN, EMAIL`) falls
  below 0.95 recall.
- `.github/workflows/benchmark.yml` — manual / on-release benchmark
  job. Sequential (no matrix), caches HF models, optionally runs the
  regression gate, uploads the report artifact (90-day retention).
- `RetentionPolicy` dataclass and `AuditLogger.enforce_retention()` /
  `AuditLogger.forget()` for DSGVO Art. 5 (1) e and Art. 17 support.
  PII is wiped after 7 days; entries hard-deleted after 7 years.
- `docs/compliance/` skeleton documents:
  - `README.md` — index and intent.
  - `dpia.md` — Datenschutz-Folgenabschätzung template (Art. 35).
  - `avv_template.md` — Auftragsverarbeitungsvertrag (Art. 28).
  - `retention_policy.md` — channel-specific retention durations.
  - `loeschkonzept.md` — operative Löschanweisung.
  - `ropa.md` — Verzeichnis von Verarbeitungstätigkeiten (Art. 30).
- New tests: `test_model_integrity.py`, `test_regression_check.py`,
  `test_audit_retention.py` (covering both `forget()` and
  `enforce_retention()` including idempotency).

#### Changed
- `Settings`: new `pii_model_revision`, `org_model_revision`,
  `mlm_model_revision`, `gliner_model_revision`,
  `fail_on_model_integrity_mismatch`. Empty string keeps the
  legacy "track latest" behaviour.
- `ModelManager.load_*_pipeline` honour the optional revision pin and
  pass it through to `from_pretrained`.
- API request size capped: `AnonymizeRequest.text` `max_length=50_000`
  characters; body-size middleware rejects payloads > 500 KB.
- API factory now configures structured logging, installs the
  Prometheus instrumentator and the hardening middleware on startup.

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
