#!/usr/bin/env bash
# Restore an encrypted Anomyze audit-log backup.
#
# Usage: restore-audit.sh <path-to-audit-*.tar.gz.gpg>
#
# WARNING: after restore we immediately run enforce_retention() so the
# restored snapshot cannot reintroduce PII past its redaction or
# hard-delete deadline. A straight restore of a 2-year-old backup
# without this call would silently resurrect data that should have
# been wiped per DSGVO Art. 5(1)e.

set -euo pipefail

if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <encrypted-backup>" >&2
    exit 2
fi

BACKUP_FILE="$1"
: "${ANOMYZE_AUDIT_DST:=/var/lib/anomyze/audit}"

if [ ! -f "$BACKUP_FILE" ]; then
    echo "backup not found: $BACKUP_FILE" >&2
    exit 1
fi

STAGE=$(mktemp -d)
trap 'rm -rf "$STAGE"' EXIT

echo "==> decrypting $BACKUP_FILE"
gpg --decrypt --output "$STAGE/bundle.tar.gz" "$BACKUP_FILE"

echo "==> extracting"
tar -xzf "$STAGE/bundle.tar.gz" -C "$STAGE"

echo "==> placing audit.json at $ANOMYZE_AUDIT_DST"
mkdir -p "$ANOMYZE_AUDIT_DST"
install -m 0600 "$STAGE"/var/lib/anomyze/audit/audit.json \
                "$ANOMYZE_AUDIT_DST/audit.json"

echo "==> re-enforcing retention (mandatory after restore)"
docker exec anomyze-anomyze-1 \
    python -c "\
from pathlib import Path; \
from anomyze.audit.logger import AuditLogger; \
log = AuditLogger(log_path=Path('/var/lib/anomyze/audit/audit.json')); \
print(log.enforce_retention())"

echo "restore ok"
