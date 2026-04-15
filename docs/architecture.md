# Anomyze Architektur

## Überblick

Anomyze ist eine souveräne KI-Anonymisierungsschicht für die österreichische Bundesverwaltung. Es ist der **Output-Filter** der "Public AI"-Initiative: Die KI-Tools (GovGPT, ELAK-KI, KAPA) arbeiten intern mit den vollen Daten — sie brauchen PII, um zu funktionieren. Anomyze prüft und filtert den Output, bevor er das System verlässt.

## Mehrschichtige Detection-Pipeline

```
KI-Tool (GovGPT / ELAK-KI / KAPA)
  arbeitet intern mit vollen Daten
     │
     ▼
KI-generierter Output
     │
     ▼
┌───────────────────────────────┐
│  Preprocessing                │  fix_encoding()
│                               │  normalize_adversarial()
└─────────┬─────────────────────┘
          ▼
┌───────────────────────────────┐
│  Stage 1: Regex               │  Österreich-spezifische Muster
│  (regex_layer.py)             │  modular unter anomyze/patterns/
│                               │  email, phone, financial, documents,
│                               │  vehicles, addresses, names, dates
└─────────┬─────────────────────┘
          ▼
┌───────────────────────────────┐
│  Stage 2a: PII-NER            │  HuggingLil/pii-sensitive-ner-german
│  (ner_layer.py)               │  Namen, E-Mails, Telefon, Geburtsdaten
├───────────────────────────────┤
│  Stage 2a: ORG-NER            │  Davlan/xlm-roberta-large-ner-hrl
│  (ner_layer.py)               │  Organisationen, Orte, Personen
├───────────────────────────────┤
│  Stage 2b: GLiNER Zero-Shot   │  urchade/gliner_large-v2.1 (optional)
│  (gliner_layer.py)            │  zero-shot NER für AT-PII-Kategorien
├───────────────────────────────┤
│  Stage 2c: Presidio-compat    │  Lokale AT-Recognizer (kein Presidio-Dep)
│  (presidio_compat_layer.py)   │  SVNR, IBAN, KFZ, Firmenbuch, Reisepass,
│                               │  Aktenzahl, AT-Namen
└─────────┬─────────────────────┘
          ▼
┌───────────────────────────────┐
│  Ensemble-Merge               │  Überlappende Spans zusammenführen,
│  (ensemble.py)                │  Konfidenz aggregieren, Layer-Quellen tracken
└─────────┬─────────────────────┘
          ▼
┌───────────────────────────────┐
│  Stage 3: Kontext / MLM       │  a) Perplexitäts-Anomalie-Erkennung
│  (context_layer.py)           │     (unbekannte Firmennamen via MLM)
│                               │  b) Quasi-Identifikator-Check
│                               │     (Rolle + Ort + Alter ohne Name)
│                               │  Modell: dbmdz/bert-base-german-cased
└─────────┬─────────────────────┘
          ▼
┌───────────────────────────────┐
│  Entity-Resolver              │  Verknüpft Varianten derselben Entität
│  (entity_resolver.py)         │  Kölner Phonetik + Teilstring-Matching
└─────────┬─────────────────────┘
          ▼
┌───────────────────────────────┐
│  Kanal-Auswahl                │  govgpt / ifg / kapa
└───┬─────┬─────┬───────────────┘
    ▼     ▼     ▼
 GovGPT  IFG  KAPA
    │     │     │
    ▼     ▼     ▼
┌───────────────────────────────┐
│  Quality-Check                │  Scannt die finale Ausgabe auf
│  (quality_check.py)           │  durchgerutschte PII-Reste
└─────────┬─────────────────────┘
          ▼
 Gefilterter Output verlässt das System
```

## 3 Ausgabe-Kanäle

### GovGPT-Kanal
- **Zweck:** KI-generierte Antworten und Berichte filtern, bevor sie an Bedienstete weitergegeben werden
- **Verhalten:** PII → nummerierte Platzhalter (`[PERSON_1]`, `[IBAN_1]`)
- **Mapping:** Platzhalter → Original wird gespeichert (re-identifizierbar für autorisierte User)
- **Anwendung:** GovGPT, ELAK-KI — Output-Filterung vor Weitergabe

### IFG-Kanal (Informationsfreiheitsgesetz)
- **Zweck:** KI-generierte Outputs schwärzen, bevor sie auf data.gv.at veröffentlicht werden
- **Verhalten:** PII → `[GESCHWÄRZT:KATEGORIE]` (ohne Nummerierung)
- **Mapping:** Kein Mapping — irreversibel by design
- **Schwärzungsprotokoll:** Kategorie + Anzahl (nie Originalwerte)
- **DSGVO:** Kein Rückweg, original_text wird nicht gespeichert

### KAPA-Kanal (Parlamentarische Anfragen)
- **Zweck:** KI-Rechercheergebnisse filtern, bevor sie als parlamentarische Antworten das System verlassen
- **Verhalten:** Wie GovGPT + vollständiger Audit-Trail
- **Human-in-the-Loop:** Entitäten unter Konfidenz-Schwelle → `[PRÜFEN:TYPE_N]`
- **Audit-Trail:** Zeitstempel, Konfidenz, Quell-Layer, Kontext-Snippet

## Paketstruktur

```
anomyze/
├── api/                        FastAPI REST-Endpunkte
│   ├── main.py                 App-Factory mit Model-Preloading
│   ├── routes.py               POST /anonymize, GET /health, ...
│   └── models.py               Pydantic Request/Response Schemas
├── benchmark/                  Benchmark-Framework
│   ├── loader.py               JSON-Dataset-Loader
│   ├── metrics.py              Precision/Recall/F1 (per Kategorie + Layer)
│   ├── evaluator.py            Orchestriert Run über Samples
│   ├── reporter.py             Text- und JSON-Report
│   └── __main__.py             CLI: python -m anomyze.benchmark
├── pipeline/                   Kern-Pipeline
│   ├── __init__.py             DetectedEntity Dataclass
│   ├── orchestrator.py         Pipeline-Steuerung + ModelManager
│   ├── normalizer.py           Adversarial-Normalization (Homoglyphen etc.)
│   ├── regex_layer.py          Stage 1: Regex-Erkennung
│   ├── ner_layer.py            Stage 2a: PII + ORG NER-Modelle
│   ├── gliner_layer.py         Stage 2b: GLiNER Zero-Shot
│   ├── presidio_compat_layer.py  Stage 2c: AT-Recognizer
│   ├── ensemble.py             Merge überlappender Detections
│   ├── context_layer.py        Stage 3: Anomalie + Quasi-Identifikatoren
│   ├── entity_resolver.py      Verknüpfung von Entitäts-Varianten
│   ├── quality_check.py        Post-Anonymization-Check
│   ├── phonetic.py             Kölner Phonetik für deutsche/AT-Namen
│   ├── recognizers/            Presidio-kompatible Recognizer-Klassen
│   │   ├── base.py             PatternRecognizer, Pattern, RecognizerResult
│   │   └── austrian.py         ATSVNR, ATIBAN, ATKFZ, ATFirmenbuch,
│   │                           ATPassport, ATAktenzahl, ATName
│   └── utils.py                Entity-Utilities (Overlap, Cleaning)
├── channels/                   3-Kanal-Output
│   ├── base.py                 Abstrakte Basis-Klasse
│   ├── govgpt.py               Platzhalter + Mapping
│   ├── ifg.py                  Irreversible Schwärzung
│   └── kapa.py                 Platzhalter + Audit-Trail
├── mappings/
│   └── mapping_store.py        Platzhalter ↔ Original Zuordnung
├── audit/
│   └── logger.py               Audit-Trail Logging
├── patterns/                   Modulare Regex-Pattern-Bibliothek
│   ├── addresses.py            Straße+Nr, PLZ+Ort
│   ├── at_names.py             AT-Vornamen und -Nachnamen
│   ├── blacklist.py            False-Positive-Filterung
│   ├── company_context.py      Kontext-Patterns für unbekannte Firmen
│   ├── dates.py                Geburtsdatum
│   ├── documents.py            Reisepass, Personalausweis, Aktenzahl
│   ├── email.py                E-Mail
│   ├── financial.py            IBAN, SVNR, Steuernummer
│   ├── names.py                Titel+Name, Label+Name
│   ├── phone.py                AT-Telefonnummern
│   └── vehicles.py             KFZ-Kennzeichen (AT-Bezirkscodes)
├── config/
│   └── settings.py             Zentrale Konfiguration
└── cli.py                      Kommandozeilen-Interface

benchmarks/
├── README.md                   Benchmark-Doku
└── datasets/
    ├── synthetic_at.json       25 annotierte AT-PII-Sätze
    └── realistic_at.json       6 realistische AT-Dokumente
```

## Modelle

| Modell | Zweck | Größe |
|--------|-------|-------|
| HuggingLil/pii-sensitive-ner-german | PII-NER (Namen, E-Mails, Telefon, Geburtsdaten) | ~1.3 GB |
| Davlan/xlm-roberta-large-ner-hrl | NER (Organisationen, Orte, Personen) | ~2.2 GB |
| dbmdz/bert-base-german-cased | MLM für Anomalie-Erkennung | ~0.4 GB |
| urchade/gliner_large-v2.1 | GLiNER Zero-Shot NER (optional) | ~1.7 GB |

Alle Modelle laufen 100 % lokal — kein Cloud-Call, kein API-Call nach außen. Die Defaults können via `ANOMYZE_*`-Umgebungsvariablen überschrieben werden (siehe `anomyze/config/settings.py`).

## Erkannte PII-Typen

| entity_group | Beispiel | Erkennung |
|--------------|----------|-----------|
| PER | Maria Gruber | NER + AT-Namensliste + Kölner Phonetik |
| ORG | Bundesministerium für Inneres | NER |
| ORG_DETECTED | Merkur, Goldfinch | Kontext-Perplexität |
| LOC | Wien, Graz | NER |
| ADRESSE | Schottenfeldgasse 29/3, 1070 Wien | Regex (Straße+Nr, PLZ+Ort) |
| EMAIL | m.gruber@gmail.com | Regex |
| IBAN | AT61 1904 3002 3457 3201 | Regex + AT-Recognizer |
| SVN | 1234 140387 | Regex + Datumsvalidierung |
| STEUERNUMMER | 12-345/6789 | Regex |
| GEBURTSDATUM | 14.03.1987 | Regex |
| AKTENZAHL | GZ BMI-2024/0815 | Regex + AT-Recognizer |
| FIRMENBUCH | FN 123456 a | AT-Recognizer |
| REISEPASS | P1234567 | Regex (kontext-gesteuert) |
| PERSONALAUSWEIS | AB123456CD | Regex (kontext-gesteuert) |
| KFZ | W-34567B | Regex (AT-Bezirkscodes) |
| TELEFON | +43 664 1234567 | Regex |
| QUASI_ID | "der Beschwerdeführer aus Graz, geboren 1985" | Kontext (Kombinations-Check) |

## Ensemble-Merging

Die Detection-Layer arbeiten weitgehend unabhängig und produzieren oft überlappende Treffer für dieselbe PII. Das Ensemble (`anomyze/pipeline/ensemble.py`) führt diese zusammen:

- **Overlap-Erkennung:** Detections mit gemeinsamer Span werden gruppiert.
- **Kategorie-Auflösung:** Bei Kategorie-Konflikten gewinnt die Kombination mit höherer Gesamtkonfidenz; alle Quell-Layer bleiben in `entity.sources` nachvollziehbar.
- **Score-Aggregation:** Die Konfidenz wird aus den Einzelscores aggregiert und steigt, wenn mehrere Layer zustimmen.
- **Layer-Tracking:** Jede finale Detection trägt `source` (primärer Layer) und `sources` (alle beteiligten Layer).

Der Benchmark nutzt `entity.source`, um pro Layer Precision/Recall/F1 auszuweisen.

## Adversarial-Normalization

Bevor die Detection-Layer greifen, normalisiert `anomyze/pipeline/normalizer.py` typische Umgehungsversuche:

- Unicode-Homoglyphen (kyrillisches "а" statt lateinischem "a")
- Zero-Width-Spaces und unsichtbare Steuerzeichen
- Leetspeak-Varianten (z. B. "M@x1" → "Maxi")
- Mehrfach-Leerzeichen und NBSP-Normalisierung

Die Normalisierung wirkt ausschließlich auf die Detection-Eingabe; der Original-Text wird vom Channel für die Ausgabe und für Mappings verwendet.

## Entity-Resolver

Der Entity-Resolver (`anomyze/pipeline/entity_resolver.py`) verknüpft Varianten derselben realen Entität, damit z. B. "Maria Gruber", "Frau Gruber" und "M. Gruber" denselben Platzhalter `[PERSON_1]` bekommen. Er kombiniert:

- Teilstring-/Token-Matching
- Kölner Phonetik (für Namen mit Schreibweisen-Varianten)
- Title-/Anrede-Heuristik

Das ist insbesondere für längere Dokumente (Bescheide, Protokolle) wichtig, in denen dieselbe Person mehrfach und unterschiedlich genannt wird.

## Quality-Check

Nach der Channel-Verarbeitung scannt `anomyze/pipeline/quality_check.py` die finale Ausgabe erneut auf PII-Muster (Regex-only, schnell). Treffer zeigen durchgerutschte Residuen an, die in Audit und im Report ausgewiesen werden. Besonders relevant für den IFG-Kanal, weil dort keine Re-Identifikation mehr möglich ist.

## Quasi-Identifikator-Erkennung

Einzelne Datenpunkte (Ort, Geburtsjahr, Berufsbezeichnung) sind für sich genommen nicht identifizierend. In Kombination können sie eine Person aber eindeutig bestimmen — auch ohne dass ein Name genannt wird.

**Beispiel:** "der Beschwerdeführer aus Graz, geboren 1985" — kein Name, aber möglicherweise identifizierbar.

Der Context-Layer erkennt solche Kombinationen:

| Signal-Typ | Beispiele |
|-----------|-----------|
| Rolle | Beschwerdeführer, Antragstellerin, Betroffener, Zeuge, Patientin |
| Ort | Bereits erkannte LOC/ADRESSE-Entitäten |
| Alter/Geburtsjahr | "geboren 1985", "45-jährige", "Jahrgang 1972" |
| Geschlecht | "die weibliche", "ein Mann" |

**Logik:** Wenn 2+ Signal-Typen innerhalb von 200 Zeichen auftreten und **kein** PER-Entity im selben Fenster erkannt wurde, werden die nicht-erkannten Signale als QUASI_ID geflaggt (Konfidenz 0.70). Im KAPA-Kanal landen sie automatisch im `[PRÜFEN:...]`-Bereich zur manuellen Prüfung.

## Benchmark-Framework

Unter `anomyze/benchmark/` liegt ein Framework, das die Pipeline gegen annotierte Ground-Truth-Datensätze vergleicht und Precision/Recall/F1 pro Kategorie und pro Detection-Layer liefert. Zwei mitgelieferte Datasets: `benchmarks/datasets/synthetic_at.json` (25 kurze AT-PII-Sätze) und `benchmarks/datasets/realistic_at.json` (6 längere AT-Dokumente). Details unter [../benchmarks/README.md](../benchmarks/README.md).
