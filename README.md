# Anomyze

**Souveräne KI-Anonymisierungsschicht für die österreichische Bundesverwaltung**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![CI](https://github.com/slavko-at-klincov-it/anomyze/actions/workflows/ci.yml/badge.svg)](https://github.com/slavko-at-klincov-it/anomyze/actions/workflows/ci.yml)

[anomyze.it](https://anomyze.it)

---

## Das Problem

Die österreichische Bundesverwaltung setzt zunehmend auf KI-Werkzeuge: GovGPT beantwortet Anfragen von Bediensteten, ELAK-KI unterstützt die Aktenverwaltung, KAPA recherchiert für parlamentarische Anfragen. Diese Werkzeuge arbeiten intern mit echten personenbezogenen Daten — Namen, Sozialversicherungsnummern, Adressen, Gesundheitsinformationen —, weil sie diese Daten brauchen, um sinnvolle Antworten zu geben.

**Das Risiko:** Wenn der KI-generierte Text das System verlässt — als Antwort an eine Bürgerin, als Veröffentlichung auf data.gv.at, als parlamentarische Beantwortung — können personenbezogene Daten unbeabsichtigt offengelegt werden. Das verletzt die DSGVO und untergräbt das Vertrauen in den Staat.

## Die Lösung

Anomyze ist der **letzte Filter** vor der Tür. Es prüft jeden KI-generierten Text automatisch auf personenbezogene Daten und ersetzt sie, bevor der Text das System verlässt. Die KI-Werkzeuge selbst müssen dafür nicht angepasst werden — Anomyze arbeitet als eigenständige Schicht dazwischen.

**Vorher** (KI-Output, ungefiltert):
> Sehr geehrte Frau Mag. Maria Huber, Ihre Sozialversicherungsnummer 1237 010180 und
> IBAN AT61 1904 3002 3457 3201 liegen dem Akt GZ 2024/4567-III/2 bei.
> Diagnose: F32.1 (mittelgradige depressive Episode).

**Nachher** (Anomyze-Output, gefiltert):
> Sehr geehrte Frau Mag. [PERSON_1], Ihre Sozialversicherungsnummer [SVNR_1] und
> IBAN [IBAN_1] liegen dem Akt [AKTENZAHL_1] bei.
> Diagnose: [GESUNDHEIT_1] (mittelgradige depressive Episode).

Anomyze erkennt dabei nicht nur offensichtliche Daten wie Namen und Kontonummern, sondern auch österreichisch-spezifische Formate (Sozialversicherungsnummern, KFZ-Kennzeichen, Firmenbuchnummern, Geschäftszahlen) und besonders sensible Kategorien wie Gesundheitsdaten oder Religionszugehörigkeit.

## Drei Kanäle fuer drei Anwendungsfälle

| Kanal | Einsatz | Verhalten |
|-------|---------|-----------|
| **GovGPT** | KI-Antworten an Bedienstete weiterleiten | Daten werden durch Platzhalter ersetzt. Berechtigte Personen können die Zuordnung einsehen ("wer ist PERSON_1?"). |
| **IFG** | KI-Ergebnisse auf data.gv.at veröffentlichen | Daten werden unwiderruflich geschwärzt. Niemand kann die Originaldaten rekonstruieren — Datenschutz by Design. |
| **KAPA** | Parlamentarische Anfragen beantworten | Wie GovGPT, aber mit vollständigem Prüfprotokoll: wann wurde was erkannt, mit welcher Sicherheit, wer hat geprüft. Unsichere Erkennungen werden zur manuellen Kontrolle markiert. |

## Warum Anomyze

- **100 % lokal.** Kein Datentransfer an Cloud-Dienste, keine externen API-Aufrufe. Alle Daten bleiben in der Infrastruktur der Behörde. Volle Datensouveränität.
- **Österreich-spezifisch.** Erkennt österreichische Sozialversicherungsnummern, UID-Nummern, KFZ-Kennzeichen mit Bezirkscodes, Geschäftszahlen, Gerichtsaktenzeichen, Firmenbuchnummern — Formate die generische Anonymisierungswerkzeuge nicht kennen.
- **DSGVO-konform.** Besonders sensible Daten (Gesundheit, Religion, Ethnie, politische Meinung) werden besonders geschützt — im IFG-Kanal nicht einmal die Kategorie öffentlich gemacht, im KAPA-Kanal zwingend zur manuellen Prüfung vorgelegt. Ein eingebautes Löschkonzept setzt das Recht auf Vergessenwerden (Art. 17) technisch um.
- **Prüfbar.** Ein mitgeliefertes Benchmark-Framework misst die Erkennungsqualität auf österreichischen Testdokumenten (Bescheide, Niederschriften, Ladungen). Automatische Regressionsprüfung stellt sicher, dass neue Versionen nicht schlechter erkennen als alte.
- **Manipulationssicher.** Versuche, personenbezogene Daten durch Unicode-Tricks, unsichtbare Zeichen oder Zeichenersetzungen an der Erkennung vorbeizuschmuggeln, werden automatisch neutralisiert.

---

## Der Gesamtprozess

Anomyze ist kein Einzelwerkzeug, sondern eine Schicht in einem durchgehend automatisierten Ablauf. Die Buergerin stellt eine Anfrage; alles Weitere — Identifikation, Datenbeschaffung, Dokumenterstellung, Anonymisierung — laeuft automatisch. Der Mensch kommt erst am Ende als Prüfinstanz.

```
Buergerin stellt Anfrage ueber Web-Portal
        |
        v
Automatische Identifikation (ID Austria)
Was wird angefragt? Welche Daten werden benoetigt?
        |
        v
Automatische Datenbeschaffung
Relevante Akten, Registerdaten, Bescheide, Gutachten
        |
        v
KI-Verarbeitung (GovGPT / ELAK-KI / KAPA)
Erstellt den Dokument-Entwurf auf Basis der gesammelten Daten
        |
        v
 +--------------+
 |   ANOMYZE    |   Automatische Anonymisierung
 +--------------+   Erkennung, Ersetzung, Risiko-Flagging,
        |           Audit-Trail, Qualitaetskontrolle
        v
Sachbearbeiterin wird benachrichtigt
"Ein Dokument wartet auf Ihre Freigabe."
        |
        v
Pruefung und Freigabe (Human-in-the-Loop)
Sachbearbeiterin prueft, klickt [Freigeben]
        |
        v
Dokument wird an die Buergerin zugestellt
```

**Der Mensch prueft, er erstellt nicht.** Die gesamte Kette laeuft automatisch. Der Mensch kontrolliert nur das Ergebnis — markierte Stellen, Warnungen bei sensiblen Daten, unsichere Erkennungen. Alles andere ist maschinell vorbereitet.

### Konkretes Beispiel: Auskunftsbegehren nach Informationsfreiheitsgesetz

| Zeitpunkt | Was passiert |
|-----------|-------------|
| 09:12 | Buergerin stellt Anfrage auf data.gv.at: "Auskunft zu GZ 2024/4567." |
| 09:12 | System erkennt: IFG-Anfrage, Ressort BMI, Geschaeftszahl bekannt. |
| 09:13 | Automatischer Abruf der Akte aus dem ELAK. 14 Dokumente, 23 Seiten. |
| 09:14 | KI erstellt Zusammenfassung. Enthaelt: 3 Namen, 2 Adressen, 1 SVNr, 1 Diagnose. |
| 09:14 | Anomyze anonymisiert. IFG-Kanal: unwiderrufliche Schwaerzung. Diagnose als besondere Kategorie markiert. |
| 09:15 | Dr. Koller erhaelt Benachrichtigung: "Dokument bereit zur Freigabe." |
| 09:22 | Dr. Koller prueft die Schwaerzungen, bestaetigt, klickt [Freigeben]. |
| 09:22 | Dokument wird an das MeinPostfach der Buergerin zugestellt. |

Gesamtdauer: **10 Minuten.** Davon manuell: 7 Minuten (Pruefung durch Dr. Koller).

Detaillierter Prozess mit Abgrenzung der Verantwortlichkeiten: [docs/end-to-end-process.md](docs/end-to-end-process.md)

---

## Technische Details

### Features

- **Mehrschichtige Detection-Pipeline:** Regex, NER-Ensemble (2 Transformer-Modelle + GLiNER Zero-Shot), Presidio-kompatible AT-Recognizer, Perplexitaets-Anomalie-Erkennung
- **Checksum-Validierung:** IBAN, SVNR und UID werden auf echte Prüfziffern validiert
- **Whitelist AT-Rechtstexte:** Gesetzestitel (ASVG, StGB, DSGVO) und Behördennamen (BMI, VfGH, ÖGK) werden von der Schwärzung ausgenommen
- **Ensemble-Merging:** Überlappende Erkennungen aus mehreren Schichten werden zusammengeführt
- **Entity-Resolver:** Varianten derselben Person ("Maria Gruber" und "Frau Gruber") werden verknüpft
- **Re-Identifikations-Schutz:** Erkennt Attribut-Kombinationen (Rolle + Beruf + Ort + Alter) die eine Person auch ohne Namen identifizierbar machen
- **Post-Anonymization Quality-Check:** Abschlusskontrolle auf durchgerutschte Datenreste
- **Observability:** Prometheus-Metriken, strukturiertes JSON-Logging, Latenz-Messung pro Verarbeitungsschritt
- **API-Hardening:** Zugriffsbegrenzung, Sicherheits-Header, Grössenprüfung
- **Model-Pinning:** Reproduzierbare Ergebnisse durch festgelegte Modellversionen
- **REST API:** Docker-ready, gehärtet (read-only Dateisystem, minimale Berechtigungen)
- **Deploy-Vorlagen:** Reverse-Proxy, Authentifizierung, automatische Datenlöschung und Backup in `deploy/`

## Quickstart

### Installation

```bash
pip install -e .                              # Kernpaket
pip install -e ".[api]"                       # + REST API (FastAPI + Uvicorn)
pip install -e ".[api,observability]"         # + Prometheus /metrics + structlog
pip install -e ".[api,observability,hardening]"  # + Rate-Limit + Security-Headers
pip install -e ".[dev]"                       # + Entwicklungstools (pytest, ruff, mypy)
```

Runtime-Dependencies: `torch`, `transformers<5.0`, `sentencepiece`, `python-stdnum`.

### CLI

```bash
# Datei anonymisieren (GovGPT-Kanal)
anomyze input.txt output.txt

# IFG-Kanal (irreversible Schwärzung)
anomyze input.txt output.txt --channel ifg

# KAPA-Kanal (mit Audit-Trail)
anomyze input.txt output.txt --channel kapa

# Interaktiver Modus
anomyze --interactive --channel govgpt
```

### Python Library

```python
from anomyze import PipelineOrchestrator

orch = PipelineOrchestrator()
orch.load_models()

# GovGPT: Reversible Platzhalter
result = orch.process("Maria Gruber, SVNr. 1234 140387", channel="govgpt")
print(result.text)     # [PERSON_1], SVNr. [SVNR_1]
print(result.mapping)  # {"[PERSON_1]": "Maria Gruber", "[SVNR_1]": "1234 140387"}

# IFG: Irreversible Schwärzung
result = orch.process("Maria Gruber, SVNr. 1234 140387", channel="ifg")
print(result.text)     # [GESCHWÄRZT:PERSON], SVNr. [GESCHWÄRZT:SVNR]

# KAPA: Mit Audit-Trail
result = orch.process("Maria Gruber, SVNr. 1234 140387", channel="kapa")
print(result.flagged_for_review)  # Entitäten unter Konfidenz-Schwelle
print(result.audit_entries)       # Vollständiger Audit-Trail
```

### REST API

```bash
# Server starten
uvicorn anomyze.api.main:app --host 0.0.0.0 --port 8000

# Anonymisieren
curl -X POST http://localhost:8000/api/v1/anonymize \
  -H "Content-Type: application/json" \
  -d '{"text": "Maria Gruber, SVNr. 1234 140387", "channel": "govgpt"}'

# Health Check
curl http://localhost:8000/api/v1/health
```

### Docker

```bash
# Production
docker compose up --build

# Lokaler Smoke-Test (nutzt Host-HF-Cache, Port 8001)
bash scripts/docker_smoke.sh
```

## Pipeline

```
KI-Tool (GovGPT / ELAK-KI / KAPA)
    ↓ KI-Output
Preprocessing
    ↓ fix_encoding + adversarial normalization
Stage 1: Regex (modular: email, phone, financial, documents, vehicles, addresses, names, dates)
Stage 2: NER-Ensemble
    ├─ PII-Modell (HuggingLil/pii-sensitive-ner-german)
    ├─ NER-Modell (Davlan/xlm-roberta-large-ner-hrl)
    └─ GLiNER Zero-Shot (urchade/gliner_large-v2.1, optional)
Stage 2c: Presidio-kompatible AT-Recognizer (mit Checksum-Validierung)
    └─ SVNR, IBAN, UID, BIC, KFZ, Firmenbuch, Reisepass, Führerschein, ZMR, Aktenzahl, Gerichtsaktenzeichen, ICD-10, AT-Namen
Ensemble-Merge (überlappende Spans + Konfidenz-Aggregation)
Whitelist-Filter (AT-Gesetzestitel + Behördennamen bleiben im Output)
Stage 3: Kontext/MLM (dbmdz/bert-base-german-cased)
    ├─ Perplexitäts-basierte Anomalie-Erkennung (unbekannte Firmen)
    └─ Quasi-Identifikator-Check (Rolle + Beruf + Verwandtschaft + Ort + Alter)
Entity-Resolver (verknüpft Varianten derselben Entität)
    ↓
Kanal-Auswahl (govgpt / ifg / kapa)
    ↓
Quality-Check (durchgerutschte PII-Reste flaggen)
    ↓
Gefilterter Output verlässt das System
```

## Erkannte PII-Typen

| Typ | Format | Quelle |
|-----|--------|--------|
| PERSON | Namen (mit/ohne Titel) | NER + AT-Namensliste + Phonetik |
| ORGANISATION | Firmennamen, Behörden | NER + Kontext-Perplexität |
| ORT | Wien, Graz | NER |
| ADRESSE | Straße Nr, PLZ Ort | Regex |
| EMAIL | Standard | Regex |
| IBAN | ATxx xxxx xxxx xxxx xxxx | Regex + AT-Recognizer |
| SVNR | XXXX DDMMYY | Regex + MOD-11-Prüfziffer (stdnum) |
| UID | ATU + 8 Ziffern | AT-Recognizer + MOD-11 (stdnum) |
| BIC | SWIFT-Code | AT-Recognizer + Land-Validierung |
| FÜHRERSCHEIN | 8-stellig (kontext-gesteuert) | AT-Recognizer |
| ZMR | 12-stellig (kontext-gesteuert) | AT-Recognizer |
| GERICHTSAKTENZAHL | 3 Ob 123/45 | AT-Recognizer |
| GESUNDHEIT (Art. 9) | ICD-10 Codes (F32.1 ...) | AT-Recognizer (kontext-gesteuert) |
| TELEFON | +43, 0043, 06xx | Regex |
| KFZ | Bezirkscode-Ziffern-Buchstaben | Regex + AT-Recognizer |
| AKTENZAHL | GZ/AZ/Zl. + Kürzel | Regex + AT-Recognizer |
| FIRMENBUCH | FN + 1-6 Ziffern + Prüfbuchstabe | AT-Recognizer |
| REISEPASS | 1 Buchstabe + 7 Ziffern | Regex (kontext-gesteuert) |
| PERSONALAUSWEIS | ID-Formate | Regex (kontext-gesteuert) |
| STEUERNUMMER | XX-XXX/XXXX | Regex |
| GEBURTSDATUM | DD.MM.YYYY | Regex |
| QUASI_ID | "der Beschwerdeführer aus Graz, geboren 1985" | Kontext (Kombinations-Check) |

## 3 Ausgabe-Kanäle

| Kanal | Zweck | Reversibel | Audit |
|-------|-------|-----------|-------|
| **GovGPT** | KI-generierte Antworten vor Weitergabe filtern | Ja (Mapping) | Nein |
| **IFG** | KI-Outputs vor Veröffentlichung auf data.gv.at schwärzen | Nein | Schwärzungsprotokoll |
| **KAPA** | KI-Rechercheergebnisse für parlamentarische Antworten filtern | Ja (Mapping) | Vollständiger Trail |

## API-Endpunkte

| Methode | Pfad | Beschreibung |
|---------|------|--------------|
| POST | /api/v1/anonymize | Text anonymisieren |
| GET | /api/v1/health | Systemstatus |
| GET | /api/v1/mappings/{document_id} | Mapping abrufen |
| DELETE | /api/v1/mappings/{document_id} | Mapping löschen |
| DELETE | /api/v1/documents/{document_id} | DSGVO Art. 17: Mapping + Audit |
| GET | /api/v1/audit/{document_id} | Audit-Trail abrufen |
| GET | /metrics | Prometheus-Metriken |

Detaillierte API-Dokumentation: [docs/api_reference.md](docs/api_reference.md)

## Benchmark-Framework

Anomyze enthält ein Benchmark-Framework zur Messung der Detection-Qualität auf annotierten Ground-Truth-Datensätzen:

```bash
# Synthetisches AT-PII-Dataset (25 Sätze)
python -m anomyze.benchmark benchmarks/datasets/synthetic_at.json

# Realistische AT-Dokumente (6 Bescheide / Anfragen / Protokolle)
python -m anomyze.benchmark benchmarks/datasets/realistic_at.json

# Mit MLM/GLiNER (langsamer, umfassender)
python -m anomyze.benchmark benchmarks/datasets/synthetic_at.json --with-mlm --with-gliner

# JSON-Report für CI
python -m anomyze.benchmark benchmarks/datasets/synthetic_at.json --json
```

Der Report zeigt Precision, Recall und F1 pro Kategorie sowie pro Detection-Layer (`regex`, `pii`, `org`, `presidio_compat`, `gliner`, `ensemble`, `perplexity`). Details: [benchmarks/README.md](benchmarks/README.md).

## Architektur

Detaillierte Architektur-Dokumentation: [docs/architecture.md](docs/architecture.md)

## Konfiguration

Alle Einstellungen können über Umgebungsvariablen gesetzt werden:

```bash
ANOMYZE_DEVICE=cpu              # cpu, cuda, mps
ANOMYZE_DEFAULT_CHANNEL=govgpt  # govgpt, ifg, kapa
ANOMYZE_PII_THRESHOLD=0.7       # Konfidenz-Schwelle PII-Modell
ANOMYZE_ORG_THRESHOLD=0.7       # Konfidenz-Schwelle NER/ORG-Modell
ANOMYZE_GLINER_THRESHOLD=0.4    # Konfidenz-Schwelle GLiNER
ANOMYZE_ANOMALY_THRESHOLD=0.5   # Finale Score-Schwelle
ANOMYZE_KAPA_REVIEW_THRESHOLD=0.85  # Unter diesem Wert → manuelle Prüfung
ANOMYZE_USE_GLINER=true         # GLiNER-Layer an/aus
ANOMYZE_ALWAYS_REVIEW_ART9=true # Art. 9 immer zur Prüfung flaggen (KAPA)
ANOMYZE_MAX_REQUEST_TEXT_CHARS=50000  # Max. Textlänge API
ANOMYZE_PII_MODEL_REVISION=     # HF Git-SHA für Reproduzierbarkeit
```

Vollständige ENV-Referenz: [deploy/env/anomyze.env.example](deploy/env/anomyze.env.example)

## Lizenz

MIT
