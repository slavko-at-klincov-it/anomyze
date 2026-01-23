# Anomyze - Projekt TODO

## Projektstruktur-Empfehlung

**Empfehlung: Zwei separate Repositories**

```
anomyze/                    ← Bestehendes Repo (Core Library)
├── anomyze.py              → wird zu anomyze/core.py
├── pyproject.toml          → PyPI Package
├── tests/
└── docs/

anomyze-extension/          ← Neues Repo (Extension + API)
├── server/                 → FastAPI Backend
├── extension/              → Browser Extension
├── admin/                  → Admin UI (React)
├── docker/
└── docs/
```

### Warum zwei Projekte?

| Aspekt | Ein Monorepo | Zwei Repos |
|--------|--------------|------------|
| **Releases** | Gekoppelt | Unabhängig |
| **Contributor** | Verwirrend | Klar getrennt |
| **CI/CD** | Komplex | Einfach |
| **Lizenzierung** | Problematisch | Flexibel |
| **Dependencies** | Vermischt | Sauber |

**Empfehlung:** Zwei Repos mit `anomyze` als Dependency in `anomyze-extension`.

---

# Phase 1: Anomyze Core Library refactoren

## 1.1 Code-Struktur

- [ ] **Restructure als Python Package**
  ```
  anomyze/
  ├── __init__.py
  ├── core.py          ← Hauptlogik
  ├── models.py        ← Model Loading
  ├── patterns.py      ← Regex Patterns
  ├── entities.py      ← Entity Classes
  ├── config.py        ← Configuration
  └── cli.py           ← CLI Entry Point
  ```

- [ ] **pyproject.toml erstellen**
  - Package Name: `anomyze`
  - Version: 1.0.0
  - Python: >=3.10
  - Dependencies: torch, transformers, etc.

- [ ] **Type Hints hinzufügen**
  - Alle Funktionen typisieren
  - mypy kompatibel machen

## 1.2 Tests

- [ ] **Test-Framework aufsetzen**
  - pytest
  - pytest-cov für Coverage

- [ ] **Unit Tests schreiben**
  - [ ] `test_regex_patterns.py` - Alle Regex-Muster
  - [ ] `test_entity_cleaning.py` - Entity Cleanup
  - [ ] `test_anonymization.py` - Hauptfunktion
  - [ ] `test_encoding.py` - Encoding Fixes

- [ ] **Integration Tests**
  - [ ] Vollständige Anonymisierung mit echten Texten
  - [ ] Performance-Benchmarks

- [ ] **Test-Daten erstellen**
  - Anonymisierte Beispieltexte
  - Edge Cases (Umlaute, Sonderzeichen)

## 1.3 Dokumentation

- [ ] **README.md aktualisieren**
  - Installation via pip
  - Quick Start
  - API Reference

- [ ] **API Dokumentation**
  - Docstrings für alle Funktionen
  - Sphinx oder MkDocs Setup

## 1.4 CI/CD

- [ ] **GitHub Actions**
  - [ ] Linting (ruff, black)
  - [ ] Tests (pytest)
  - [ ] Type Checking (mypy)
  - [ ] Coverage Report

- [ ] **PyPI Publishing**
  - [ ] TestPyPI zuerst
  - [ ] Automatisches Publishing bei Release

## 1.5 Lizenz klären

- [ ] **PII Model Lizenz prüfen**
  - `HuggingLil/pii-sensitive-ner-german`
  - Kontakt mit Model-Autor aufnehmen
  - Alternative Modelle evaluieren falls nötig

- [ ] **Lizenz für Anomyze wählen**
  - MIT? Apache 2.0? Dual License?
  - LICENSE Datei erstellen

---

# Phase 2: Anomyze API Server

## 2.1 FastAPI Backend

- [ ] **Grundstruktur**
  ```
  server/
  ├── app/
  │   ├── __init__.py
  │   ├── main.py           ← FastAPI App
  │   ├── api/
  │   │   ├── v1/
  │   │   │   ├── anonymize.py
  │   │   │   ├── check.py
  │   │   │   ├── config.py
  │   │   │   └── health.py
  │   ├── core/
  │   │   ├── config.py     ← Settings
  │   │   ├── security.py   ← Auth
  │   │   └── models.py     ← ML Model Management
  │   ├── schemas/
  │   │   ├── request.py
  │   │   └── response.py
  │   └── middleware/
  │       ├── logging.py
  │       └── rate_limit.py
  ├── tests/
  ├── Dockerfile
  └── requirements.txt
  ```

- [ ] **API Endpoints implementieren**
  - [ ] `POST /api/v1/anonymize`
  - [ ] `POST /api/v1/check`
  - [ ] `GET /api/v1/config`
  - [ ] `GET /api/v1/health`
  - [ ] `POST /api/v1/feedback`

- [ ] **Model Loading optimieren**
  - Lazy Loading
  - Warmup beim Start
  - Health Check für Model Status

## 2.2 Authentifizierung

- [ ] **Token-basierte Auth**
  - JWT Tokens
  - Token Validation Middleware

- [ ] **SSO Integration (später)**
  - SAML Support
  - OIDC Support
  - Entra ID Integration

## 2.3 Rate Limiting

- [ ] **Redis-basiertes Rate Limiting**
  - Per-User Limits
  - Per-IP Limits
  - Sliding Window

- [ ] **Graceful Degradation**
  - 429 Responses mit Retry-After
  - Backoff-Strategien dokumentieren

## 2.4 Logging & Monitoring

- [ ] **Strukturiertes Logging**
  - JSON Format
  - Request IDs
  - Keine sensiblen Daten!

- [ ] **Prometheus Metrics**
  - Request Latency
  - Model Inference Time
  - Error Rates
  - Active Connections

- [ ] **Health Checks**
  - Liveness: API läuft
  - Readiness: Modelle geladen

## 2.5 Docker

- [ ] **Dockerfile**
  - Multi-Stage Build
  - Non-root User
  - Optimierte Layer

- [ ] **docker-compose.yml**
  - API Server
  - Redis (optional)
  - Prometheus (optional)

- [ ] **Kubernetes Manifests (später)**
  - Deployment
  - Service
  - ConfigMap
  - Secrets
  - HPA

---

# Phase 3: Browser Extension

## 3.1 Extension Grundstruktur

- [ ] **Manifest V3 Setup**
  ```
  extension/
  ├── manifest.json
  ├── src/
  │   ├── background/
  │   │   └── service-worker.ts
  │   ├── content/
  │   │   ├── content-script.ts
  │   │   └── regex-engine.ts
  │   ├── popup/
  │   │   ├── popup.html
  │   │   ├── popup.ts
  │   │   └── popup.css
  │   ├── options/
  │   │   ├── options.html
  │   │   └── options.ts
  │   └── shared/
  │       ├── api-client.ts
  │       ├── storage.ts
  │       └── types.ts
  ├── public/
  │   └── icons/
  ├── webpack.config.js
  └── package.json
  ```

## 3.2 Content Script

- [ ] **Textarea Detection**
  - ChatGPT Eingabefeld finden
  - Gemini Eingabefeld finden
  - Claude Eingabefeld finden
  - Generische Textarea-Erkennung

- [ ] **Input Interception**
  - Submit Event abfangen
  - Keyboard Shortcuts (Ctrl+Enter, etc.)
  - Paste Events

- [ ] **Lokale Regex-Engine**
  - E-Mail Regex
  - IBAN Regex
  - Telefonnummer Regex
  - Deutsche Titel + Name Regex

- [ ] **API Communication**
  - Async Request an Server
  - Timeout Handling
  - Retry Logic
  - Fallback zu Regex-Only

## 3.3 Popup UI

- [ ] **Status Anzeige**
  - Verbindungsstatus
  - Letzte Erkennungen
  - An/Aus Toggle

- [ ] **Aktionen**
  - Whitelist für aktuelle Seite
  - Korrektur melden
  - Einstellungen öffnen

## 3.4 Options Page

- [ ] **Benutzereinstellungen**
  - Server URL
  - Fallback-Verhalten
  - Benachrichtigungen

- [ ] **Enterprise Settings (managed)**
  - Via managed_storage
  - Nicht vom User änderbar

## 3.5 Enterprise Features

- [ ] **Managed Schema**
  - `managed_schema.json` für Chrome
  - ADMX Templates für Edge

- [ ] **Policy Support**
  - Force-Install via GPO
  - Zentrale Konfiguration

## 3.6 Build & Distribution

- [ ] **Build Pipeline**
  - TypeScript Compilation
  - Webpack Bundle
  - Source Maps (nur Dev)

- [ ] **Chrome Web Store**
  - Developer Account
  - Private/Unlisted Listing
  - Review Process

- [ ] **Edge Add-ons**
  - Microsoft Partner Center
  - Submission Process

---

# Phase 4: Admin UI

## 4.1 React Dashboard

- [ ] **Tech Stack**
  - React 18+
  - TypeScript
  - Tailwind CSS oder shadcn/ui
  - React Query

- [ ] **Seiten**
  - [ ] Dashboard (Übersicht)
  - [ ] Regeln verwalten
  - [ ] Domains verwalten
  - [ ] Benutzergruppen
  - [ ] Logs / Audit
  - [ ] Einstellungen

## 4.2 Regel-Editor

- [ ] **Regel-Typen**
  - Entity-basiert (PER, ORG, etc.)
  - Pattern-basiert (Regex)
  - Custom Wordlists

- [ ] **Aktionen**
  - Anonymisieren
  - Blockieren
  - Warnen
  - Umleiten

- [ ] **Bedingungen**
  - Domain-Filter
  - Benutzergruppen
  - Zeitbasiert

## 4.3 Analytics (Basic)

- [ ] **Statistiken**
  - Anfragen pro Tag
  - Erkannte Entitäten
  - Top Domains
  - Error Rates

---

# Phase 5: Testing & QA

## 5.1 End-to-End Tests

- [ ] **Playwright Setup**
  - Browser Automation
  - Extension Testing

- [ ] **Test-Szenarien**
  - [ ] ChatGPT Anonymisierung
  - [ ] Gemini Anonymisierung
  - [ ] Claude Anonymisierung
  - [ ] Blocking-Regeln
  - [ ] Redirect-Regeln
  - [ ] Offline-Fallback

## 5.2 Load Testing

- [ ] **k6 oder Locust Setup**
  - API Benchmarks
  - Concurrent Users
  - Latency Percentiles

## 5.3 Security Testing

- [ ] **OWASP Checks**
  - Injection
  - XSS
  - CSRF
  - Auth Bypass

- [ ] **Penetration Test (später)**
  - Externe Firma beauftragen

---

# Phase 6: Dokumentation

## 6.1 Technische Docs

- [ ] **API Dokumentation**
  - OpenAPI/Swagger
  - Beispiel-Requests

- [ ] **Extension Docs**
  - Entwickler-Guide
  - Build Instructions

- [ ] **Deployment Guide**
  - Docker
  - Kubernetes
  - On-Premise Requirements

## 6.2 User Docs

- [ ] **Admin Guide**
  - Regel-Konfiguration
  - User Management
  - Troubleshooting

- [ ] **End-User Guide**
  - Extension Nutzung
  - FAQ

## 6.3 Compliance Docs

- [ ] **DSGVO Dokumentation**
  - Verarbeitungsverzeichnis
  - TOM (Technisch-Organisatorische Maßnahmen)

- [ ] **Betriebsrat-Vorlage**
  - Betriebsvereinbarung Template

---

# Offene Fragen & Entscheidungen

## Technisch

- [ ] **PII Model Alternative?**
  - Falls Lizenz problematisch
  - Eigenes Fine-Tuning?

- [ ] **Caching-Strategie?**
  - Redis für häufige Patterns?
  - Wie lange cachen?

- [ ] **Multi-Language Support?**
  - Wann Englisch hinzufügen?
  - Separate Modelle oder Multilingual?

## Business

- [ ] **Pricing-Modell?**
  - Per User/Month
  - Per Request
  - Flat Fee

- [ ] **Support-Level?**
  - Community (kostenlos)
  - Professional (bezahlt)
  - Enterprise (SLA)

- [ ] **Go-to-Market?**
  - Direktvertrieb
  - Partner/Reseller
  - Self-Service

---

# Timeline-Empfehlung

| Phase | Dauer | Output |
|-------|-------|--------|
| 1. Core Refactoring | 2-3 Wochen | anomyze v1.1 auf PyPI |
| 2. API Server | 3-4 Wochen | Docker Image |
| 3. Extension MVP | 4-6 Wochen | Chrome Extension |
| 4. Admin UI Basic | 2-3 Wochen | Web Dashboard |
| 5. Testing | 2 Wochen | Test Coverage >80% |
| 6. Docs | 1-2 Wochen | Vollständige Docs |

**Gesamt: 14-20 Wochen für MVP**

---

# Nächste konkrete Schritte

1. **Heute/Diese Woche:**
   - [ ] Neues Repo `anomyze-extension` erstellen
   - [ ] Core refactoring beginnen (Package-Struktur)
   - [ ] PII Model Lizenz prüfen

2. **Nächste Woche:**
   - [ ] Tests für Core schreiben
   - [ ] FastAPI Grundgerüst aufsetzen
   - [ ] Extension Manifest V3 Grundstruktur

3. **Danach:**
   - [ ] Iterativ entwickeln
   - [ ] Regelmäßige Reviews

---

*Dokument-Version: 1.0 | Erstellt: Januar 2025*
