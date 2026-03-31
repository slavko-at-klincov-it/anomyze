# Anomyze Architektur

## Überblick

Anomyze ist eine souveräne KI-Anonymisierungsschicht für die österreichische Bundesverwaltung. Es ist der **Output-Filter** der "Public AI"-Initiative: Die KI-Tools (GovGPT, ELAK-KI, KAPA) arbeiten intern mit den vollen Daten — sie brauchen PII um zu funktionieren. Anomyze prüft und filtert den Output, bevor er das System verlässt.

## 3-Stufen-Pipeline

```
KI-Tool (GovGPT / ELAK-KI / KAPA)
  arbeitet intern mit vollen Daten
     │
     ▼
KI-generierter Output
     │
     ▼
┌─────────────────────┐
│  Preprocessing      │  fix_encoding() — OCR/Transkriptions-Fehler
└─────────┬───────────┘
          ▼
┌─────────────────────┐
│  Stufe 1: Regex     │  Österreich-spezifische Muster
│  (regex_layer.py)   │  SVNr, IBAN, KFZ, Aktenzahl, Geburtsdaten,
│                     │  Telefon, Email, Reisepass, Steuernummer
└─────────┬───────────┘
          ▼
┌─────────────────────┐
│  Stufe 2: NER       │  HuggingFace Transformer-Modelle
│  (ner_layer.py)     │  PII-Modell: Namen, Emails, Telefon
│                     │  NER-Modell: Organisationen, Orte
└─────────┬───────────┘
          ▼
┌─────────────────────┐
│  Stufe 3: Kontext   │  Perplexitäts-basierte Anomalie-Erkennung
│  (context_layer.py) │  Erkennt unbekannte Firmennamen via MLM
└─────────┬───────────┘
          ▼
┌─────────────────────┐
│  Kanal-Auswahl      │  govgpt / ifg / kapa
└───┬─────┬─────┬─────┘
    ▼     ▼     ▼
 GovGPT  IFG  KAPA
    │     │     │
    ▼     ▼     ▼
 Gefilterter Output verlässt das System
```

## 3 Ausgabe-Kanäle

### GovGPT-Kanal
- **Zweck:** KI-generierte Antworten und Berichte filtern, bevor sie an Bedienstete weitergegeben werden
- **Verhalten:** PII → nummerierte Platzhalter ([PERSON_1], [IBAN_1])
- **Mapping:** Platzhalter → Original wird gespeichert (re-identifizierbar für autorisierte User)
- **Anwendung:** GovGPT, ELAK-KI — Output-Filterung vor Weitergabe

### IFG-Kanal (Informationsfreiheitsgesetz)
- **Zweck:** KI-generierte Outputs schwärzen, bevor sie auf data.gv.at veröffentlicht werden
- **Verhalten:** PII → [GESCHWÄRZT:KATEGORIE] (ohne Nummerierung)
- **Mapping:** Kein Mapping — irreversibel by design
- **Schwärzungsprotokoll:** Kategorie + Anzahl (nie Originalwerte)
- **DSGVO:** Kein Rückweg, original_text wird nicht gespeichert

### KAPA-Kanal (Parlamentarische Anfragen)
- **Zweck:** KI-Rechercheergebnisse filtern, bevor sie als parlamentarische Antworten das System verlassen
- **Verhalten:** Wie GovGPT + vollständiger Audit-Trail
- **Human-in-the-Loop:** Entitäten unter Konfidenz-Schwelle → [PRÜFEN:TYPE_N]
- **Audit-Trail:** Zeitstempel, Konfidenz, Quell-Layer, Kontext-Snippet

## Paketstruktur

```
anomyze/
├── api/                    FastAPI REST-Endpunkte
│   ├── main.py             App-Factory mit Model-Preloading
│   ├── routes.py           POST /anonymize, GET /health, ...
│   └── models.py           Pydantic Request/Response Schemas
├── pipeline/               Kern-Pipeline
│   ├── __init__.py         DetectedEntity Dataclass
│   ├── orchestrator.py     3-Stufen-Steuerung + ModelManager
│   ├── regex_layer.py      Stufe 1: Regex-Erkennung
│   ├── ner_layer.py        Stufe 2: NER-Modelle
│   ├── context_layer.py    Stufe 3: Anomalie-Erkennung
│   └── utils.py            Entity-Utilities (Overlap, Cleaning)
├── channels/               3-Kanal-Output
│   ├── base.py             Abstrakte Basis-Klasse
│   ├── govgpt.py           Platzhalter + Mapping
│   ├── ifg.py              Irreversible Schwärzung
│   └── kapa.py             Platzhalter + Audit-Trail
├── mappings/
│   └── mapping_store.py    Platzhalter ↔ Original Zuordnung
├── audit/
│   └── logger.py           Audit-Trail Logging
├── patterns/
│   └── at_patterns.py      Österreich-spezifische Regex-Muster
├── config/
│   └── settings.py         Zentrale Konfiguration
└── cli.py                  Kommandozeilen-Interface
```

## Modelle

| Modell | Zweck | Größe |
|--------|-------|-------|
| HuggingLil/pii-sensitive-ner-german | PII-Erkennung (Namen, Emails, Telefon) | ~1.3 GB |
| dslim/bert-base-NER | NER (Organisationen, Orte) | ~0.4 GB |
| dbmdz/bert-base-german-cased | MLM für Anomalie-Erkennung | ~0.4 GB |

Alle Modelle laufen 100% lokal — kein Cloud-Call, kein API-Call nach außen.

## Erkannte PII-Typen

| Typ | Beispiel | Erkennung |
|-----|----------|-----------|
| PERSON | Maria Gruber | NER + Regex (Titel) |
| ORGANISATION | Bundesministerium für Inneres | NER + Perplexität |
| ORT | Wien, Graz | NER |
| EMAIL | m.gruber@gmail.com | Regex |
| IBAN | AT61 1904 3002 3457 3201 | Regex |
| SVNR | 1234 140387 | Regex + Datumsvalidierung |
| STEUERNUMMER | 12-345/6789 | Regex |
| GEBURTSDATUM | 14.03.1987 | Regex |
| AKTENZAHL | GZ BMI-2024/0815 | Regex |
| REISEPASS | P1234567 | Regex (kontext-gesteuert) |
| PERSONALAUSWEIS | AB123456CD | Regex (kontext-gesteuert) |
| KFZ | W-34567B | Regex (Bezirk-Codes) |
| TELEFON | +43 664 1234567 | Regex |
