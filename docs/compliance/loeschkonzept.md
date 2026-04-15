# Löschkonzept Anomyze

Operative Anweisung zur Umsetzung der Löschpflichten gemäß Art. 17
DSGVO sowie der Aufbewahrungspflichten gemäß BAO / AVG.

## Auslöser

| Auslöser | Maßnahme | Frist |
|---|---|---|
| Antrag der/des Betroffenen | `forget(document_id)` + Mapping-Delete | 30 Tage |
| Ablauf der Speicherfrist (PII-Redaktion) | `enforce_retention()` (Cron) | täglich |
| Ablauf der Hard-Delete-Frist | `enforce_retention()` (Cron) | täglich |
| Revisionsende | Manuelles Audit-Export + Hard-Delete | 7 Jahre |

## Umsetzung

```bash
# Tägliches Retention-Cron (z.B. cron / systemd-timer)
python -c "
from pathlib import Path
from anomyze.audit.logger import AuditLogger
log = AuditLogger(log_path=Path('/var/log/anomyze/audit.json'))
print(log.enforce_retention())
"
```

## Nachweis

Jede Anwendung der Retention oder eines Forget-Requests wird selbst
geloggt (operatives Logging, nicht der PII-Audit-Trail) und ist
mindestens 5 Jahre aufzubewahren.

## Schnittstelle zur Behörden-IT

- Backup-Strategie muss `audit_log_path` einschließen.
- Restore von älteren Snapshots darf die Retention nicht umgehen — vor
  Wiederherstellung erneut `enforce_retention()` ausführen.
