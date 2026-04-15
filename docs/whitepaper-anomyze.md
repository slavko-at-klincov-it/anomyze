# Anomyze

## Souveräne KI-Anonymisierungsschicht für die österreichische Bundesverwaltung

**Technical Whitepaper v2.0**

---

# Executive Summary

Anomyze ist der **Output-Filter** der "Public AI"-Initiative der österreichischen Bundesverwaltung. Die KI-Tools — GovGPT, ELAK-KI, KAPA — arbeiten intern mit vollen Daten, weil sie PII benötigen, um Anfragen sinnvoll zu beantworten. Anomyze prüft und filtert den **Output**, bevor er das System verlässt: Veröffentlichungen auf data.gv.at, parlamentarische Antworten, weitergeleitete Berichte an Bedienstete.

Die Detection-Pipeline kombiniert Regex, mehrere NER-Modelle (klassisch und Zero-Shot), Presidio-kompatible AT-spezifische Recognizer, eine Perplexitäts-basierte Anomalie-Erkennung sowie einen Quasi-Identifikator-Check. Drei Ausgabe-Kanäle adressieren unterschiedliche Rechtsgrundlagen: GovGPT (reversible Mappings), IFG (irreversible Schwärzung), KAPA (reversible Mappings plus vollständiger Audit-Trail). Alle Komponenten laufen 100 % lokal, ohne Cloud-Anbindung oder externen API-Call.

### Das Problem

KI-Tools im behördlichen Kontext produzieren Antworten, die personenbezogene Daten aus Akten, Registern und Protokollen reproduzieren. Werden diese Antworten weitergegeben oder veröffentlicht, ist der Output eine De-facto-Offenlegung. Standard-NER-Modelle erfassen gängige Namen und Organisationen, übersehen aber:

- lokale Unternehmen und interne Projektnamen,
- österreichspezifische Formate (SVNR, Firmenbuchnummer, AT-KFZ-Kennzeichen, Aktenzahlen),
- Quasi-Identifikatoren (Rolle + Ort + Alter ohne Nennung des Namens),
- Umgehungsversuche durch Unicode-Homoglyphen, Zero-Width-Spaces oder Leetspeak.

### Die Lösung

Anomyze ergänzt klassische NER um vier komplementäre Schichten und ein Ensemble, das die Einzelsignale zu einer finalen Detection verbindet. Entscheidungen bleiben pro Detection auf den Quell-Layer zurückführbar, ein integriertes Benchmark-Framework misst die Qualität pro Kategorie und Layer.

---

# 1. Architektur

## 1.1 Pipeline-Überblick

```
┌────────────────────────────────────────────────────────────────────┐
│  Preprocessing                                                     │
│    fix_encoding()           — Transkriptions-/OCR-Artefakte       │
│    normalize_adversarial()  — Homoglyphen, Zero-Width, Leetspeak  │
├────────────────────────────────────────────────────────────────────┤
│  Stage 1 — Regex                                                   │
│    anomyze/patterns/{email, phone, financial, documents,          │
│                      vehicles, addresses, names, dates}.py        │
├────────────────────────────────────────────────────────────────────┤
│  Stage 2a — NER-Ensemble                                           │
│    PII-Modell: HuggingLil/pii-sensitive-ner-german                │
│    ORG-Modell: Davlan/xlm-roberta-large-ner-hrl                   │
│  Stage 2b — GLiNER Zero-Shot (optional)                           │
│    urchade/gliner_large-v2.1                                      │
│  Stage 2c — Presidio-kompatible AT-Recognizer                     │
│    SVNR, IBAN, KFZ, Firmenbuch, Reisepass, Aktenzahl, AT-Namen   │
├────────────────────────────────────────────────────────────────────┤
│  Ensemble-Merge                                                    │
│    Überlappende Spans zusammenführen, Konfidenz aggregieren,      │
│    Quell-Layer in entity.sources erhalten                         │
├────────────────────────────────────────────────────────────────────┤
│  Stage 3 — Kontext / MLM                                           │
│    dbmdz/bert-base-german-cased                                   │
│    a) Perplexitäts-Anomalie (unbekannte Firmennamen)              │
│    b) Quasi-Identifikator-Check (Rolle + Ort + Alter)             │
├────────────────────────────────────────────────────────────────────┤
│  Entity-Resolver                                                   │
│    Verknüpft Varianten derselben Entität                          │
│    (Kölner Phonetik + Teilstring-Matching)                        │
├────────────────────────────────────────────────────────────────────┤
│  Kanal-Auswahl: govgpt / ifg / kapa                               │
├────────────────────────────────────────────────────────────────────┤
│  Quality-Check                                                     │
│    Scannt finale Ausgabe auf durchgerutschte PII-Reste            │
└────────────────────────────────────────────────────────────────────┘
```

## 1.2 Ausgabe-Kanäle

| Kanal | Zweck | Platzhalter | Reversibilität | Audit |
|-------|-------|-------------|----------------|-------|
| **GovGPT** | Antwort-Filter vor Weitergabe an Bedienstete | `[PERSON_1]`, `[IBAN_1]` | Ja (Mapping) | — |
| **IFG** | Schwärzung vor Veröffentlichung auf data.gv.at | `[GESCHWÄRZT:PERSON]` | Nein (by design) | Schwärzungsprotokoll |
| **KAPA** | Parlamentarische Antworten mit Nachweispflicht | Wie GovGPT + `[PRÜFEN:X]` | Ja (Mapping) | Vollständiger Audit-Trail |

Der IFG-Kanal speichert bewusst kein Mapping und behält keinen Original-Text zurück; die Schwärzung ist irreversibel by design. Der KAPA-Kanal protokolliert jede Detection mit Zeitstempel, Konfidenz, Quell-Layer und Kontext-Snippet und markiert Detections unter der konfigurierbaren Review-Schwelle (`ANOMYZE_KAPA_REVIEW_THRESHOLD`, Default 0.85) als `[PRÜFEN:TYPE_N]`.

---

# 2. Detection-Layer im Detail

## 2.1 Stage 1 — Regex

Modularer Aufbau unter `anomyze/patterns/`:

| Modul | Erkennt |
|-------|---------|
| `email.py` | E-Mail-Adressen |
| `phone.py` | AT-Telefonnummern (+43, 0043, 06xx) |
| `financial.py` | IBAN (AT), SVNR, Steuernummer |
| `documents.py` | Reisepass, Personalausweis, Aktenzahl |
| `vehicles.py` | KFZ-Kennzeichen (AT-Bezirkscodes) |
| `addresses.py` | Straße+Nr, PLZ+Ort (AT-PLZ) |
| `names.py` | Titel+Name, Label+Name (z. B. "Dr. Maria Gruber") |
| `dates.py` | Geburtsdatum |
| `at_names.py` | AT-Vor- und Nachnamen-Liste |
| `company_context.py` | Kontext-Patterns für Stage 3 |
| `blacklist.py` | False-Positive-Filterung ("Montag", "Herr", ...) |

Die Regex-Layer arbeitet mit hoher Präzision für klar strukturierte Formate. SVNR-Treffer werden zusätzlich per Datumsvalidierung (Tag/Monat im Suffix) geprüft; IBAN-Treffer gegen das AT-Länderkürzel; KFZ gegen die Liste der AT-Bezirkscodes.

## 2.2 Stage 2a — NER-Ensemble

**PII-Modell** `HuggingLil/pii-sensitive-ner-german` liefert Personennamen, E-Mails, Telefonnummern und Geburtsdaten mit dem PII-Ontologie-Tag-Schema (TELEPHONENUM, GIVENNAME, SURNAME, DATEOFBIRTH).

**ORG-Modell** `Davlan/xlm-roberta-large-ner-hrl` ergänzt Organisationen und Orte. Die Labels (B-/I-PER, B-/I-ORG, B-/I-LOC) werden auf das interne Schema normalisiert; nur `ORG`, `LOC` und `PER` werden übernommen, weil MISC zu viele False Positives produziert.

Beide Modelle laufen als HuggingFace `token-classification`-Pipelines mit `aggregation_strategy="simple"`. Konfidenz-Schwellen (`ANOMYZE_PII_THRESHOLD`, `ANOMYZE_ORG_THRESHOLD`, Default 0.7) werden je Layer angewendet.

## 2.3 Stage 2b — GLiNER Zero-Shot

Optional (`ANOMYZE_USE_GLINER=true`, Default an) wird `urchade/gliner_large-v2.1` geladen und für eine konfigurierbare Liste von Entity-Typen in natürlicher Sprache angefragt:

```python
gliner_entity_types = (
    "person name", "email address", "phone number",
    "physical address", "date of birth", "organization",
    "company name", "social security number",
    "bank account number", "license plate number",
)
```

GLiNER funktioniert sprach-agnostisch und findet Kategorien, die das PII-Modell nicht trainiert hat. Der Score-Threshold ist niedriger (`ANOMYZE_GLINER_THRESHOLD`, Default 0.4), weil Zero-Shot unsicherer ist; die Ensemble-Stufe filtert Unsicheres heraus.

## 2.4 Stage 2c — Presidio-kompatible AT-Recognizer

Anomyze implementiert die Recognizer-API von Microsoft Presidio, ohne `presidio-analyzer` als Dependency mitzunehmen. Unter `anomyze/pipeline/recognizers/` liegen AT-spezifische Recognizer:

| Recognizer | Entity-Typ | Muster |
|------------|------------|--------|
| `ATSVNRRecognizer` | SVN | 10 Ziffern, Suffix DDMMYY, Datumsvalidierung |
| `ATIBANRecognizer` | IBAN | AT + 2 Prüfziffern + 16 Ziffern (gruppiert) |
| `ATKFZRecognizer` | KFZ | Bezirkscode + Ziffern + Buchstaben |
| `ATFirmenbuchRecognizer` | FIRMENBUCH | FN + 1-6 Ziffern + Prüfbuchstabe a-z |
| `ATPassportRecognizer` | REISEPASS | 1 Buchstabe + 7 Ziffern (kontext-gesteuert) |
| `ATAktenzahlRecognizer` | AKTENZAHL | GZ/Az/Zl-Präfix + Kürzel |
| `ATNameRecognizer` | PER | Exact-Match gegen AT-Namensliste |

Kontext-Wörter (`context=["iban", "konto", ...]`) boosten die Konfidenz innerhalb eines Fensters um den Treffer herum. Das ist insbesondere für schwach strukturierte Muster wie Reisepass (`[A-Z]\d{7}`) relevant, weil der Score ohne Kontext niedrig ist.

## 2.5 Ensemble-Merging

`anomyze/pipeline/ensemble.py` führt überlappende Detections aus allen Stage-2-Layern zusammen. Ziel: eine Detection pro tatsächlichem PII-Vorkommen, mit aggregierter Konfidenz und kompletter Nachvollziehbarkeit:

- **Overlap-Erkennung:** Spans mit gemeinsamer Überlappung werden gruppiert.
- **Kategorie-Auflösung:** Bei Konflikten gewinnt die Kombination mit der höchsten Summen-Konfidenz; alle Quell-Layer bleiben in `entity.sources` erhalten.
- **Score-Aggregation:** Die Einzelscores werden aggregiert, sodass Mehrfach-Zustimmung einen höheren finalen Score ergibt.

Der Benchmark wertet `entity.source` pro Layer aus und liefert damit eine transparente Aussage darüber, wie viel jede Schicht tatsächlich beiträgt.

## 2.6 Stage 3 — Kontext / MLM

Der Context-Layer (`anomyze/pipeline/context_layer.py`) nutzt das MLM `dbmdz/bert-base-german-cased` für zwei unabhängige Aufgaben:

**a) Perplexitäts-basierte Anomalie-Erkennung.** Wortkandidaten in typischen Firmenkontexten ("bei uns in der X", "unser Kunde X", "X GmbH") werden maskiert und das MLM liefert die Top-k-Vorhersagen. Taucht der Kandidat nicht unter den erwarteten Wörtern auf, wird er als potenzieller Eigenname geflaggt (`ORG_DETECTED`).

**b) Quasi-Identifikator-Check.** Einzelne Signale (Rolle, Ort, Alter, Geschlecht) sind für sich nicht identifizierend, aber in Kombination können sie eine Person eindeutig bestimmen — auch wenn kein Name genannt wird:

| Signal-Typ | Beispiele |
|------------|-----------|
| Rolle | Beschwerdeführer, Antragstellerin, Betroffener, Zeuge, Patientin |
| Ort | Bereits erkannte LOC/ADRESSE-Entitäten |
| Alter / Geburtsjahr | "geboren 1985", "45-jährige", "Jahrgang 1972" |
| Geschlecht | "die weibliche", "ein Mann" |

Wenn 2+ Signal-Typen innerhalb von 200 Zeichen auftreten und kein PER-Entity im selben Fenster erkannt wurde, werden die nicht-erkannten Signale als `QUASI_ID` (Konfidenz 0.70) geflaggt. Im KAPA-Kanal landen sie automatisch unter `[PRÜFEN:QUASI_ID_N]`.

---

# 3. Supporting-Layer

## 3.1 Adversarial-Normalization

`anomyze/pipeline/normalizer.py` normalisiert die Detection-Eingabe gegen typische Umgehungsversuche:

- Unicode-Homoglyphen (kyrillisches "а" statt lateinischem "a")
- Zero-Width-Spaces und unsichtbare Steuerzeichen
- Leetspeak-Varianten ("M@x1" → "Maxi")
- Mehrfach-Leerzeichen und NBSP

Die Normalisierung wirkt ausschließlich auf die Detection-Eingabe. Für Platzhalter-Ersetzung und Mapping wird der Original-Text verwendet, sodass die Ausgabe den Input 1:1 spiegelt (abgesehen von PII-Ersetzungen).

## 3.2 Entity-Resolver

`anomyze/pipeline/entity_resolver.py` verknüpft Detections, die dieselbe reale Entität meinen. In längeren Dokumenten (Bescheiden, Protokollen, Anfragen) wird eine Person oft mehrfach und unterschiedlich genannt — "Maria Gruber", "Frau Gruber", "M. Gruber". Der Resolver kombiniert:

- Teilstring-/Token-Matching,
- Kölner Phonetik (`anomyze/pipeline/phonetic.py`) für Schreibweisen-Varianten,
- Title-/Anrede-Heuristik.

Verknüpfte Varianten erhalten denselben Platzhalter (`[PERSON_1]`), was Konsistenz und Lesbarkeit erhöht und Re-Identifikation durch Kreuzlesen verhindert.

## 3.3 Quality-Check

`anomyze/pipeline/quality_check.py` scannt nach der Channel-Verarbeitung die finale Ausgabe erneut mit Regex-Mustern. Treffer zeigen Residuen an, die alle vorherigen Stufen überstanden haben. Relevant besonders für IFG, weil dort keine nachträgliche Re-Identifikation möglich ist. Der Report landet auf `result.quality_report` und kann pro Request ausgewertet werden.

---

# 4. Erkannte PII-Typen

| entity_group | Beispiel | Primäre Quelle |
|--------------|----------|----------------|
| PER | Maria Gruber | NER + AT-Namensliste + Phonetik |
| ORG | Bundesministerium für Inneres | NER |
| ORG_DETECTED | Merkur, Goldfinch | Kontext-Perplexität |
| LOC | Wien, Graz | NER |
| ADRESSE | Schottenfeldgasse 29/3, 1070 Wien | Regex |
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

---

# 5. Benchmark-Framework

Unter `anomyze/benchmark/` liegt ein Framework, das die Pipeline gegen annotierte Ground-Truth-Datensätze vergleicht:

```bash
python -m anomyze.benchmark benchmarks/datasets/synthetic_at.json
python -m anomyze.benchmark benchmarks/datasets/realistic_at.json --json
python -m anomyze.benchmark my_dataset.json --with-mlm --with-gliner
```

Der Report liefert Precision, Recall und F1

- pro Kategorie (welche PII-Typen werden wie gut erkannt),
- pro Detection-Layer (welcher Layer trägt wie viel bei),
- global.

Die mitgelieferten Datasets:

- `benchmarks/datasets/synthetic_at.json` — 25 kurze AT-PII-Sätze, bewusst fiktive Werte (example.at, IBANs mit Null-Blöcken, Dummy-SVNR).
- `benchmarks/datasets/realistic_at.json` — 6 längere AT-Dokumente (Bescheid, parlamentarische Anfrage, Einvernahmeprotokoll, Ladung, Zahlungsaufforderung, Meldung) mit 41 annotierten PII.

Eigene Datasets folgen einem einfachen JSON-Schema mit `id`, `text` und annotierten `entities` (`start`, `end`, `type`). Details unter `benchmarks/README.md`.

Das Framework ist bewusst dependency-frei (pure Python + stdlib) und macht Regression-Detection in CI trivial: ein Ground-Truth-Dataset, ein `--json`-Aufruf, ein Diff gegen die letzte Baseline.

---

# 6. Deployment

## 6.1 Python Library

```python
from anomyze import PipelineOrchestrator

orch = PipelineOrchestrator()
orch.load_models()

result = orch.process("Maria Gruber, SVNr. 1234 140387", channel="govgpt")
print(result.text)     # [PERSON_1], SVNr. [SVNR_1]
print(result.mapping)  # {"[PERSON_1]": "Maria Gruber", "[SVNR_1]": "1234 140387"}
```

## 6.2 CLI

```bash
anomyze input.txt output.txt                    # GovGPT (Default)
anomyze input.txt output.txt --channel ifg      # Irreversible Schwärzung
anomyze input.txt output.txt --channel kapa     # Mit Audit-Trail
anomyze --interactive --channel govgpt          # Interaktiver Modus
```

## 6.3 REST API

```bash
uvicorn anomyze.api.main:app --host 0.0.0.0 --port 8000
```

Endpunkte unter `/api/v1/`:

| Methode | Pfad | Beschreibung |
|---------|------|--------------|
| POST | `/anonymize` | Text anonymisieren (mit optionalem `settings_override`) |
| GET | `/health` | Modell-Status und Device |
| GET | `/mappings/{document_id}` | Mapping abrufen (GovGPT/KAPA) |
| DELETE | `/mappings/{document_id}` | Mapping löschen |
| GET | `/audit/{document_id}` | Audit-Trail abrufen (KAPA) |

Pro Request können Thresholds und Feature-Flags temporär überschrieben werden, was Integrationstests und A/B-Szenarien ohne Service-Restart erlaubt.

## 6.4 Docker

```bash
docker-compose up --build
```

Das mitgelieferte `Dockerfile` baut ein Image mit vorgeladenen Modellen und exponiert die REST API auf Port 8000.

## 6.5 Konfiguration

Alle Einstellungen via Umgebungsvariablen:

| Variable | Default | Beschreibung |
|----------|---------|--------------|
| `ANOMYZE_DEVICE` | auto | cpu, cuda, mps |
| `ANOMYZE_PII_THRESHOLD` | 0.7 | Schwelle PII-Modell |
| `ANOMYZE_ORG_THRESHOLD` | 0.7 | Schwelle ORG-Modell |
| `ANOMYZE_GLINER_THRESHOLD` | 0.4 | Schwelle GLiNER |
| `ANOMYZE_ANOMALY_THRESHOLD` | 0.5 | Finale Score-Schwelle |
| `ANOMYZE_PERPLEXITY_THRESHOLD` | 0.3 | Kontext-Anomalie-Schwelle |
| `ANOMYZE_USE_GLINER` | true | GLiNER-Layer an/aus |
| `ANOMYZE_DEFAULT_CHANNEL` | govgpt | Default-Kanal |
| `ANOMYZE_KAPA_REVIEW_THRESHOLD` | 0.85 | KAPA-Review-Schwelle |
| `ANOMYZE_AUDIT_ENABLED` | false | Audit-Logging an/aus |
| `ANOMYZE_AUDIT_LOG_PATH` | - | Audit-Log-Dateipfad |
| `ANOMYZE_MAPPING_PERSIST_PATH` | - | Persistenz-Pfad für Mappings |

---

# 7. Modelle und Lizenzen

| Modell | Zweck | Größe | Lizenz |
|--------|-------|-------|--------|
| HuggingLil/pii-sensitive-ner-german | PII-NER | ~1.3 GB | siehe HF-Repo |
| Davlan/xlm-roberta-large-ner-hrl | NER (Org/Loc/Per) | ~2.2 GB | MIT / Apache 2.0 (siehe HF-Repo) |
| dbmdz/bert-base-german-cased | MLM | ~0.4 GB | MIT |
| urchade/gliner_large-v2.1 | GLiNER Zero-Shot | ~1.7 GB | Apache 2.0 |

Alle Modelle laufen 100 % lokal. Der erste Start lädt die Modelle einmalig via HuggingFace Hub; danach ist keine Netzwerkverbindung mehr nötig. Für air-gapped Deployments lassen sich die Modell-Artefakte vorab mirroren.

---

# 8. Souveränität und DSGVO

Anomyze ist als Output-Filter konzipiert, der an der Systemgrenze wirkt. Für die Rechtsgrundlage relevant:

- **100 % lokal:** Keine Drittstaaten-Übermittlung, keine Auftragsverarbeitung an US-Cloud-Provider.
- **IFG-Kanal irreversibel:** Weder Mapping noch Original-Text werden persistiert. Privacy by Default.
- **GovGPT/KAPA reversibel mit Zweckbindung:** Mapping-Abruf erfordert explizite `GET /mappings/{id}`-Autorisierung; Löschung via `DELETE` jederzeit möglich.
- **KAPA-Audit-Trail:** Jede Detection ist mit Zeitstempel, Konfidenz, Quell-Layer und Kontext-Snippet protokolliert — nachvollziehbar für parlamentarische Kontrolle.
- **Quality-Check:** Residuen-Erkennung am Ende der Pipeline. Dokumentiert das Restrisiko, anstatt es zu verschweigen.

---

# 9. Entwicklung

## 9.1 Installation

```bash
pip install -e .          # Kernpaket
pip install -e ".[api]"   # + REST API
pip install -e ".[dev]"   # + Testing, Linting, Type-Checking
```

## 9.2 Qualitätssicherung

- **ruff** für Linting (`[E, F, W, I, UP, B, C4]`-Regeln).
- **mypy** für Type-Checking (`warn_return_any`, `warn_unused_configs`).
- **pytest** für die Testsuite (Unit + Integration + Adversarial + Benchmark).
- **Benchmark** für Detection-Qualität-Regressionen.

Die Testsuite deckt Regex-Patterns, Ensemble-Merging, Entity-Resolver, adversariale Normalisierung, Pipeline-Integration und das Benchmark-Framework ab. ML-Modelle werden pro Prozess einmal geladen (~8 GB) — entsprechend läuft nur ein pytest-Prozess gleichzeitig.

## 9.3 Roadmap

Anomyze Core ist mit v2.0 funktional abgeschlossen. Geplante Extensions (separates Repository `anomyze-extension`):

- Browser-Extension (Manifest V3) mit lokalem Regex-Fallback,
- Admin-UI für Regelverwaltung und Audit-Auswertung,
- SSO-Integration (SAML/OIDC, Entra ID),
- Kubernetes-Deployment-Manifeste.

---

# 10. Referenzen

- Projekt-Homepage: [anomyze.it](https://anomyze.it)
- Repository: [github.com/slavkoklincov/anomyze](https://github.com/slavkoklincov/anomyze)
- Architektur-Doku: `docs/architecture.md`
- API-Referenz: `docs/api_reference.md`
- Benchmark-Doku: `benchmarks/README.md`
- Lizenz: MIT

---

*Whitepaper v2.0 — April 2026*
