# Anomyze

**Intelligent PII Anonymizer for German Text**

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

### Voraussetzungen

- Python 3.10+
- macOS (Apple Silicon) oder Linux/Windows mit CUDA

### Setup

```bash
# Repository klonen
git clone https://github.com/your-username/anomyze.git
cd anomyze

# Dependencies installieren
pip install -r requirements.txt
```

### Erster Start

Beim ersten Start werden ~2.5 GB Modelle heruntergeladen:

| Modell | Größe | Funktion |
|--------|-------|----------|
| PII-NER German | ~1.1 GB | Persönliche Daten |
| BERT-NER | ~400 MB | Organisationen |
| German BERT | ~400 MB | Anomalie-Erkennung |

## Verwendung

### Interaktiver Modus

```bash
python anomyze.py --interactive
```

```
[Paste text, then type END]
Hallo, ich bin Thomas Müller von der Ersten Bank.
Bei uns in der Billa kaufe ich immer ein.
END

Detected 3 entities:
  [PER         ] "Thomas Müller" (score: 0.86, source: org)
  [ORG_DETECTED] "Ersten Bank" (score: 0.75, source: perplexity)
  [ORG_DETECTED] "Billa" (score: 0.95, source: perplexity)
```

### Datei-Modus

```bash
# Ausgabe im Terminal
python anomyze.py transcript.txt

# Mit Ausgabedatei
python anomyze.py transcript.txt anonymized.txt
```

### Ausgabe

1. **Anonymisierter Text** — PII durch Platzhalter ersetzt
2. **Mapping-Datei** (`.mapping.json`) — Zum späteren Re-Mapping

```json
{
  "[PER_1]": "Thomas Müller",
  "[ORG_DETECTED_1]": "Ersten Bank",
  "[ORG_DETECTED_2]": "Billa"
}
```

## Erkannte Entitäten

| Kategorie | Typen |
|-----------|-------|
| **Personen** | GIVENNAME, SURNAME, PER |
| **Kontakt** | USERNAME (E-Mail), TELEPHONENUM |
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
| "zur X gewechselt" | "...zur **Siemens** gewechselt" |

## Workflow

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Transkript     │────▶│    Anomyze      │────▶│  Anonymisiert   │
│  (sensibel)     │     │    (lokal)      │     │  (sicher)       │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                                        │
                        ┌───────────────────────────────┘
                        ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Fertiges       │◀────│  Re-Mapping     │◀────│  LLM Summary    │
│  Dokument       │     │  (lokal)        │     │  (Cloud/API)    │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

1. **Lokal**: Transkript durch Anomyze anonymisieren
2. **Lokal**: Mapping-Datei sicher aufbewahren
3. **Cloud**: Anonymisierten Text an LLM für Zusammenfassung
4. **Lokal**: Platzhalter durch echte Namen ersetzen

## Performance

Getestet auf MacBook Pro M3 Pro:

| Text | Zeit |
|------|------|
| < 500 Zeichen | ~2 Sek |
| 1-5 KB | ~10 Sek |
| > 10 KB | ~30 Sek |

## Bekannte Einschränkungen

- **Deutsch only** — Optimiert für deutsche Texte
- **Kontextabhängig** — "Hofer" als Name vs. Supermarkt nicht unterscheidbar
- **Manuelle Prüfung** — Automatische Erkennung ist nie 100%

## Lizenz

MIT License

Die verwendeten Modelle haben eigene Lizenzen:
- [HuggingLil/pii-sensitive-ner-german](https://huggingface.co/HuggingLil/pii-sensitive-ner-german)
- [dslim/bert-base-NER](https://huggingface.co/dslim/bert-base-NER)
- [dbmdz/bert-base-german-cased](https://huggingface.co/dbmdz/bert-base-german-cased)

---

**Made with precision in Austria** 🇦🇹
