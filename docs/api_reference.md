# Anomyze API Reference

## Base URL

```
http://localhost:8000/api/v1
```

## Endpoints

### POST /anonymize

Filter KI-generated output through the specified channel.

**Request Body:**
```json
{
  "text": "Maria Gruber, SVNr. 1234 140387",
  "channel": "govgpt",
  "document_id": "optional-custom-id",
  "settings_override": {
    "pii_threshold": 0.8,
    "anomaly_threshold": 0.6
  }
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| text | string | yes | Text to anonymize |
| channel | string | no | `govgpt` (default), `ifg`, `kapa` |
| document_id | string | no | Custom document ID (auto-generated UUID if omitted) |
| settings_override | object | no | Per-request threshold overrides |

**Response (GovGPT):**
```json
{
  "document_id": "abc-123",
  "channel": "govgpt",
  "text": "[PERSON_1], SVNr. [SVNR_1]",
  "entities": [
    {
      "word": "Maria Gruber",
      "entity_group": "PER",
      "score": 0.95,
      "start": 0,
      "end": 12,
      "source": "pii",
      "placeholder": "[PERSON_1]"
    }
  ],
  "entity_count": 2,
  "mapping": {
    "[PERSON_1]": "Maria Gruber",
    "[SVNR_1]": "1234 140387"
  }
}
```

**Response (IFG):**
```json
{
  "document_id": "abc-123",
  "channel": "ifg",
  "text": "[GESCHWÄRZT:PERSON], SVNr. [GESCHWÄRZT:SVNR]",
  "entities": [...],
  "entity_count": 2,
  "mapping": null,
  "redaction_protocol": [
    {
      "category": "PERSON",
      "count": 1,
      "min_confidence": 0.95,
      "max_confidence": 0.95
    }
  ]
}
```

**Response (KAPA):**
```json
{
  "document_id": "abc-123",
  "channel": "kapa",
  "text": "[PERSON_1], SVNr. [SVNR_1]",
  "entities": [...],
  "entity_count": 2,
  "mapping": {"[PERSON_1]": "Maria Gruber"},
  "flagged_for_review": ["[PRÜFEN:QUASI_ID_1]"],
  "audit_trail": [
    {
      "timestamp": "2026-03-31T10:00:00+00:00",
      "document_id": "abc-123",
      "entity_group": "PERSON",
      "confidence": 0.95,
      "source_layer": "pii",
      "action": "anonymized",
      "placeholder": "[PERSON_1]",
      "context_snippet": "...[PERSON_1], SVNr...."
    }
  ]
}
```

**Quasi-Identifikatoren im KAPA-Kanal:**

Passagen mit Kombinationen aus Rolle + Ort + Alter (ohne erkannten Namen) werden als `QUASI_ID` mit Konfidenz 0.70 erkannt und automatisch zur manuellen Prüfung geflaggt (`[PRÜFEN:QUASI_ID_N]`).

**Erkannte Entity-Typen:**

| entity_group | Placeholder | Erkennung |
|---|---|---|
| PER | PERSON | NER + Regex (Titel) |
| ORG / ORG_DETECTED | ORGANISATION | NER + Perplexität |
| LOC | ORT | NER |
| ADRESSE | ADRESSE | Regex (Straße+Nr, PLZ+Ort) |
| EMAIL | EMAIL | Regex |
| IBAN | IBAN | Regex |
| SVN | SVNR | Regex + Datumsvalidierung |
| STEUERNUMMER | STEUERNUMMER | Regex |
| GEBURTSDATUM | GEBURTSDATUM | Regex |
| AKTENZAHL | AKTENZAHL | Regex + AT-Recognizer |
| FIRMENBUCH | FIRMENBUCH | AT-Recognizer |
| REISEPASS | REISEPASS | Regex (kontext-gesteuert) |
| PERSONALAUSWEIS | PERSONALAUSWEIS | Regex (kontext-gesteuert) |
| KFZ | KFZ | Regex (AT-Bezirkscodes) |
| TELEFON | TELEFON | Regex |
| QUASI_ID | QUASI_ID | Kontext (Kombinations-Check) |

### GET /health

System health and model loading status.

**Response:**
```json
{
  "status": "healthy",
  "models_loaded": true,
  "device": "Apple Silicon GPU (MPS)",
  "version": "2.0.0"
}
```

### GET /mappings/{document_id}

Retrieve the placeholder mapping for a previously anonymized document.
Only available for GovGPT and KAPA channel results.

**Response:**
```json
{
  "document_id": "abc-123",
  "mapping": {
    "[PERSON_1]": "Maria Gruber",
    "[IBAN_1]": "AT61 1904 3002 3457 3201"
  }
}
```

### DELETE /mappings/{document_id}

Delete the mapping for a document. Returns 404 if not found.

### GET /audit/{document_id}

Retrieve the audit trail for a KAPA channel result.

**Response:**
```json
{
  "document_id": "abc-123",
  "entries": [...],
  "total": 5
}
```

## Docker

```bash
# Build and run
docker-compose up --build

# Test
curl -X POST http://localhost:8000/api/v1/anonymize \
  -H "Content-Type: application/json" \
  -d '{"text": "Maria Gruber, SVNr. 1234 140387", "channel": "govgpt"}'

curl http://localhost:8000/api/v1/health
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| ANOMYZE_DEVICE | auto | Compute device: cpu, cuda, mps |
| ANOMYZE_PII_THRESHOLD | 0.7 | PII detection confidence threshold |
| ANOMYZE_ORG_THRESHOLD | 0.7 | Organization detection threshold |
| ANOMYZE_ANOMALY_THRESHOLD | 0.5 | Minimum score for anonymization |
| ANOMYZE_PERPLEXITY_THRESHOLD | 0.3 | Anomaly detection threshold |
| ANOMYZE_DEFAULT_CHANNEL | govgpt | Default output channel |
| ANOMYZE_KAPA_REVIEW_THRESHOLD | 0.85 | Below this → flagged for review |
| ANOMYZE_AUDIT_ENABLED | false | Enable audit logging |
| ANOMYZE_AUDIT_LOG_PATH | - | Path for audit log file |
| ANOMYZE_API_HOST | 0.0.0.0 | API server host |
| ANOMYZE_API_PORT | 8000 | API server port |
| ANOMYZE_MAPPING_PERSIST_PATH | - | Path for JSON mapping persistence |
