"""Tests for the Prometheus metrics endpoint and instrumentation.

Requires the ``observability`` extra (``pip install -e '.[observability]'``).
Skipped automatically when ``prometheus_fastapi_instrumentator`` is absent.
"""

import pytest

pytest.importorskip("prometheus_fastapi_instrumentator")

from unittest.mock import MagicMock  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from anomyze.api.main import create_app
from anomyze.audit.logger import AuditLogger
from anomyze.config.settings import Settings, configure
from anomyze.mappings.mapping_store import MappingStore
from anomyze.pipeline.orchestrator import PipelineOrchestrator


@pytest.fixture
def client():
    settings = Settings(use_anomaly_detection=False, device="cpu")
    configure(settings)
    orchestrator = PipelineOrchestrator(settings)
    orchestrator.model_manager._pii_pipeline = MagicMock(return_value=[])
    orchestrator.model_manager._org_pipeline = MagicMock(return_value=[])
    orchestrator.model_manager._mlm_pipeline = MagicMock(return_value=[])
    orchestrator.model_manager._device = "cpu"
    orchestrator.model_manager._device_name = "CPU [test]"

    app = create_app(settings)
    app.state.orchestrator = orchestrator
    app.state.mapping_store = MappingStore()
    app.state.audit_logger = AuditLogger()
    app.state.settings = settings

    with TestClient(app, raise_server_exceptions=True) as c:
        yield c


class TestMetricsEndpoint:
    def test_metrics_endpoint_reachable(self, client) -> None:
        response = client.get("/metrics")
        assert response.status_code == 200
        # Standard Prometheus text exposition format.
        assert response.headers["content-type"].startswith("text/plain")

    def test_custom_metrics_present(self, client) -> None:
        # Trigger one channel request so the counters have non-empty
        # series to render.
        client.post(
            "/api/v1/anonymize",
            json={"text": "Mail an maria@example.at", "channel": "govgpt"},
        )
        response = client.get("/metrics")
        body = response.text
        # HELP / TYPE lines appear regardless of whether a label set
        # has been observed yet.
        assert "anomyze_entity_detected_total" in body
        assert "anomyze_channel_requests_total" in body
        assert "anomyze_pipeline_stage_duration_seconds" in body
        assert "anomyze_confidence_score" in body


class TestChannelCounter:
    def test_channel_counter_increments(self, client) -> None:
        client.post(
            "/api/v1/anonymize",
            json={"text": "Hallo", "channel": "govgpt"},
        )
        body = client.get("/metrics").text
        assert 'anomyze_channel_requests_total{channel="govgpt"}' in body

    def test_two_requests_two_increments(self, client) -> None:
        for _ in range(2):
            client.post(
                "/api/v1/anonymize",
                json={"text": "Hallo", "channel": "kapa"},
            )
        body = client.get("/metrics").text
        # Two calls on the same label -> value 2.0
        for line in body.splitlines():
            if line.startswith('anomyze_channel_requests_total{channel="kapa"}'):
                assert line.endswith("2.0") or line.endswith(" 2")
                break
        else:  # pragma: no cover
            raise AssertionError("channel counter not rendered")


class TestNoPIIInMetrics:
    def test_entity_word_never_appears_in_metrics(self, client) -> None:
        client.post(
            "/api/v1/anonymize",
            json={
                "text": "Kontakt: maria.huber@example.at, IBAN AT61 1904 3002 3457 3201",
                "channel": "govgpt",
            },
        )
        body = client.get("/metrics").text
        assert "maria.huber" not in body
        assert "example.at" not in body
        # Redacted IBAN digits must not leak via labels either.
        assert "1904 3002" not in body
