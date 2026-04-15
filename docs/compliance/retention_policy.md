# Aufbewahrungs- und Löschfristen

Anomyze speichert je nach Kanal unterschiedlich. Die Defaults sind
konservativ und sollten an die spezifischen fachgesetzlichen Vorgaben
angepasst werden (z.B. BAO 7 Jahre, AVG 30 Jahre Akten).

## Mappings (GovGPT, KAPA)

- **Speicherort:** `Settings.mapping_persist_path` (JSON-Datei).
- **Default:** Aus — Mappings nur im Speicher der API-Instanz.
- **Empfohlene Frist:** ≤ 30 Tage. Reversibilität ist nur für die
  unmittelbare Bearbeitung vorgesehen.
- **Löschung:** `DELETE /api/v1/mappings/{document_id}`.

## Audit-Trail (KAPA)

- **Speicherort:** `Settings.audit_log_path` (JSON-Datei).
- **Default-Retention:** Siehe `RetentionPolicy` in
  `anomyze/audit/logger.py`:
  - `pii_redact_after_days = 7` — Original-PII wird nach 7 Tagen
    durch `[REDACTED]` ersetzt; der Audit-Eintrag bleibt nachvollziehbar.
  - `max_age_days = 90` — empfohlener Soft-Cutoff für externe
    Rotation (z.B. Loki / SIEM).
  - `hard_delete_after_days = 2555` — Hard-Delete nach 7 Jahren
    (BAO-Aufbewahrung).
- **Operativ:** `AuditLogger.enforce_retention()` im Cron-Intervall
  ausführen (täglich genügt).

## Originaltext (IFG-Kanal)

- Wird **nicht** persistiert (DSGVO-konform — `original_text=""`).

## Recht auf Vergessenwerden (Art. 17)

- API: `DELETE /api/v1/mappings/{document_id}` entfernt das Mapping.
- Code: `AuditLogger.forget(document_id)` entfernt sämtliche
  Audit-Einträge zu einem Dokument.

## Verantwortliche Pflege

- DSB verifiziert quartalsweise die effektive Anwendung der Retention.
- Bei Änderungen der Defaults: Anpassung in
  `anomyze/audit/logger.py` (`RetentionPolicy`-Defaults) und
  Aktualisierung dieses Dokuments.
