# Anomyze Benchmark-Framework

Mit dem Benchmark-Framework laesst sich die Detection-Qualitaet der
3-stufigen Anomyze-Pipeline messen. Es vergleicht die Ausgabe des
Pipeline-Orchestrators mit annotierten Ground-Truth-Daten und liefert
Precision, Recall und F1 pro Kategorie, pro Detection-Layer sowie global.

## Ausfuehren

    python -m anomyze.benchmark benchmarks/datasets/synthetic_at.json

Wichtige Flags:

    --json                     Maschinenlesbare JSON-Ausgabe.
    --device {cpu,mps,cuda}    Erzwingt ein bestimmtes Compute-Device.
    --iou-threshold 0.5        IoU-Schwellwert fuer einen Treffer.
    --with-mlm                 MLM-basierte Kontext-/Anomalieschicht aktivieren.
    --with-gliner              GLiNER Zero-Shot-NER aktivieren.
    --no-presidio              Presidio-kompatible Recognizer deaktivieren.
    --no-regex                 Regex-Schicht deaktivieren.

Ohne `--with-mlm` und `--with-gliner` laeuft ein schneller Benchmark
ueber Regex + NER + Presidio-kompatible Schicht.

## Datenformat

Ein Dataset ist eine JSON-Liste mit Sample-Objekten:

    [
      {
        "id": "sample-001",
        "text": "Kontakt: maria@example.at, IBAN AT00 0000 0000 0000 0001",
        "entities": [
          {"start": 9, "end": 25, "type": "EMAIL"},
          {"start": 32, "end": 56, "type": "IBAN"}
        ]
      }
    ]

Die `start`/`end`-Offsets sind Python-String-Indizes (UTF-8,
Umlaute zaehlen als 1 Zeichen). `type` verwendet die internen
entity_group-Namen (EMAIL, IBAN, SVN, TELEFON, KFZ, PER, ORG,
ADRESSE, REISEPASS, AKTENZAHL, FIRMENBUCH, QUASI_ID, ...).

## Vorhandene Datasets

- `datasets/synthetic_at.json` (25 kurze Saetze, AT-PII, rein fiktive Werte)
- `datasets/realistic_at.json` (6 laengere AT-Dokumente: Bescheid,
  Anfrage, Protokoll, Ladung, Zahlungsaufforderung, Meldung)

Alle Werte sind bewusst nicht echt (fiktive Domains, IBANs mit
Null-Bloecken, Dummy-SVNR). Die Datasets sollen ausschliesslich der
Qualitaetsmessung dienen.

## Interpretation der Metriken

- **True Positive (TP)**: Detektierte Entity span-ueberlappt mit einer
  Ground-Truth-Entity der gleichen Kategorie (IoU >= Threshold).
- **False Positive (FP)**: Detektierte Entity matcht keine Ground-Truth.
- **False Negative (FN)**: Ground-Truth-Entity wurde nicht gefunden.
- **Precision** = TP / (TP + FP)  -- Anteil korrekter Detektionen.
- **Recall** = TP / (TP + FN)     -- Anteil gefundener PII.
- **F1** = harmonisches Mittel von Precision und Recall.

### Per-Kategorie

Zeigt Staerken und Schwaechen einzelner Kategorien: Regex-detektierbare
PII (EMAIL, IBAN, SVN, AKTENZAHL, FIRMENBUCH) sollten F1 > 0.9 erreichen.
NER-abhaengige Kategorien (PER, ADRESSE) liegen typischerweise niedriger.

### Per-Layer

Fuer jede Detection-Schicht (regex, pii, org, pattern, perplexity, ...)
wird TP/FP/FN unabhaengig berechnet: pro Ground-Truth-Entity bekommt
jede Schicht ein TP, wenn sie selbst die Entity gefunden hat, sonst
einen FN. So sieht man den individuellen Beitrag jeder Schicht zur
Gesamt-Qualitaet.

## Ein eigenes Dataset erstellen

1. JSON-Liste mit `id`, `text`, `entities`-Feldern anlegen.
2. Jede Entity mit `start`, `end`, `type` annotieren.
3. Positionen verifizieren (z. B. `text[start:end]` in Python).
4. Loader anwerfen: `python -m anomyze.benchmark path/to/dataset.json`.
