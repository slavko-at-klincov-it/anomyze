#!/usr/bin/env bash
# Encrypted audit-log backup for Anomyze.
#
# Expects /etc/anomyze/backup.env with:
#   ANOMYZE_AUDIT_SRC=/var/lib/anomyze/audit/audit.json
#   ANOMYZE_BACKUP_DIR=/srv/backup/anomyze
#   ANOMYZE_BACKUP_RECIPIENT=dsb@behoerde.gv.at
#   ANOMYZE_BACKUP_RETENTION_DAYS=2555  # 7 Jahre BAO
#
# Install as /usr/local/bin/anomyze-audit-backup, executable, root-owned.

set -euo pipefail

: "${ANOMYZE_AUDIT_SRC:?ANOMYZE_AUDIT_SRC required}"
: "${ANOMYZE_BACKUP_DIR:?ANOMYZE_BACKUP_DIR required}"
: "${ANOMYZE_BACKUP_RECIPIENT:?ANOMYZE_BACKUP_RECIPIENT required}"
: "${ANOMYZE_BACKUP_RETENTION_DAYS:=2555}"

mkdir -p "$ANOMYZE_BACKUP_DIR"
chmod 0700 "$ANOMYZE_BACKUP_DIR"

TS=$(date -u +%Y%m%dT%H%M%SZ)
OUT="$ANOMYZE_BACKUP_DIR/audit-${TS}.tar.gz.gpg"

# tar + gzip + GPG-verschlüsselt an DSB. Kein Zwischen-Entpacken im
# Klartext; pipe direkt in gpg.
tar -czf - "$ANOMYZE_AUDIT_SRC" \
    | gpg --batch --yes --trust-model always \
          --recipient "$ANOMYZE_BACKUP_RECIPIENT" \
          --encrypt \
          --output "$OUT"

chmod 0600 "$OUT"

# Retention der Backups respektieren.
find "$ANOMYZE_BACKUP_DIR" -name 'audit-*.tar.gz.gpg' \
    -mtime "+${ANOMYZE_BACKUP_RETENTION_DAYS}" -delete

echo "backup ok: $OUT"
