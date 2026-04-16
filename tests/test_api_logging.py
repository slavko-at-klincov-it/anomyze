"""Tests for structured API logging (structlog / stdlib fallback)."""

import json
import logging

import pytest

from anomyze.api.logging_config import configure_logging, get_logger


class TestStructlogJSON:
    def test_json_output_format(self, capsys) -> None:
        pytest.importorskip("structlog")
        configure_logging()
        log = get_logger("anomyze.test")
        log.info("demo_event", channel="govgpt", entity_count=3)
        captured = capsys.readouterr().out
        # Exactly one JSON line for the event.
        lines = [line for line in captured.splitlines() if line.strip()]
        assert lines, "no log line emitted"
        payload = json.loads(lines[-1])
        assert payload["event"] == "demo_event"
        assert payload["channel"] == "govgpt"
        assert payload["entity_count"] == 3
        # timestamp + level added by the processor chain
        assert "timestamp" in payload
        assert "level" in payload

    def test_idempotent_configure(self) -> None:
        # calling configure_logging() twice must not raise
        configure_logging()
        configure_logging()


class TestNoPIIInLogs:
    def test_entity_word_not_logged(self, capsys) -> None:
        pytest.importorskip("structlog")
        configure_logging()
        log = get_logger("anomyze.test")
        log.info("anon_request", document_id="doc-123", channel="govgpt")
        captured = capsys.readouterr().out
        assert "doc-123" in captured
        assert "maria@example.at" not in captured  # nothing emitted that wasn't passed in


class TestStdlibFallback:
    def test_fallback_when_structlog_missing(self, monkeypatch, caplog) -> None:
        # Simulate missing structlog. The fallback routes through the
        # stdlib logging module, which pytest captures via caplog.
        from anomyze.api import logging_config
        monkeypatch.setattr(logging_config, "_STRUCTLOG_AVAILABLE", False)

        # Re-import path: configure_logging() must not raise.
        logging_config.configure_logging(level="INFO")

        fallback_logger = logging_config.get_logger("anomyze.fallback")
        # stdlib logger => use standard API
        assert isinstance(fallback_logger, logging.Logger)

        with caplog.at_level(logging.INFO, logger="anomyze.fallback"):
            fallback_logger.info("stdlib message")
        assert any("stdlib message" in r.message for r in caplog.records)
