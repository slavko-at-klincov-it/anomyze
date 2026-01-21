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
- **Text-Glättung** — Optional: Transkripte mit lokalem LLM aufbereiten
- **Encoding-Korrektur** — Repariert kaputte Umlaute aus Transkriptions-Software
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
- Optional: [Ollama](https://ollama.ai) für Text-Glättung (`--smooth`)

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
Enter text (Enter = submit, Esc+Enter = newline, Ctrl+C = exit):
> Hallo, ich bin Thomas Müller von der Ersten Bank. Bei uns in der Billa kaufe ich immer ein.

Detected 3 entities:
  [PER         ] "Thomas Müller" (score: 0.86, source: pii)
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

### Text-Glättung (--smooth)

Entfernt Füllwörter und korrigiert Grammatik mit einem lokalen LLM:

```bash
# Ollama + Qwen installieren (einmalig)
brew install ollama
ollama pull qwen2.5:14b

# Mit Glättung
python anomyze.py --interactive --smooth
python anomyze.py transcript.txt output.txt --smooth
```

Bei Datei-Modus mit `--smooth`:
- `output.txt` — Geglätteter Text
- `output.raw.txt` — Original anonymisierter Text (vor Glättung)
- `output.mapping.json` — Mapping für Re-Anonymisierung

**Was `--smooth` macht:**
- Entfernt Füllwörter (ähm, also, halt, ja, mhm, etc.)
- Korrigiert Grammatik und macht Sätze flüssiger
- Behält alle Fakten und Platzhalter exakt bei
- Repariert Encoding-Fehler (kaputte Umlaute)

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
                                    ┌───────────────────┤
                                    ▼                   ▼ (optional)
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Fertiges       │◀────│  Re-Mapping     │◀────│  --smooth       │
│  Dokument       │     │  (lokal)        │     │  (Ollama)       │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                ▲
                                │
                        ┌───────┴───────┐
                        │  LLM Summary  │
                        │  (Cloud/API)  │
                        └───────────────┘
```

1. **Lokal**: Transkript durch Anomyze anonymisieren
2. **Lokal**: Optional mit `--smooth` Text glätten (Ollama)
3. **Lokal**: Mapping-Datei sicher aufbewahren
4. **Cloud**: Anonymisierten Text an LLM für Zusammenfassung
5. **Lokal**: Platzhalter durch echte Namen ersetzen

## Performance

Getestet auf MacBook Pro M3 Pro:

| Text | Zeit |
|------|------|
| < 500 Zeichen | ~2 Sek |
| 1-5 KB | ~10 Sek |
| > 10 KB | ~30 Sek |

## Encoding-Korrektur

Anomyze repariert automatisch kaputte Umlaute aus Transkriptions-Software:

| Fehler | Korrektur |
|--------|-----------|
| ‰, Š | ä |
| ÷ | ö |
| ¸, ³ | ü |
| ﬂ, ﬁ | ß |

## Bekannte Einschränkungen

- **Deutsch only** — Optimiert für deutsche Texte
- **Kontextabhängig** — "Hofer" als Name vs. Supermarkt nicht unterscheidbar
- **Manuelle Prüfung** — Automatische Erkennung ist nie 100%
- **Smooth-Timeout** — Text-Glättung hat 2 Min Timeout für sehr lange Texte

## Lizenz

MIT License

Die verwendeten Modelle haben eigene Lizenzen:
- [HuggingLil/pii-sensitive-ner-german](https://huggingface.co/HuggingLil/pii-sensitive-ner-german)
- [dslim/bert-base-NER](https://huggingface.co/dslim/bert-base-NER)
- [dbmdz/bert-base-german-cased](https://huggingface.co/dbmdz/bert-base-german-cased)

---

**Made with precision in Austria** 🇦🇹
