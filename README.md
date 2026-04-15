# Anomyze

**Souveräne KI-Anonymisierungsschicht für die österreichische Bundesverwaltung**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)

[anomyze.it](https://anomyze.it)

---

Anomyze ist der **Output-Filter** der "Public AI"-Initiative. Die KI-Tools (GovGPT, ELAK-KI, KAPA) arbeiten intern mit den vollen Daten — sie brauchen PII, um zu funktionieren. Anomyze prüft und filtert den **Output**, bevor er das System verlässt: Veröffentlichung auf data.gv.at, parlamentarische Antworten, weitergeleitete Berichte.

## Features

- **Mehrschichtige Detection-Pipeline:** Regex → NER-Ensemble (2 HF-Modelle + GLiNER Zero-Shot) → Presidio-kompatible AT-Recognizer → Perplexitäts-Anomalie-Erkennung
- **3 Ausgabe-Kanäle:** GovGPT (reversibel), IFG (irreversibel), KAPA (mit Audit-Trail)
- **Österreich-spezifisch:** Adressen, SVNr, IBAN, KFZ-Kennzeichen, Aktenzahlen, Firmenbuchnummern, Reisepass, Steuernummern, AT-Namensliste mit Kölner Phonetik
- **Ensemble-Merging:** Überlappende Detections aus mehreren Layern werden mit Konfidenz-Aggregation zusammengeführt
- **Entity-Resolver:** Varianten derselben Entität (z. B. "Maria Gruber" und "Frau Gruber") werden verknüpft
- **Quasi-Identifikator-Check:** Erkennt re-identifizierende Attribut-Kombinationen (Rolle + Ort + Alter)
- **Adversarial-Normalization:** Unicode-Homoglyphen, Zero-Width-Spaces und Leetspeak werden normalisiert, bevor Detection greift
- **Post-Anonymization Quality-Check:** Überprüft die finale Ausgabe auf durchgerutschte PII-Reste
- **Benchmark-Framework:** Precision / Recall / F1 pro Kategorie und pro Detection-Layer auf annotierten Ground-Truth-Datensätzen
- **100 % lokal:** Kein Cloud-Call, kein API-Call nach außen
- **REST API:** FastAPI-basiert, Docker-ready
- **DSGVO-konform:** Privacy by Default, irreversible Schwärzung für IFG
- **Human-in-the-Loop:** Unsichere Erkennungen werden zur manuellen Prüfung geflaggt (KAPA)

## Quickstart

### Installation

```bash
pip install -e .          # Kernpaket
pip install -e ".[api]"   # + REST API (FastAPI + Uvicorn)
pip install -e ".[dev]"   # + Entwicklungstools
```

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
docker-compose up --build
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
Stage 2c: Presidio-kompatible AT-Recognizer
    └─ SVNR, IBAN, KFZ, Firmenbuch, Reisepass, Aktenzahl, AT-Namen
Ensemble-Merge (überlappende Spans + Konfidenz-Aggregation)
Stage 3: Kontext/MLM (dbmdz/bert-base-german-cased)
    ├─ Perplexitäts-basierte Anomalie-Erkennung (unbekannte Firmen)
    └─ Quasi-Identifikator-Check (Rolle + Ort + Alter)
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
| SVNR | XXXX DDMMYY | Regex + Datumsvalidierung |
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
| GET | /api/v1/audit/{document_id} | Audit-Trail abrufen |

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
```

## Lizenz

MIT
