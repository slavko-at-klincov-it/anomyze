# Anomyze

## Datenschutzkonforme KI-Nutzung im Unternehmen

**Whitepaper v1.1**

---

# Executive Summary

Die Nutzung von KI-Tools wie ChatGPT, Google Gemini oder Claude durch Mitarbeiter ist nicht mehr aufzuhalten. Studien zeigen, dass über 70% der Wissensarbeiter bereits KI-Assistenten nutzen – oft ohne Wissen der IT-Abteilung. Dabei werden täglich sensible Unternehmensdaten, Kundennamen, interne Projektnamen und vertrauliche Informationen an externe Server übertragen.

**Anomyze** löst dieses Problem durch automatische Anonymisierung direkt im Browser. Bevor Daten an externe KI-Dienste gesendet werden, erkennt und ersetzt Anomyze personenbezogene Daten, Firmennamen und sensible Informationen durch Platzhalter. Die KI erhält nur anonymisierte Anfragen – die Produktivitätsvorteile bleiben erhalten, das Datenschutzrisiko wird eliminiert.

### Kernvorteile auf einen Blick

| Für Management | Für IT-Leiter | Für Datenschutz |
|----------------|---------------|-----------------|
| Produktivität erhalten | Einfaches Deployment | DSGVO-Konformität |
| Kontrollierter KI-Einsatz | Zentrale Administration | Keine Daten an Dritte |
| Risikominimierung | On-Premise möglich | Audit-Trail |
| Wettbewerbsvorteil | Browser-Integration | Privacy by Design |

---

# 1. Die Herausforderung: Shadow AI im Unternehmen

## 1.1 Das Problem

Seit der Veröffentlichung von ChatGPT im November 2022 hat sich die Arbeitswelt fundamental verändert. Mitarbeiter nutzen KI-Assistenten für:

- E-Mail-Formulierungen und Kommunikation
- Code-Entwicklung und Debugging
- Analyse von Dokumenten und Verträgen
- Protokolle und Meeting-Zusammenfassungen
- Übersetzungen und Textoptimierung

**Das Risiko:** Bei jeder Nutzung werden die eingegebenen Daten an externe Server übertragen. Ein typisches Beispiel:

> *„Kannst du mir helfen, eine E-Mail an Herrn Thomas Müller von der Ersten Bank zu formulieren? Es geht um das Projekt Goldfinch mit einem Volumen von 2,3 Mio. Euro..."*

Mit dieser einen Anfrage wurden übertragen:
- Ein Personenname (Thomas Müller)
- Ein Unternehmensname (Erste Bank)
- Ein interner Projektname (Goldfinch)
- Vertrauliche Finanzdaten (2,3 Mio. Euro)

## 1.2 Die Dimension des Problems

| Risikokategorie | Beispiele | Konsequenzen |
|-----------------|-----------|--------------|
| **Personenbezogene Daten** | Kunden-, Mitarbeiter-, Partnernamen | DSGVO-Verstoß, Bußgelder bis 4% des Jahresumsatzes |
| **Geschäftsgeheimnisse** | Projektnamen, Strategien, Preise | Wettbewerbsnachteile, Vertrauensverlust |
| **Finanzdaten** | Umsätze, Budgets, Kontodaten | Compliance-Verstöße, Insiderhandel-Risiko |
| **Technische Daten** | Quellcode, Architekturen, Credentials | Sicherheitslücken, IP-Verlust |

## 1.3 Warum Verbote nicht funktionieren

Viele Unternehmen reagieren mit KI-Verboten. Die Realität zeigt:

- **Verbote werden umgangen:** Mitarbeiter nutzen private Geräte oder Mobilfunk
- **Produktivitätsverlust:** Unternehmen ohne KI-Nutzung fallen zurück
- **Frustration:** Talente wechseln zu moderneren Arbeitgebern
- **Keine Kontrolle:** Schatten-IT entzieht sich jeder Governance

**Die Lösung ist nicht Verhinderung, sondern kontrollierte Ermöglichung.**

---

# 2. Die Lösung: Anomyze

## 2.1 Funktionsprinzip

Anomyze arbeitet als intelligente Zwischenschicht zwischen Mitarbeiter und KI-Dienst:

```
┌─────────────────────────────────────────────────────────────────┐
│                        MITARBEITER                              │
│                                                                 │
│  "Schreibe eine E-Mail an Thomas Müller von der Ersten Bank    │
│   bezüglich Projekt Goldfinch..."                               │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     ANOMYZE BROWSER EXTENSION                   │
│                                                                 │
│  ✓ Erkennung: Thomas Müller → Person                           │
│  ✓ Erkennung: Erste Bank → Organisation                        │
│  ✓ Erkennung: Goldfinch → Projektname                          │
│  ✓ Erkennung: 2,3 Mio. Euro → Finanzdaten → BLOCKIERT          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        EXTERNE KI (ChatGPT)                     │
│                                                                 │
│  "Schreibe eine E-Mail an [PERSON_1] von der [ORG_1]           │
│   bezüglich Projekt [PROJEKT_1]..."                             │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     ANOMYZE RE-IDENTIFIKATION                   │
│                                                                 │
│  Antwort der KI mit Platzhaltern wird zurück-übersetzt         │
│  [PERSON_1] → Thomas Müller                                     │
└─────────────────────────────────────────────────────────────────┘
```

## 2.2 Erkennungstechnologie

Anomyze verwendet ein dreistufiges KI-Erkennungssystem:

### Stufe 1: PII-Erkennung (Personal Identifiable Information)
- Spezialisiertes NER-Modell für deutsche Texte
- Erkennt: Namen, E-Mail-Adressen, Telefonnummern, Adressen, Geburtsdaten
- Optimiert für deutsche Namenskonventionen und Anreden

### Stufe 2: Organisations-Erkennung
- BERT-basiertes Named Entity Recognition
- Erkennt bekannte Unternehmen, Behörden, Institutionen
- Kontextbasierte Erkennung von Geschäftsbeziehungen

### Stufe 3: Anomalie-Erkennung (Perplexity-basiert)
- Erkennt unbekannte Firmennamen durch sprachliche Anomalien
- Identifiziert interne Projektnamen und Codenamen
- Findet auch nicht-offensichtliche sensible Begriffe

### Zusätzliche Muster-Erkennung
- IBAN und Kontonummern
- Kreditkartennummern
- Sozialversicherungsnummern
- Steuernummern
- Interne Referenznummern

## 2.3 Betriebsmodi

| Modus | Verhalten | Anwendungsfall |
|-------|-----------|----------------|
| **Anonymisieren** | Sensible Daten werden durch Platzhalter ersetzt | Standard für externe KI |
| **Blockieren** | Eingabe wird verhindert, Hinweis erscheint | Für Finanzdaten, Credentials |
| **Warnen** | Nutzer wird informiert, kann fortfahren | Für Grenzfälle |
| **Umleiten** | Verweis auf interne Alternative (z.B. Copilot) | Für genehmigte Tools |

---

# 3. Technische Architektur

*Dieser Abschnitt richtet sich primär an IT-Leiter und technische Entscheider.*

## 3.1 Architektur-Entscheidung: Warum ein Backend-Server notwendig ist

Eine zentrale Designentscheidung bei Anomyze betrifft die Verarbeitung: **Die ML-basierte Anonymisierung muss auf einem Backend-Server erfolgen** und kann nicht vollständig im Browser stattfinden.

### Technische Begründung

| Aspekt | Browser-Only | Server-Architektur |
|--------|--------------|-------------------|
| **Modellgröße** | ~2.5 GB müssten bei jedem Seitenaufruf geladen werden | Modelle einmal beim Server-Start geladen |
| **Runtime** | PyTorch/Transformers laufen nicht nativ im Browser | Volle Python-Umgebung verfügbar |
| **Performance** | WebAssembly/ONNX wäre 10-50x langsamer | GPU-Beschleunigung möglich |
| **Memory** | Browser haben ~2-4 GB Limit | Server mit 16+ GB RAM |
| **Wartung** | Modell-Updates an jeden Client | Zentrale Updates am Server |

### Hybrid-Ansatz für optimale Performance

Um Latenz zu minimieren, verwendet Anomyze einen zweistufigen Ansatz:

```
┌─────────────────────────────────────────────────────────────────┐
│                    BROWSER EXTENSION                            │
│                                                                 │
│  Stufe 1: Lokale Regex-Erkennung (sofort, <10ms)               │
│  • E-Mail-Adressen                                              │
│  • IBAN, Kontonummern                                           │
│  • Telefonnummern                                               │
│  • Bekannte Patterns (Herr/Frau + Name)                        │
│                                                                 │
│  → 60-80% der sensiblen Daten werden sofort erkannt            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ Falls komplexe Erkennung nötig
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    ANOMYZE SERVER (On-Premise)                  │
│                                                                 │
│  Stufe 2: ML-basierte Erkennung (200-500ms)                    │
│  • Unbekannte Personennamen                                     │
│  • Firmennamen ohne Suffix (GmbH, AG)                          │
│  • Projektnamen, Codenamen                                      │
│  • Kontextbasierte Anomalien                                    │
└─────────────────────────────────────────────────────────────────┘
```

### Fallback-Strategien

| Szenario | Verhalten |
|----------|-----------|
| **Server nicht erreichbar** | Nur Regex-Erkennung aktiv, Warnung an Nutzer |
| **Hohe Latenz (>2s)** | Lokale Erkennung + asynchrone Server-Prüfung |
| **Server-Fehler** | Retry mit Exponential Backoff, lokaler Fallback |
| **Wartungsfenster** | Graceful Degradation auf Regex-Only |

## 3.2 Systemübersicht

```
┌─────────────────────────────────────────────────────────────────┐
│                      UNTERNEHMENSNETZWERK                       │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              ANOMYZE API SERVER (Docker)                 │   │
│  │                                                          │   │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐    │   │
│  │  │ FastAPI      │ │ ML-Modelle   │ │ Config       │    │   │
│  │  │ Endpoints    │ │ (lokal)      │ │ Management   │    │   │
│  │  └──────────────┘ └──────────────┘ └──────────────┘    │   │
│  │                                                          │   │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐    │   │
│  │  │ Redis Cache  │ │ Prometheus   │ │ Admin UI     │    │   │
│  │  │ (optional)   │ │ Metrics      │ │ (React)      │    │   │
│  │  └──────────────┘ └──────────────┘ └──────────────┘    │   │
│  │                                                          │   │
│  │  Ressourcen: 16GB RAM, 4+ CPU Cores, GPU empfohlen      │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              ▲                                  │
│                              │ HTTPS (intern)                   │
│                              ▼                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              BROWSER EXTENSIONS                          │   │
│  │                                                          │   │
│  │  Chrome │ Edge │ Firefox                                 │   │
│  │  • Manifest V3 kompatibel                                │   │
│  │  • Lokale Regex-Engine                                   │   │
│  │  • Zentrale Verteilung via GPO/MDM                      │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ Anonymisierte Anfragen
                              ▼
                    ┌───────────────────┐
                    │   Externe KI      │
                    │   (ChatGPT etc.)  │
                    └───────────────────┘
```

## 3.3 Komponenten

### Anomyze API Server

| Eigenschaft | Spezifikation |
|-------------|---------------|
| **Framework** | FastAPI (Python 3.11+) |
| **Deployment** | Docker Container / Kubernetes |
| **ML-Runtime** | PyTorch 2.x mit MPS/CUDA/CPU Support |
| **Modellgröße** | ~2.5 GB (einmalig beim Start geladen) |
| **Latenz** | 200-500ms pro Anfrage (GPU), 500-1500ms (CPU) |
| **Durchsatz** | ~50-100 req/s (GPU), ~10-20 req/s (CPU) |
| **Skalierung** | Horizontal via Load Balancer |
| **Cache** | Redis für häufige Patterns (optional) |

### API Endpoints

```
POST /api/v1/anonymize
    Body: { "text": "...", "options": {...} }
    Response: {
        "anonymized": "...",
        "mapping": {...},
        "entities": [...],
        "processing_time_ms": 234
    }

POST /api/v1/check
    Body: { "text": "..." }
    Response: {
        "allowed": bool,
        "blocked_reason": "...",
        "redirect_url": "...",
        "entities_found": [...]
    }

GET /api/v1/config
    Response: { "rules": [...], "blocked_domains": [...], ... }

GET /api/v1/health
    Response: { "status": "healthy", "models_loaded": true, "uptime": ... }

POST /api/v1/feedback
    Body: { "text": "...", "correction": "...", "entity_id": "..." }
    → Für kontinuierliche Verbesserung
```

### Browser Extension

| Feature | Beschreibung |
|---------|--------------|
| **Content Script** | Überwacht Texteingaben auf konfigurierten Seiten |
| **Lokale Regex-Engine** | Sofortige Erkennung von E-Mails, IBANs, Telefonnummern |
| **Service Worker** | Kommunikation mit Anomyze API |
| **Popup UI** | Status, An/Aus, aktuelle Erkennungen |
| **Options Page** | Benutzereinstellungen |
| **Enterprise Policies** | Konfiguration via GPO/MDM |
| **Offline-Modus** | Regex-Only wenn Server nicht erreichbar |

## 3.4 Deployment-Optionen

### Option A: On-Premise (empfohlen für Enterprises)
- Volle Datenkontrolle – Text verlässt nie das Unternehmensnetzwerk
- Docker/Kubernetes Deployment
- Integration in bestehende Infrastruktur
- GPU-Server für beste Performance

### Option B: Private Cloud
- Deployment in unternehmenseigener Cloud (Azure, AWS, GCP)
- Skalierbarkeit nach Bedarf
- VPN-Anbindung an Unternehmensnetz
- Managed Kubernetes (AKS, EKS, GKE)

### Option C: Managed Service (geplant)
- Gehostete Lösung durch Anomyze
- Datenverarbeitung in EU-Rechenzentren
- SLA-garantierte Verfügbarkeit
- Kein Server-Setup für Kunden nötig

## 3.5 Integration

### Active Directory / Entra ID
- SSO-Authentifizierung (SAML, OIDC)
- Gruppenbasierte Regelzuweisung
- Automatische Lizenzierung

### SIEM Integration
- Logging aller Anonymisierungsvorgänge (konfigurierbar)
- Alerts bei Policy-Verstößen
- Compliance-Reporting
- Unterstützte Formate: Syslog, JSON, CEF

### MDM/GPO
- Zentrale Extension-Verteilung
- Konfiguration ohne Benutzerinteraktion
- Erzwungene Aktivierung

### Proxy/Firewall
- Funktioniert hinter Corporate Proxies
- Certificate Pinning optional
- Whitelist: Nur interne API-Kommunikation

---

# 4. Datenschutz und Compliance

*Dieser Abschnitt richtet sich primär an Datenschutzbeauftragte und CISOs.*

## 4.1 DSGVO-Konformität

Anomyze wurde nach dem Prinzip **Privacy by Design** entwickelt:

| DSGVO-Anforderung | Anomyze-Umsetzung |
|-------------------|-------------------|
| **Art. 5 - Datenminimierung** | Nur anonymisierte Daten werden an Dritte übertragen |
| **Art. 25 - Privacy by Design** | Datenschutz ist Kernfunktion, nicht Zusatz |
| **Art. 32 - Sicherheit** | Verschlüsselung, Zugriffskontrolle, Audit-Logs |
| **Art. 28 - Auftragsverarbeitung** | Bei On-Premise: keine Auftragsverarbeitung nötig |
| **Art. 35 - DSFA** | Risikobewertung wird durch Anonymisierung obsolet |

## 4.2 Datenflüsse

### Ohne Anomyze
```
Mitarbeiter → ChatGPT (USA)
              ↓
        Personenbezogene Daten
        werden in USA verarbeitet
              ↓
        DSGVO-Verstoß möglich
```

### Mit Anomyze
```
Mitarbeiter → Anomyze (On-Premise) → ChatGPT (USA)
                    ↓                      ↓
              Verarbeitung im          Nur anonyme
              Unternehmen              Platzhalter
                    ↓
              Kein Transfer von
              personenbezogenen Daten
```

## 4.3 Verarbeitete Datenkategorien

| Kategorie | Behandlung | Rechtsgrundlage |
|-----------|------------|-----------------|
| Eingabetext | Temporär (nur während Verarbeitung, max. 30s) | Berechtigtes Interesse (Art. 6 Abs. 1 lit. f) |
| Mapping-Tabelle | Nur im Browser (Session Storage), nie am Server | Keine Speicherung |
| Nutzungsstatistiken | Aggregiert, pseudonymisiert, opt-out möglich | Berechtigtes Interesse |
| Audit-Logs | Konfigurierbar: nur Metadaten oder vollständig | Compliance-Anforderungen |

## 4.4 Arbeitsrechtliche Aspekte (Betriebsrat)

**WICHTIG für Deutschland und Österreich:**

Anomyze kann als Werkzeug zur Verhaltens- oder Leistungskontrolle interpretiert werden, wenn:
- Individuelle Nutzungsdaten geloggt werden
- Mitarbeiter identifizierbar sind
- Die Logs für Performance-Bewertung verwendet werden könnten

### Empfohlene Maßnahmen

| Maßnahme | Beschreibung |
|----------|--------------|
| **Betriebsvereinbarung** | Frühzeitige Einbindung des Betriebsrats |
| **Anonyme Logs** | Nur aggregierte Statistiken, keine Benutzer-IDs |
| **Opt-out Rechte** | Mitarbeiter können Logging für sich deaktivieren |
| **Zweckbindung** | Logs nur für Security/Compliance, nie für Performance |
| **Transparenz** | Mitarbeiter werden über Funktionsweise informiert |

### Konfigurationsoptionen

```yaml
logging:
  user_identification: false  # Keine Benutzer-IDs in Logs
  log_content: false          # Kein Originaltext in Logs
  log_entities: true          # Nur Entitäts-Typen, nicht Werte
  retention_days: 30          # Automatische Löschung
  access_restricted_to:
    - security-team
    - compliance-team
```

## 4.5 Technische Datenschutzmaßnahmen

- **Keine persistente Speicherung** von Originaltexten am Server
- **Mapping nur clientseitig** im Browser Session Storage
- **TLS 1.3** für alle Verbindungen
- **API-Authentifizierung** via Token/SSO
- **Automatische Löschung** von Verarbeitungsdaten nach 30 Sekunden
- **Audit-Trail** für Compliance-Nachweise (konfigurierbar)
- **Verschlüsselung at Rest** für alle Server-Daten

## 4.6 Zertifizierungen und Standards

Anomyze orientiert sich an:
- ISO 27001 (Informationssicherheit)
- ISO 27701 (Datenschutz-Management)
- BSI C5 (Cloud-Sicherheit)
- SOC 2 Type II (Service Organisation Controls)

*Hinweis: Formale Zertifizierungen sind für zukünftige Versionen geplant.*

---

# 5. Sicherheitsarchitektur

*Dieser Abschnitt richtet sich an CISOs und Security-Teams.*

## 5.1 Bedrohungsmodell

| Bedrohung | Risiko | Gegenmaßnahme |
|-----------|--------|---------------|
| **Man-in-the-Middle** | Abfangen der Kommunikation | TLS 1.3, Certificate Pinning |
| **Extension Tampering** | Manipulierte Extension | Code Signing, Integrity Checks |
| **API Missbrauch** | Unbefugte API-Nutzung | Token-Auth, Rate Limiting |
| **Server Compromise** | Zugriff auf Modelle/Logs | Isolation, minimale Logs |
| **Reverse Engineering** | Analyse der Erkennungslogik | Obfuscation, Server-side Logic |
| **Denial of Service** | Überlastung des Servers | Rate Limiting, Auto-Scaling |

## 5.2 Authentifizierung und Autorisierung

```
┌─────────────────────────────────────────────────────────────────┐
│                    AUTHENTIFIZIERUNGS-FLOW                      │
│                                                                 │
│  1. User öffnet Browser                                         │
│  2. Extension prüft: Gültiges Enterprise-Token vorhanden?       │
│     └── Nein: SSO-Redirect zu Entra ID / ADFS                  │
│     └── Ja: Token validieren via API                           │
│  3. API prüft: Token gültig + User in erlaubter Gruppe?        │
│     └── Nein: 401 Unauthorized                                 │
│     └── Ja: Anfrage verarbeiten                                │
│  4. Token-Refresh alle 60 Minuten (silent)                     │
└─────────────────────────────────────────────────────────────────┘
```

## 5.3 Rate Limiting

| Ebene | Limit | Aktion bei Überschreitung |
|-------|-------|---------------------------|
| Pro Benutzer | 100 req/min | 429 + Backoff |
| Pro Extension | 1000 req/min | 429 + Alert |
| Pro IP | 5000 req/min | Temporary Block |
| Global | 10000 req/min | Graceful Degradation |

## 5.4 Incident Response

Bei Sicherheitsvorfällen:
1. **Automatische Alerts** an Security-Team
2. **Automatisches Blocking** bei Anomalien
3. **Forensic Logs** für Analyse (DSGVO-konform)
4. **Kill Switch** zum sofortigen Deaktivieren aller Extensions

---

# 6. Browser Extension im Detail

## 6.1 Funktionsweise

Die Browser Extension ist das Herzstück der Benutzererfahrung:

### Automatische Erkennung
Die Extension erkennt automatisch Eingabefelder auf konfigurierten Seiten:
- chat.openai.com (ChatGPT)
- gemini.google.com (Google Gemini)
- claude.ai (Anthropic Claude)
- Weitere konfigurierbar

### Echtzeit-Verarbeitung
```
1. Benutzer tippt in Textfeld
2. Bei Absenden: Extension fängt Eingabe ab
3. Lokale Regex-Prüfung (sofort)
4. Falls nötig: Server-Anfrage (async)
5. Anonymisierter Text ersetzt Original
6. Anfrage geht an KI-Dienst
7. Antwort wird re-identifiziert
```

### Latenz-Optimierung

| Erkennungsart | Latenz | Verfügbarkeit |
|---------------|--------|---------------|
| Regex (lokal) | <10ms | Immer |
| ML-Server | 200-500ms | Server erreichbar |
| Kombiniert | 200-500ms | Server erreichbar |
| Fallback | <10ms | Server nicht erreichbar |

### Benutzeroberfläche

```
┌─────────────────────────────────────┐
│ 🛡️ Anomyze                    [An] │
├─────────────────────────────────────┤
│                                     │
│ Status: Aktiv ✓                     │
│ Server: Verbunden (45ms)            │
│                                     │
│ Letzte Erkennung:                   │
│ ┌─────────────────────────────────┐ │
│ │ Thomas Müller    → [PERSON_1]  │ │
│ │ Erste Bank       → [ORG_1]     │ │
│ │ Projekt Alpha    → [PROJEKT_1] │ │
│ └─────────────────────────────────┘ │
│                                     │
│ [Korrektur melden] [Whitelist]     │
│                                     │
├─────────────────────────────────────┤
│ Diese Seite: Anonymisierung aktiv  │
│ ⚙️ Einstellungen                    │
└─────────────────────────────────────┘
```

### Feedback-Loop

Nutzer können Fehlerkennungen melden:
- **False Positive**: "Küche" wurde fälschlich als Firma erkannt
- **False Negative**: Firmenname wurde nicht erkannt

Diese Meldungen werden (anonymisiert) zur Verbesserung der Erkennung verwendet.

## 6.2 Administrations-Panel

IT-Administratoren erhalten Zugriff auf ein zentrales Management-Interface:

### Regelkonfiguration

```yaml
rules:
  - name: "Finanzdaten blockieren"
    pattern: "IBAN|Kreditkarte|Kontonummer"
    action: "block"
    message: "Finanzdaten dürfen nicht an externe KI übertragen werden."

  - name: "Personennamen anonymisieren"
    entity_type: "PER"
    action: "anonymize"

  - name: "Zu Copilot umleiten"
    domains: ["chat.openai.com", "gemini.google.com"]
    action: "redirect"
    target: "https://copilot.microsoft.com"
    message: "Bitte nutzen Sie den unternehmensinternen Copilot."

  - name: "Interne Projektnamen blockieren"
    custom_list: ["Goldfinch", "Phoenix", "Titan"]
    action: "block"
    message: "Interne Projektnamen dürfen nicht extern verwendet werden."
```

### Domain-Management

| Kategorie | Beispiele | Standardverhalten |
|-----------|-----------|-------------------|
| **Blockiert** | - | Keine Eingabe möglich |
| **Anonymisiert** | chat.openai.com, claude.ai | Anonymisierung aktiv |
| **Erlaubt** | copilot.microsoft.com | Keine Verarbeitung |
| **Intern** | intranet.firma.de | Extension inaktiv |

### Benutzergruppen

- **Standard-Mitarbeiter**: Volle Anonymisierung
- **Entwickler**: Erweiterte Whitelist für Code-Plattformen
- **Management**: Zusätzliche Warnung bei Finanzdaten
- **Datenschutz-Team**: Vollständiger Audit-Zugriff

## 6.3 Deployment

### Chrome (via Google Admin Console)
```
1. Extension in Chrome Web Store (private/unlisted)
2. Erzwungene Installation via Policy
3. Konfiguration via managed_schema.json
```

### Edge (via Microsoft Endpoint Manager)
```
1. Extension-Paket erstellen
2. Via Intune verteilen
3. Konfiguration via ADMX-Templates
```

### Firefox (via Group Policy)
```
1. XPI-Datei signieren
2. Via GPO installieren
3. Konfiguration via policies.json
```

---

# 7. Marktumfeld und Differenzierung

## 7.1 Konkurrierende Lösungen

| Lösung | Typ | Stärken | Schwächen |
|--------|-----|---------|-----------|
| **Microsoft Presidio** | Open Source | Kostenlos, erweiterbar | Keine Browser-Integration, nur Python |
| **Private AI** | SaaS | Einfache Integration | Daten gehen in Cloud, teuer |
| **Nightfall AI** | SaaS | Breite Integration | US-Cloud, kein On-Premise |
| **BigID** | Enterprise | Umfassende DLP-Suite | Sehr teuer, komplex |
| **Manuell** | Prozess | Kostenfrei | Nicht skalierbar, fehleranfällig |

## 7.2 Anomyze Differenzierung

| Merkmal | Anomyze | Wettbewerb |
|---------|---------|------------|
| **On-Premise möglich** | ✓ Vollständig | Meist nur Cloud |
| **Deutsche Sprache** | ✓ Optimiert | Oft nur Englisch |
| **Browser-Integration** | ✓ Native Extension | API-only |
| **Echtzeit** | ✓ <500ms | Oft Batch |
| **Perplexity-Detection** | ✓ Einzigartig | Standard NER |
| **Preis** | Wettbewerbsfähig | Oft >$50k/Jahr |

## 7.3 Open Source Basis

Anomyze basiert auf bewährten Open Source Komponenten:

| Komponente | Lizenz | Kommerzielle Nutzung |
|------------|--------|---------------------|
| PyTorch | BSD | ✓ Erlaubt |
| Transformers (HuggingFace) | Apache 2.0 | ✓ Erlaubt |
| FastAPI | MIT | ✓ Erlaubt |
| dslim/bert-base-NER | Apache 2.0 | ✓ Erlaubt |
| dbmdz/bert-base-german-cased | MIT | ✓ Erlaubt |

*Hinweis: Die Lizenzen der verwendeten Modelle wurden geprüft und erlauben kommerzielle Nutzung.*

---

# 8. Business Case

*Dieser Abschnitt richtet sich primär an Management und Entscheider.*

## 8.1 Kosten ohne Anomyze

### Szenario: DSGVO-Verstoß durch KI-Nutzung

| Kostenposition | Betrag |
|----------------|--------|
| Bußgeld (4% Jahresumsatz bei 50 Mio.) | bis zu 2.000.000 € |
| Rechtsberatung und Verfahren | 50.000 - 200.000 € |
| Reputationsschaden | nicht quantifizierbar |
| Kundenabwanderung | variabel |

### Szenario: Datenleck durch KI-Eingabe

| Kostenposition | Betrag |
|----------------|--------|
| Incident Response | 20.000 - 100.000 € |
| Benachrichtigung Betroffener | 10.000 - 50.000 € |
| PR-Krisenmanagement | 30.000 - 150.000 € |
| Vertrauensverlust bei Kunden | nicht quantifizierbar |

## 8.2 Kosten von KI-Verboten

| Faktor | Auswirkung |
|--------|------------|
| Produktivitätsverlust | 10-30% bei Wissensarbeitern |
| Wettbewerbsnachteil | Konkurrenz nutzt KI effektiver |
| Mitarbeiterfluktuation | Top-Talente suchen moderne Arbeitgeber |
| Schatten-IT | Unkontrollierte Nutzung privater Geräte |

## 8.3 Wertbeitrag von Anomyze

### Quantifizierbare Vorteile

| Vorteil | Einsparung/Nutzen |
|---------|-------------------|
| Vermiedene Bußgelder | bis zu 2.000.000 € |
| Erhaltene Produktivität | 15-25% Effizienzsteigerung |
| Reduzierte Compliance-Kosten | 50.000 € p.a. |
| Vermiedene Incident-Kosten | 100.000 € pro vermiedenem Vorfall |

### Strategische Vorteile

- **Wettbewerbsfähigkeit**: KI-Nutzung ohne Risiko
- **Employer Branding**: Moderne, sichere Arbeitsumgebung
- **Governance**: Kontrolle über KI-Nutzung im Unternehmen
- **Audit-Readiness**: Nachweisbare Datenschutzmaßnahmen

## 8.4 Investitionsübersicht

| Komponente | Einmalig | Laufend (p.a.) |
|------------|----------|----------------|
| Lizenz (pro Benutzer) | - | individuell |
| Implementation | nach Aufwand | - |
| Schulung | nach Aufwand | - |
| Support | - | inkludiert |

*Konkrete Preise auf Anfrage.*

---

# 9. Roadmap

## Phase 1: Core Platform (verfügbar) ✓
- [x] Anonymisierungs-Engine
- [x] Deutsche Sprachunterstützung
- [x] CLI-Tool für Batch-Verarbeitung
- [x] Lokale Verarbeitung (On-Premise)

## Phase 2: API & Extension (in Entwicklung)
- [ ] FastAPI Server mit Docker-Deployment
- [ ] Chrome Extension MVP
- [ ] Edge Extension
- [ ] Admin-Panel (Basic)

## Phase 3: Enterprise Features (geplant)
- [ ] Active Directory / Entra ID Integration
- [ ] SIEM-Anbindung
- [ ] Multi-Sprach-Support (EN, FR, ES)
- [ ] Custom-Modell-Training
- [ ] Erweiterte Analytics

## Phase 4: Ecosystem (Vision)
- [ ] Outlook/Office Add-ins
- [ ] Slack/Teams Integration
- [ ] Mobile Apps (iOS/Android)
- [ ] KI-gestützte Regel-Empfehlungen
- [ ] Managed Cloud Service

---

# 10. Zusammenfassung

Die Nutzung von KI-Tools durch Mitarbeiter ist Realität. Die Frage ist nicht ob, sondern wie Unternehmen damit umgehen.

**Anomyze bietet den dritten Weg:**

Nicht Verbot. Nicht Ignorieren. Sondern **kontrollierte Ermöglichung**.

Mit Anomyze können Unternehmen:
- ✓ Die Produktivitätsvorteile von KI nutzen
- ✓ Datenschutz und Compliance sicherstellen
- ✓ Volle Kontrolle über den KI-Einsatz behalten
- ✓ Mitarbeiter befähigen statt einschränken

**Der nächste Schritt:**

Kontaktieren Sie uns für eine Demo oder einen Proof-of-Concept in Ihrer Umgebung.

---

# Kontakt

**Anomyze**

E-Mail: [kontakt@anomyze.io]
Web: [www.anomyze.io]

---

*Dieses Dokument wurde mit Anomyze erstellt. Alle genannten Personennamen und Unternehmen in Beispielen sind fiktiv.*

**Version 1.1 | Januar 2025**

---

# Anhang A: Technische Spezifikationen

## Hardware-Anforderungen Server

| Konfiguration | CPU | RAM | GPU | Nutzer |
|---------------|-----|-----|-----|--------|
| **Minimal** | 4 Cores | 8 GB | - | bis 50 |
| **Standard** | 8 Cores | 16 GB | - | bis 200 |
| **Performance** | 8 Cores | 32 GB | NVIDIA T4 | bis 500 |
| **Enterprise** | 16 Cores | 64 GB | NVIDIA A10 | 500+ |

## Software-Anforderungen

- Docker 20.10+ oder Kubernetes 1.24+
- HTTPS-Zertifikat (intern oder öffentlich)
- Outbound: Nur zu konfigurierten KI-Diensten
- Inbound: Nur von internen Clients

## Netzwerk-Ports

| Port | Protokoll | Zweck |
|------|-----------|-------|
| 443 | HTTPS | API-Kommunikation |
| 8080 | HTTP | Health Checks (intern) |
| 9090 | HTTP | Prometheus Metrics (intern) |
