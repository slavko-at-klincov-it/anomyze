# Anomyze

**Intelligent PII Anonymizer for German Text**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)

[anomyze.it](https://anomyze.it)

---

Anomyze erkennt und anonymisiert personenbezogene Daten in deutschen Texten — inklusive Firmennamen, die kein anderes Tool findet.

## Das Problem

Standard-Anonymizer erkennen nur bekannte Entitäten aus Trainingsdaten. Lokale Firmennamen wie "Billa", "Hofer" oder "Merkur" werden übersehen.

## Die Lösung

Anomyze nutzt **Perplexity-basierte Anomalie-Erkennung**:

```
"Bei uns in der Küche gibt es Probleme"   → "Küche" ist erwartbar ✓
"Bei uns in der Billa gibt es Probleme"   → "Billa" ist unerwartet → Firma!
```

## Features

- **3-Schicht-Erkennung** — PII + NER + Anomalie-Detection
- **100% lokal** — Keine Cloud, keine API-Calls, DSGVO-konform
- **Findet unbekannte Firmen** — Durch Sprachmodell-Analyse
- **Python Package** — Einfache Integration in eigene Projekte
- **CLI Tool** — Batch-Verarbeitung von Dateien
- **Text-Glättung** — Optional: Transkripte mit lokalem LLM aufbereiten
- **Optimiert für Apple Silicon** — MPS-Beschleunigung auf M1/M2/M3

## Architektur

```
┌────────────────────────────────────────────────────────────┐
│  Layer 1: PII Model                                        │
│  → Namen, E-Mails, Telefonnummern, Geburtsdaten           │
├────────────────────────────────────────────────────────────┤
│  Layer 2: NER Model                                        │
│  → Bekannte Firmen, Orte, Personen                        │
├────────────────────────────────────────────────────────────┤
│  Layer 3: Perplexity Anomaly Detection                    │
│  → Unbekannte Firmen durch Sprachmodell-Analyse           │
└────────────────────────────────────────────────────────────┘
```

## Installation

### Als Package (empfohlen)

```bash
pip install anomyze
```

### Aus Source

```bash
git clone https://github.com/slavko-at-klincov-it/anomyze.git
cd anomyze
pip install -e .
```

### Voraussetzungen

- Python 3.10+
- ~2.5 GB Speicher für ML-Modelle (werden automatisch heruntergeladen)
- Optional: [Ollama](https://ollama.ai) für Text-Glättung

## Verwendung

### Als Python Library

```python
from anomyze import anonymize, load_models

# Modelle laden (einmalig)
pii, org, mlm = load_models()

# Text anonymisieren
result = anonymize(
    "Hallo, ich bin Thomas Müller von der Ersten Bank.",
    pii, org, mlm
)

print(result.text)
# → "Hallo, ich bin [PER_1] von der [ORG_1]."

print(result.mapping)
# → {"[PER_1]": "Thomas Müller", "[ORG_1]": "Ersten Bank"}
```

### Als CLI Tool

```bash
# Interaktiver Modus
anomyze --interactive

# Datei verarbeiten
anomyze input.txt output.txt

# Mit Text-Glättung (benötigt Ollama)
anomyze input.txt output.txt --smooth
```

### Ausgabe

```
Detected 3 entities:
  [PER         ] "Thomas Müller" (score: 0.86, source: pii)
  [ORG_DETECTED] "Ersten Bank" (score: 0.75, source: perplexity)
  [ORG_DETECTED] "Billa" (score: 0.95, source: perplexity)

ANONYMIZED TEXT:
Hallo, ich bin [PER_1] von der [ORG_1]. Bei [ORG_2] kaufe ich immer ein.
```

## API Reference

### `anonymize(text, pii_pipeline, org_pipeline, mlm_pipeline)`

Anonymisiert Text und gibt ein `AnonymizeResult` zurück.

```python
@dataclass
class AnonymizeResult:
    text: str                      # Anonymisierter Text
    mapping: Dict[str, str]        # Placeholder → Original
    entities: List[Dict]           # Alle erkannten Entitäten
    original_text: str             # Originaltext
```

### `load_models(device=None, verbose=True)`

Lädt alle ML-Modelle und gibt die Pipelines zurück.

```python
pii_pipeline, org_pipeline, mlm_pipeline = load_models()
```

### `Settings`

Konfiguration über Umgebungsvariablen oder programmatisch:

```python
from anomyze import Settings, configure

settings = Settings(
    pii_threshold=0.7,      # Mindest-Score für PII
    org_threshold=0.7,      # Mindest-Score für ORG
    anomaly_threshold=0.5,  # Mindest-Score für Anomalien
    device="mps",           # Oder "cuda", "cpu"
)
configure(settings)
```

## Erkannte Entitäten

| Kategorie | Typen |
|-----------|-------|
| **Personen** | GIVENNAME, SURNAME, PER |
| **Kontakt** | EMAIL, TELEPHONENUM |
| **Dokumente** | IDCARDNUM, DATEOFBIRTH |
| **Orte** | LOC, STREET |
| **Organisationen** | ORG, ORG_DETECTED |

## Kontext-Patterns

Anomyze erkennt Firmen in diesen Kontexten:

| Muster | Beispiel |
|--------|----------|
| "bei uns in der X" | "Bei uns in der **Billa**..." |
| "arbeite bei X" | "Ich arbeite bei **Hofer**" |
| "Kunde X" | "Unser Kunde **Merkur**" |
| "X Bank" | "...von der **Ersten Bank**" |
| "X Versicherung" | "...bei der **Allianz Versicherung**" |

## Performance

Getestet auf MacBook Pro M3 Pro:

| Text | Zeit |
|------|------|
| < 500 Zeichen | ~2 Sek |
| 1-5 KB | ~10 Sek |
| > 10 KB | ~30 Sek |

## Verwandte Projekte

- **[Anomyze Extension](https://github.com/slavko-at-klincov-it/anomyze-extension)** — Browser Extension + API Server für Echtzeit-Anonymisierung

## Dokumentation

- **[Whitepaper](docs/whitepaper-anomyze.md)** — Ausführliche Dokumentation für IT-Entscheider
- **[Projekt-Roadmap](docs/PROJECT-TODO.md)** — Entwicklungsplan

## Lizenz

MIT License

Die verwendeten ML-Modelle haben eigene Lizenzen:
- [dslim/bert-base-NER](https://huggingface.co/dslim/bert-base-NER) — Apache 2.0
- [dbmdz/bert-base-german-cased](https://huggingface.co/dbmdz/bert-base-german-cased) — MIT

---

**Made with precision in Austria** 🇦🇹
