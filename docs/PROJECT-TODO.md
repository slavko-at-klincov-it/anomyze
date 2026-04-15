# Anomyze - Projekt-TODO

*Ursprünglich erstellt: Januar 2025. Zuletzt aktualisiert: April 2026 nach Task 9 (Benchmark-Framework).*

## Status-Übersicht

| Phase | Status | Ergebnis |
|-------|--------|----------|
| 1. Anomyze Core Library | **Erledigt** | anomyze v2.0.0, auf PyPI-ready, MIT-lizenziert |
| 2. Anomyze API Server | **Erledigt** (Basis) | FastAPI + Docker, REST-Endpunkte `/anonymize`, `/health`, `/mappings`, `/audit` |
| 3. Browser-Extension | **Ausgelagert** | Geplant in separatem Repo `anomyze-extension` |
| 4. Admin-UI | **Ausgelagert** | Geplant in separatem Repo `anomyze-extension` |
| 5. End-to-End-Testing | Teilweise | Unit-/Integration-/Adversarial-Tests vorhanden, E2E-Extension offen |
| 6. Dokumentation | Laufend | README, architecture.md, api_reference.md, Whitepaper v2.0, Benchmark-Doku |

Phasen 3-6 betreffen das geplante Schwester-Repository `anomyze-extension` (Browser-Extension + Admin-UI). Sie bleiben hier als Referenz für die ursprüngliche Roadmap dokumentiert.

---

## Projektstruktur-Entscheidung

**Entscheidung:** Zwei separate Repositories.

```
anomyze/                    ← Aktuelles Repo (Core Library)
├── anomyze/                → Package
├── benchmarks/             → Benchmark-Datasets
├── tests/
└── docs/

anomyze-extension/          ← Zukünftiges Repo (Extension + API + Admin-UI)
├── server/                 → FastAPI Backend (mit anomyze als Dependency)
├── extension/              → Browser Extension
├── admin/                  → Admin UI (React)
├── docker/
└── docs/
```

Begründung: Unabhängige Releases, sauberere Dependencies, klarere Lizenzierung, geringere CI-Komplexität.

---

# Phase 1: Anomyze Core Library [ERLEDIGT]

## 1.1 Code-Struktur

- [x] **Restructure als Python Package** — siehe `anomyze/{api,benchmark,channels,config,mappings,patterns,pipeline}/`
- [x] **pyproject.toml erstellt** — Version 2.0.0, Python >=3.10, Dependencies: torch, transformers, prompt-toolkit
- [x] **Type Hints hinzugefügt** — mypy sauber (`warn_return_any`, `warn_unused_configs`)

## 1.2 Tests

- [x] **pytest + pytest-cov aufgesetzt**
- [x] **Unit Tests** — Regex-Patterns, Ensemble, Entity-Resolver, Phonetik, Normalizer, Recognizers, Pipeline-Unit, Quality-Check
- [x] **Integration Tests** — `test_integration.py`
- [x] **Adversarial Tests** — `test_adversarial.py`
- [x] **Benchmark-Framework** — Precision/Recall/F1 auf annotierten Ground-Truth-Datasets
- [x] **Test-Daten** — `tests/fixtures/`, `benchmarks/datasets/` (synthetic_at, realistic_at)

## 1.3 Dokumentation

- [x] **README.md** auf v2.0-Stand
- [x] **docs/architecture.md** — vollständige Pipeline + Paketstruktur
- [x] **docs/api_reference.md** — REST-Endpunkte + Entity-Typen
- [x] **docs/whitepaper-anomyze.md** v2.0
- [x] **benchmarks/README.md**

## 1.4 CI/CD

- [x] **GitHub Actions** — Linting (ruff), Tests (pytest), Type Checking (mypy), Coverage
- [ ] **PyPI Publishing** — TestPyPI zuerst, dann automatisches Publishing bei Release

## 1.5 Lizenz

- [x] **Lizenz gewählt:** MIT (LICENSE-Datei vorhanden)
- [ ] **PII-Model-Lizenz prüfen** — `HuggingLil/pii-sensitive-ner-german` verwendet, Lizenz-Klärung offen. Fallback: Davlan/xlm-roberta-large-ner-hrl deckt Personen und Organisationen bereits ab; ein Swap ist möglich, falls die Lizenz problematisch ist.

---

# Phase 2: Anomyze API Server [ERLEDIGT - Basis]

## 2.1 FastAPI Backend

- [x] **Grundstruktur** — `anomyze/api/{main.py, routes.py, models.py}`
- [x] **API-Endpoints:**
  - [x] `POST /api/v1/anonymize`
  - [x] `GET /api/v1/health`
  - [x] `GET /api/v1/mappings/{document_id}`
  - [x] `DELETE /api/v1/mappings/{document_id}`
  - [x] `GET /api/v1/audit/{document_id}`
- [x] **Model Loading** — Lazy Loading via `ModelManager`, Warmup beim Start, Health-Check für Model-Status

## 2.2 Authentifizierung

- [ ] **Token-basierte Auth** (JWT) — offen
- [ ] **SSO-Integration** (SAML/OIDC/Entra ID) — offen, in `anomyze-extension` vorgesehen

## 2.3 Rate Limiting

- [ ] **Redis-basiertes Rate Limiting** — offen
- [ ] **Graceful Degradation** — offen

## 2.4 Logging & Monitoring

- [x] **Strukturiertes Logging** — via `anomyze/audit/logger.py` für KAPA-Kanal
- [ ] **Prometheus Metrics** — offen
- [x] **Health Checks** — `/api/v1/health` mit Model-Status

## 2.5 Docker

- [x] **Dockerfile** — vorhanden
- [x] **docker-compose.yml** — vorhanden
- [ ] **Kubernetes Manifests** — offen

---

# Phase 3: Browser Extension [AUSGELAGERT in anomyze-extension]

Für die Extension ist ein separates Repository vorgesehen. Die ursprüngliche Roadmap (Manifest V3, Content-Script mit lokaler Regex-Engine, Popup-UI, Options-Page, Enterprise-Features via managed_storage) bleibt als Referenz:

- Manifest V3 Setup, TypeScript, Webpack
- ChatGPT / Gemini / Claude Textarea-Detection + Input-Interception
- Lokale Regex-Engine als Fallback + async API-Calls
- Popup + Options + Managed-Schema (`managed_schema.json`, ADMX für Edge)
- Chrome Web Store + Edge Add-ons Distribution

---

# Phase 4: Admin UI [AUSGELAGERT in anomyze-extension]

- React 18+ / TypeScript / shadcn/ui / React Query
- Seiten: Dashboard, Regeln, Domains, Benutzergruppen, Logs/Audit, Einstellungen
- Regel-Editor (Entity-basiert, Pattern-basiert, Custom Wordlists)
- Basic Analytics (Anfragen/Tag, erkannte Entitäten, Top-Domains, Error-Rates)

---

# Phase 5: End-to-End-Testing

- [x] **Unit- und Integrationstests** im Core-Repo
- [x] **Adversarial-Tests** (Homoglyphen, Zero-Width-Spaces, Leetspeak)
- [x] **Benchmark-Framework** für Detection-Qualitätsmessung
- [ ] **Playwright-E2E** für die Extension — in `anomyze-extension`
- [ ] **Load Testing** (k6 oder Locust) — offen
- [ ] **Security Testing** (OWASP, Penetration Test) — offen

---

# Phase 6: Dokumentation

## 6.1 Technische Docs

- [x] **API-Dokumentation** — `docs/api_reference.md` + FastAPI OpenAPI
- [x] **Architektur-Dokumentation** — `docs/architecture.md`
- [x] **Whitepaper** — `docs/whitepaper-anomyze.md` v2.0
- [x] **Benchmark-Doku** — `benchmarks/README.md`
- [ ] **Deployment-Guide** (Docker detailliert, Kubernetes, On-Premise-Requirements) — offen

## 6.2 User Docs

- [ ] **Admin-Guide** — offen (hängt an Admin-UI)
- [ ] **End-User-Guide** — offen (hängt an Extension)

## 6.3 Compliance-Docs

- [ ] **DSGVO-Dokumentation** (Verarbeitungsverzeichnis, TOM) — offen
- [ ] **Betriebsrat-Vorlage** — offen

---

# Offene Fragen & Entscheidungen

## Technisch

- [ ] **PII-Model Alternative?** Lizenz-Klärung für `HuggingLil/pii-sensitive-ner-german` offen. Davlan/xlm-roberta-large-ner-hrl ist einsatzfähig als Backup.
- [ ] **Caching-Strategie?** Redis für häufige Patterns — relevant ab Extension-Release.
- [ ] **Multi-Language Support?** Aktuell DE/AT. Englisch kommt natürlich mit via xlm-roberta; Tests für EN-PII fehlen noch.

## Business

- [ ] Pricing-Modell (Per User/Month vs. Per Request vs. Flat Fee) — offen
- [ ] Support-Level (Community / Professional / Enterprise mit SLA) — offen
- [ ] Go-to-Market (Direktvertrieb / Partner / Self-Service) — offen

---

# Nächste konkrete Schritte

1. **PyPI-Publishing** — TestPyPI für v2.0.0 vorbereiten.
2. **Lizenzklärung PII-Model** — Kontakt mit Model-Autor bzw. Swap-Plan finalisieren.
3. **Repository `anomyze-extension`** anlegen und Grundgerüst (FastAPI-Server mit `anomyze` als Dependency, Manifest V3, Admin-UI-Skeleton).
4. **Deployment-Guide** schreiben (Docker + On-Premise-Requirements).
