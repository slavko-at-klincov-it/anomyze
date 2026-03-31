# Anomyze

**Souveräne KI-Anonymisierungsschicht für die österreichische Bundesverwaltung**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)

[anomyze.it](https://anomyze.it)

---

Anomyze ist der **Output-Filter** der "Public AI"-Initiative. Die KI-Tools (GovGPT, ELAK-KI, KAPA) arbeiten intern mit den vollen Daten — sie brauchen PII um zu funktionieren. Anomyze prüft und filtert den **Output**, bevor er das System verlässt: Veröffentlichung auf data.gv.at, parlamentarische Antworten, weitergeleitete Berichte.

## Features

- **3-Stufen-Pipeline:** Regex → NER → Perplexitäts-Anomalie-Erkennung
- **3 Ausgabe-Kanäle:** GovGPT (reversibel), IFG (irreversibel), KAPA (mit Audit-Trail)
- **Österreich-spezifisch:** SVNr, IBAN, KFZ-Kennzeichen, Aktenzahlen, Steuernummern, Verwaltungssprache
- **100% lokal:** Kein Cloud-Call, kein API-Call nach außen
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

## 3-Stufen-Pipeline

### Stufe 1: Regex (regex_layer.py)

Österreich-spezifische Muster mit höchster Präzision:

| Typ | Format | Beispiel |
|-----|--------|----------|
| SVNr | XXXX DDMMYY | 1234 140387 |
| IBAN | ATxx xxxx xxxx xxxx xxxx | AT61 1904 3002 3457 3201 |
| KFZ | Bezirk-Ziffern-Buchstaben | W-34567B |
| Aktenzahl | GZ/AZ/Zl. + Kürzel | GZ BMI-2024/0815 |
| Geburtsdatum | DD.MM.YYYY | 14.03.1987 |
| Telefon | +43, 0043, 06xx | +43 664 1234567 |
| Email | Standard | m.gruber@gmail.com |
| Steuernummer | XX-XXX/XXXX | 12-345/6789 |
| Reisepass | Kontext + A1234567 | Reisepass: P1234567 |
| Personalausweis | Kontext + ID | Personalausweis: AB123456CD |

### Stufe 2: NER (ner_layer.py)

HuggingFace Transformer-Modelle für Personennamen, Organisationen und Orte.

### Stufe 3: Kontext (context_layer.py)

Perplexitäts-basierte Anomalie-Erkennung: Erkennt unbekannte Firmennamen, die weder durch Regex noch NER abgedeckt sind.

## 3 Ausgabe-Kanäle

| Kanal | Zweck | Reversibel | Audit |
|-------|-------|-----------|-------|
| **GovGPT** | KI-generierte Antworten vor Weitergabe filtern | Ja (Mapping) | Nein |
| **IFG** | KI-Outputs vor Veröffentlichung auf data.gv.at schwärzen | Nein | Schwärzungsprotokoll |
| **KAPA** | KI-Rechercheergebnisse für parlamentarische Antworten filtern | Ja (Mapping) | Vollständiger Trail |

## API Endpunkte

| Methode | Pfad | Beschreibung |
|---------|------|--------------|
| POST | /api/v1/anonymize | Text anonymisieren |
| GET | /api/v1/health | Systemstatus |
| GET | /api/v1/mappings/{id} | Mapping abrufen |
| DELETE | /api/v1/mappings/{id} | Mapping löschen |
| GET | /api/v1/audit/{id} | Audit-Trail abrufen |

Detaillierte API-Dokumentation: [docs/api_reference.md](docs/api_reference.md)

## Architektur

Detaillierte Architektur-Dokumentation: [docs/architecture.md](docs/architecture.md)

## Konfiguration

Alle Einstellungen können über Umgebungsvariablen gesetzt werden:

```bash
ANOMYZE_DEVICE=cpu              # cpu, cuda, mps
ANOMYZE_DEFAULT_CHANNEL=govgpt  # govgpt, ifg, kapa
ANOMYZE_PII_THRESHOLD=0.7       # Konfidenz-Schwelle PII
ANOMYZE_KAPA_REVIEW_THRESHOLD=0.85  # Unter diesem Wert → manuelle Prüfung
```

## Lizenz

MIT
