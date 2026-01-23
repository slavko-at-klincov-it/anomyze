# Anomyze Core

## Intelligente PII-Anonymisierung mit 3-Schicht-Erkennung

**Technical Whitepaper v1.1**

---

# Executive Summary

Anomyze ist eine Python-Bibliothek zur automatischen Erkennung und Anonymisierung personenbezogener Daten (PII) in deutschsprachigen Texten. Im Gegensatz zu herkömmlichen NER-Tools verwendet Anomyze eine einzigartige **3-Schicht-Erkennungsarchitektur**, die auch unbekannte Firmennamen und interne Projektnamen findet.

### Das Problem

Standard-NER-Modelle erkennen nur Entitäten, die in ihren Trainingsdaten vorkommen. Lokale Unternehmen, interne Projektnamen oder branchenspezifische Bezeichnungen werden übersehen:

```
"Der Kunde von Billa war zufrieden"    → "Billa" wird nicht erkannt ✗
"Das Projekt Goldfinch startet morgen" → "Goldfinch" wird nicht erkannt ✗
```

### Die Lösung

Anomyze ergänzt klassische NER um eine **Perplexity-basierte Anomalie-Erkennung**:

```
"Bei uns in der Küche gibt es Probleme"  → "Küche" ist erwartbar ✓
"Bei uns in der Billa gibt es Probleme"  → "Billa" ist unerwartet → Firma!
```

---

# 1. Architektur

## 1.1 3-Schicht-Erkennungssystem

```
┌────────────────────────────────────────────────────────────┐
│  Layer 1: PII Model                                        │
│  Modell: dslim/bert-large-NER (finetuned)                 │
│  → Namen, E-Mails, Telefonnummern, Geburtsdaten, Adressen │
│  → Optimiert für deutsche Namenskonventionen              │
├────────────────────────────────────────────────────────────┤
│  Layer 2: NER Model                                        │
│  Modell: dbmdz/bert-base-german-cased-NER                 │
│  → Bekannte Firmen, Orte, Personen aus Trainingsdaten     │
│  → Standard Named Entity Recognition                       │
├────────────────────────────────────────────────────────────┤
│  Layer 3: Perplexity Anomaly Detection                    │
│  Modell: dbmdz/bert-base-german-cased (MLM)               │
│  → Unbekannte Firmen durch sprachliche Anomalie-Analyse   │
│  → Kontextbasierte Erkennung ohne Vorwissen               │
└────────────────────────────────────────────────────────────┘
```

## 1.2 Perplexity-basierte Erkennung

### Das Prinzip

Sprachmodelle können vorhersagen, welche Wörter in einem Kontext wahrscheinlich sind. Wenn ein unerwartetes Wort auftaucht, ist das ein Hinweis auf einen Eigennamen:

```python
# Erwartete Wörter (niedrige Perplexity):
"Bei uns in der [Küche|Firma|Abteilung] gibt es..."

# Unerwartetes Wort (hohe Perplexity):
"Bei uns in der [Billa] gibt es..."
→ "Billa" hat hohe Perplexity im Kontext
→ Wahrscheinlich ein Eigenname/Firma
```

### Kontext-Patterns

Anomyze erkennt potenzielle Firmennamen in diesen Kontexten:

| Muster | Beispiel |
|--------|----------|
| "bei uns in der X" | "Bei uns in der **Billa**..." |
| "arbeite bei X" | "Ich arbeite bei **Hofer**" |
| "unser Kunde X" | "Unser Kunde **Merkur**" |
| "X Bank" | "...von der **Ersten Bank**" |
| "X Versicherung" | "...bei der **Allianz Versicherung**" |
| "X GmbH/AG" | "Die **Müller GmbH**..." |

### Algorithmus

```python
def detect_anomaly(text: str, candidate: str, mlm_pipeline) -> float:
    """
    Berechnet Anomalie-Score für einen Kandidaten im Kontext.

    Returns:
        Score 0.0-1.0 (höher = wahrscheinlicher ein Eigenname)
    """
    # 1. Text mit maskiertem Kandidat
    masked_text = text.replace(candidate, "[MASK]")

    # 2. Top-k Vorhersagen des Sprachmodells
    predictions = mlm_pipeline(masked_text, top_k=50)

    # 3. Prüfen ob Kandidat in Vorhersagen
    predicted_words = [p['token_str'] for p in predictions]

    if candidate.lower() not in [w.lower() for w in predicted_words]:
        # Kandidat ist unerwartet → hoher Score
        return calculate_perplexity_score(predictions, candidate)
    else:
        # Kandidat ist erwartbar → niedriger Score
        return 0.0
```

## 1.3 Entity Merging

Nach der Erkennung werden überlappende Entitäten zusammengeführt:

```
Input:  "Thomas Müller von der Ersten Bank"

Layer 1 (PII):    "Thomas" (GIVENNAME), "Müller" (SURNAME)
Layer 2 (NER):    "Thomas Müller" (PER), "Ersten Bank" (ORG)
Layer 3 (Anomaly): -

Merged:           "Thomas Müller" (PER, score: 0.92)
                  "Ersten Bank" (ORG, score: 0.85)
```

---

# 2. Erkannte Entitäten

## 2.1 Entitäts-Typen

| Kategorie | Typen | Quelle |
|-----------|-------|--------|
| **Personen** | GIVENNAME, SURNAME, PER | Layer 1, 2 |
| **Kontakt** | EMAIL, TELEPHONENUM | Layer 1 + Regex |
| **Dokumente** | IDCARDNUM, DATEOFBIRTH | Layer 1 |
| **Orte** | LOC, STREET | Layer 2 |
| **Organisationen** | ORG, ORG_DETECTED | Layer 2, 3 |

## 2.2 Zusätzliche Regex-Patterns

Für strukturierte Daten werden reguläre Ausdrücke verwendet:

| Pattern | Regex | Beispiel |
|---------|-------|----------|
| E-Mail | `[\w.-]+@[\w.-]+\.\w{2,}` | max.muster@firma.at |
| IBAN | `[A-Z]{2}\d{2}[\dA-Z]{4}\d{7}([\dA-Z]{0,16})?` | AT611904300234573201 |
| Telefon | `(\+\d{1,3}[\s-]?)?\(?\d{2,4}\)?[\s.-]?\d{3,4}[\s.-]?\d{2,4}` | +43 1 234 5678 |
| SVN (AT) | `\d{4}\s?\d{6}` | 1234 010190 |

## 2.3 Blacklist-Filterung

Häufige Fehlerkennungen werden herausgefiltert:

```python
ENTITY_BLACKLIST = {
    # Deutsche Wörter die fälschlich erkannt werden
    "Montag", "Dienstag", "Januar", "Februar", "März",
    "Herr", "Frau", "Sehr", "Geehrte", "Freundlichen",
    # Häufige englische Begriffe
    "Team", "Meeting", "Call", "Update", "Status",
    # Technische Begriffe
    "Server", "Client", "API", "Backend", "Frontend",
}
```

---

# 3. API Reference

## 3.1 Hauptfunktionen

### `anonymize(text, pii_pipeline, org_pipeline, mlm_pipeline) -> AnonymizeResult`

Anonymisiert Text und gibt strukturiertes Ergebnis zurück.

```python
from anomyze import anonymize, load_models

# Modelle einmalig laden
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

print(result.entities)
# → [
#     {"text": "Thomas Müller", "label": "PER", "score": 0.92, "source": "pii"},
#     {"text": "Ersten Bank", "label": "ORG", "score": 0.85, "source": "ner"}
#   ]
```

### `load_models(device=None, verbose=True) -> Tuple`

Lädt alle ML-Modelle und gibt die Pipelines zurück.

```python
from anomyze import load_models

# Automatische Geräteerkennung (MPS > CUDA > CPU)
pii_pipeline, org_pipeline, mlm_pipeline = load_models()

# Explizites Gerät
pii, org, mlm = load_models(device="cuda:0")
```

## 3.2 Datenstrukturen

### `AnonymizeResult`

```python
@dataclass
class AnonymizeResult:
    text: str                      # Anonymisierter Text
    mapping: Dict[str, str]        # Placeholder → Original
    entities: List[Dict]           # Alle erkannten Entitäten
    original_text: str             # Originaltext (für Re-Identifikation)
```

### `Settings`

```python
@dataclass
class Settings:
    pii_threshold: float = 0.7      # Mindest-Score für PII
    org_threshold: float = 0.7      # Mindest-Score für ORG
    anomaly_threshold: float = 0.5  # Mindest-Score für Anomalien
    device: str = "auto"            # "auto", "mps", "cuda", "cpu"
    verbose: bool = True            # Debug-Ausgaben
```

## 3.3 CLI

```bash
# Interaktiver Modus
anomyze --interactive

# Datei verarbeiten
anomyze input.txt output.txt

# Mit Text-Glättung (benötigt Ollama)
anomyze input.txt output.txt --smooth
```

---

# 4. Performance

## 4.1 Benchmarks

Getestet auf Apple M3 Pro (18 GB RAM):

| Textlänge | Zeit | Speicher |
|-----------|------|----------|
| < 500 Zeichen | ~2s | ~2.5 GB |
| 1-5 KB | ~10s | ~3 GB |
| > 10 KB | ~30s | ~4 GB |

## 4.2 Optimierung

### GPU-Beschleunigung

```python
# Apple Silicon (MPS)
pii, org, mlm = load_models(device="mps")

# NVIDIA CUDA
pii, org, mlm = load_models(device="cuda:0")
```

### Batch-Verarbeitung

```python
# Für viele kurze Texte
results = [anonymize(text, pii, org, mlm) for text in texts]
```

---

# 5. Verwendete Modelle

| Modell | Zweck | Lizenz | Größe |
|--------|-------|--------|-------|
| dslim/bert-large-NER | PII-Erkennung | Apache 2.0 | ~1.3 GB |
| dbmdz/bert-base-german-cased-NER | NER | MIT | ~0.4 GB |
| dbmdz/bert-base-german-cased | Perplexity | MIT | ~0.4 GB |

Gesamter Speicherbedarf: **~2.5 GB**

Modelle werden beim ersten Start automatisch von Hugging Face heruntergeladen.

---

# 6. Integration

## 6.1 Als Python-Modul

```python
# In eigener Anwendung
from anomyze import anonymize, load_models, Settings, configure

# Konfiguration anpassen
settings = Settings(
    pii_threshold=0.8,
    device="mps"
)
configure(settings)

# Modelle laden und verwenden
pii, org, mlm = load_models()
result = anonymize("Text...", pii, org, mlm)
```

## 6.2 Als API-Backend

Die [Anomyze Extension](https://github.com/slavko-at-klincov-it/anomyze-extension) bietet einen FastAPI-Server, der Anomyze als Backend verwendet.

---

# Verwandte Projekte

- **[Anomyze Extension](https://github.com/slavko-at-klincov-it/anomyze-extension)** — Browser Extension + API Server für Enterprise-Deployment
- **[Enterprise Whitepaper](https://github.com/slavko-at-klincov-it/anomyze-extension/blob/main/docs/whitepaper-enterprise.md)** — Ausführliche Dokumentation für IT-Entscheider

---

**Version 1.1 | Januar 2025**

**Made with precision in Austria** 🇦🇹
