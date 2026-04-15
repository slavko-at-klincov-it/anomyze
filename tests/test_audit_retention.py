"""Tests for AuditLogger retention and forget()."""

from datetime import datetime, timedelta, timezone

from anomyze.audit.logger import AuditEntry, AuditLogger, RetentionPolicy


def _entry(doc_id: str, days_ago: int) -> AuditEntry:
    ts = datetime.now(timezone.utc) - timedelta(days=days_ago)
    return AuditEntry(
        timestamp=ts.isoformat(),
        document_id=doc_id,
        entity_word="Maria Gruber",
        entity_group="PERSON",
        confidence=0.95,
        source_layer="pii",
        action="anonymized",
        placeholder="[PERSON_1]",
        context_snippet="...[PERSON_1] kam...",
    )


class TestForget:
    def test_removes_all_entries_for_document(self) -> None:
        log = AuditLogger()
        log.log_batch([
            _entry("doc-1", 0),
            _entry("doc-1", 1),
            _entry("doc-2", 0),
        ])
        removed = log.forget("doc-1")
        assert removed == 2
        assert log.get_entries("doc-1") == []
        assert len(log.get_entries("doc-2")) == 1

    def test_unknown_doc_returns_zero(self) -> None:
        log = AuditLogger()
        assert log.forget("nope") == 0


class TestRetention:
    def test_redact_pii_after_grace(self) -> None:
        log = AuditLogger(retention=RetentionPolicy(pii_redact_after_days=7))
        log.log_batch([
            _entry("fresh", 1),    # within grace → keep PII
            _entry("stale", 30),   # past grace → redact
        ])
        result = log.enforce_retention()
        assert result["redacted"] == 1
        assert log.get_entries("fresh")[0].entity_word == "Maria Gruber"
        assert log.get_entries("stale")[0].entity_word == "[REDACTED]"

    def test_hard_delete_after_threshold(self) -> None:
        log = AuditLogger(retention=RetentionPolicy(hard_delete_after_days=30))
        log.log_batch([
            _entry("recent", 5),
            _entry("ancient", 90),
        ])
        result = log.enforce_retention()
        assert result["deleted"] == 1
        assert log.get_entries("ancient") == []
        assert len(log.get_entries("recent")) == 1

    def test_redact_idempotent(self) -> None:
        log = AuditLogger(retention=RetentionPolicy(pii_redact_after_days=1))
        log.log_batch([_entry("a", 30)])
        log.enforce_retention()
        # Second invocation should not double-count
        result = log.enforce_retention()
        assert result["redacted"] == 0
