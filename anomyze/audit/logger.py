"""
Audit logging for anonymization operations.

Provides structured audit trail logging for the KAPA channel,
enabling parliamentary accountability and human-in-the-loop review.
Every anonymization action is logged with timestamp, confidence,
source layer, and a sanitized context snippet.

IMPORTANT: Context snippets are sanitized — they show the placeholder,
not the original PII, to prevent audit log leakage.
"""

import csv
import io
import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class RetentionPolicy:
    """Audit-log retention policy.

    Implements DSGVO Art. 5(1)(e) Speicherbegrenzung in three tiers:

    * ``pii_redact_after_days`` — after this many days the original
      ``entity_word`` is wiped (set to ``"[REDACTED]"``); the audit
      entry itself is retained for accountability.
    * ``max_age_days`` — soft retention used by external rotation
      tooling. Not enforced automatically, but exposed via
      ``enforce_retention()``.
    * ``hard_delete_after_days`` — entries older than this are
      removed entirely. Defaults to seven years (BAO).
    """

    pii_redact_after_days: int = 7
    max_age_days: int = 90
    hard_delete_after_days: int = 7 * 365


@dataclass
class AuditEntry:
    """A single audit log entry for an anonymization action.

    Attributes:
        timestamp: ISO 8601 timestamp of the action.
        document_id: Unique document identifier.
        entity_word: The original PII value (stored securely, not in exports).
        entity_group: PII category (PERSON, IBAN, etc.).
        confidence: Detection confidence score (0.0-1.0).
        source_layer: Which pipeline layer detected this (regex, pii, org, perplexity).
        action: What was done (anonymized, flagged_for_review).
        placeholder: The placeholder that replaced the PII.
        context_snippet: Sanitized context (~30 chars before/after, PII masked).
        reviewer: Who reviewed the flagged entity (None until reviewed).
        review_decision: Review outcome (confirmed, rejected, modified, or None).
    """

    timestamp: str
    document_id: str
    entity_word: str
    entity_group: str
    confidence: float
    source_layer: str
    action: str
    placeholder: str
    context_snippet: str
    reviewer: str | None = None
    review_decision: str | None = None

    def to_dict(self, include_pii: bool = False) -> dict:
        """Convert to dictionary for serialization.

        Args:
            include_pii: If True, include the original entity_word.
                Defaults to False for security.

        Returns:
            Dictionary representation of the audit entry.
        """
        result = {
            "timestamp": self.timestamp,
            "document_id": self.document_id,
            "entity_group": self.entity_group,
            "confidence": round(self.confidence, 3),
            "source_layer": self.source_layer,
            "action": self.action,
            "placeholder": self.placeholder,
            "context_snippet": self.context_snippet,
        }
        if include_pii:
            result["entity_word"] = self.entity_word
        if self.reviewer:
            result["reviewer"] = self.reviewer
        if self.review_decision:
            result["review_decision"] = self.review_decision
        return result


class AuditLogger:
    """Structured audit logger for anonymization operations.

    Stores audit entries in memory and optionally persists them to
    a JSON log file. Supports export in JSON and CSV formats.
    """

    def __init__(
        self,
        log_path: Path | None = None,
        retention: RetentionPolicy | None = None,
    ):
        self._entries: list[AuditEntry] = []
        self.log_path = log_path
        self.retention = retention or RetentionPolicy()

        # Load existing entries from disk if available
        if log_path and log_path.exists():
            try:
                data = json.loads(log_path.read_text(encoding="utf-8"))
                if isinstance(data, list):
                    for item in data:
                        self._entries.append(AuditEntry(**item))
                    logger.info("Loaded %d audit entries from %s", len(data), log_path)
            except (json.JSONDecodeError, OSError, TypeError) as exc:
                logger.warning("Failed to load audit log from %s: %s", log_path, exc)

    def log(self, entry: AuditEntry) -> None:
        """Log a single audit entry.

        Args:
            entry: The audit entry to log.
        """
        self._entries.append(entry)
        self._persist()

    def log_batch(self, entries: list[AuditEntry]) -> None:
        """Log multiple audit entries at once.

        Args:
            entries: List of audit entries to log.
        """
        self._entries.extend(entries)
        self._persist()

    def get_entries(self, document_id: str) -> list[AuditEntry]:
        """Get all audit entries for a specific document.

        Args:
            document_id: The document ID to filter by.

        Returns:
            List of matching audit entries.
        """
        return [e for e in self._entries if e.document_id == document_id]

    def get_flagged(self, document_id: str | None = None) -> list[AuditEntry]:
        """Get all entries flagged for human review.

        Args:
            document_id: Optional document ID filter.

        Returns:
            List of flagged audit entries.
        """
        entries = self._entries
        if document_id:
            entries = [e for e in entries if e.document_id == document_id]
        return [e for e in entries if e.action == "flagged_for_review"]

    def export_json(
        self, document_id: str, include_pii: bool = False
    ) -> str:
        """Export audit entries for a document as JSON.

        Args:
            document_id: The document ID to export.
            include_pii: If True, include original PII values.

        Returns:
            JSON string of audit entries.
        """
        entries = self.get_entries(document_id)
        return json.dumps(
            [e.to_dict(include_pii=include_pii) for e in entries],
            indent=2,
            ensure_ascii=False,
        )

    def export_csv(
        self, document_id: str, include_pii: bool = False
    ) -> str:
        """Export audit entries for a document as CSV.

        Args:
            document_id: The document ID to export.
            include_pii: If True, include original PII values.

        Returns:
            CSV string of audit entries.
        """
        entries = self.get_entries(document_id)
        if not entries:
            return ""

        output = io.StringIO()
        fieldnames = list(entries[0].to_dict(include_pii=include_pii).keys())
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        for entry in entries:
            writer.writerow(entry.to_dict(include_pii=include_pii))
        return output.getvalue()

    def _persist(self) -> None:
        """Write entries to disk if persistence is configured."""
        if self.log_path is not None:
            try:
                self.log_path.parent.mkdir(parents=True, exist_ok=True)
                # Persist with PII for secure storage (access-controlled)
                data = [asdict(e) for e in self._entries]
                self.log_path.write_text(
                    json.dumps(data, indent=2, ensure_ascii=False),
                    encoding="utf-8",
                )
            except OSError as exc:
                logger.error("Failed to persist audit log to %s: %s", self.log_path, exc)

    # ------------------------------------------------------------------
    # DSGVO retention helpers
    # ------------------------------------------------------------------

    def forget(self, document_id: str) -> int:
        """Delete every entry for ``document_id`` (Art. 17 DSGVO)."""
        before = len(self._entries)
        self._entries = [e for e in self._entries if e.document_id != document_id]
        removed = before - len(self._entries)
        if removed:
            self._persist()
        return removed

    def enforce_retention(self, now: datetime | None = None) -> dict[str, int]:
        """Apply the configured ``RetentionPolicy``.

        * Redacts the ``entity_word`` field of entries older than
          ``pii_redact_after_days``.
        * Hard-deletes entries older than ``hard_delete_after_days``.
        * Returns a ``{redacted, deleted}`` summary suitable for
          operational logging.
        """
        if now is None:
            now = datetime.now(timezone.utc)

        redact_threshold = self.retention.pii_redact_after_days
        delete_threshold = self.retention.hard_delete_after_days

        kept: list[AuditEntry] = []
        redacted = 0
        deleted = 0

        for entry in self._entries:
            try:
                ts = datetime.fromisoformat(entry.timestamp)
            except ValueError:
                kept.append(entry)
                continue
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            age_days = (now - ts).total_seconds() / 86400.0

            if age_days > delete_threshold:
                deleted += 1
                continue
            if age_days > redact_threshold and entry.entity_word != "[REDACTED]":
                entry.entity_word = "[REDACTED]"
                redacted += 1
            kept.append(entry)

        self._entries = kept
        if redacted or deleted:
            self._persist()
        return {"redacted": redacted, "deleted": deleted}
