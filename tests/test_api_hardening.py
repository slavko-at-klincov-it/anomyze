"""Tests for the API hardening middleware (rate limit, body size, headers).

Uses a dedicated test client with mocked pipelines so the middleware
is exercised without paying the 8 GB model-load cost on every run.
"""

from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from anomyze.api.main import create_app
from anomyze.audit.logger import AuditLogger
from anomyze.config.settings import Settings, configure
from anomyze.mappings.mapping_store import MappingStore
from anomyze.pipeline.orchestrator import PipelineOrchestrator


def _build_client(settings: Settings) -> TestClient:
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
    return TestClient(app, raise_server_exceptions=True)


@pytest.fixture
def client():
    settings = Settings(use_anomaly_detection=False, device="cpu")
    with _build_client(settings) as c:
        yield c


class TestBodySizeMiddleware:
    def test_small_body_accepted(self, client) -> None:
        response = client.post(
            "/api/v1/anonymize",
            json={"text": "Hallo Welt", "channel": "govgpt"},
        )
        assert response.status_code == 200

    def test_oversized_body_returns_413(self, client) -> None:
        # 600 KB raw body > 500_000 default cap
        oversize = "x" * 600_000
        body = f'{{"text":"{oversize}","channel":"govgpt"}}'
        response = client.post(
            "/api/v1/anonymize",
            content=body,
            headers={"content-type": "application/json"},
        )
        assert response.status_code == 413
        assert "exceeds" in response.text.lower()

    def test_custom_body_limit_raised(self) -> None:
        # Raising the cap lets a 600 KB body through; the ValidatorCheck
        # on text (max 50_000 chars) still applies, but a smaller text
        # inside a large body must succeed.
        settings = Settings(
            use_anomaly_detection=False,
            device="cpu",
            max_request_body_bytes=2_000_000,
        )
        with _build_client(settings) as c:
            padding = " " * 600_000
            response = c.post(
                "/api/v1/anonymize",
                content=(
                    f'{{"text":"Hallo","channel":"govgpt","_padding":"{padding}"}}'
                ),
                headers={"content-type": "application/json"},
            )
            # Pydantic rejects the unknown _padding field by default,
            # but the middleware did NOT block the body — which is
            # what this test is asserting. Any response other than
            # 413 proves the middleware let the large body through.
            assert response.status_code != 413


class TestSecurityHeaders:
    def test_health_response_has_hardening_headers(self, client) -> None:
        pytest.importorskip("secure")
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        headers = {k.lower(): v for k, v in response.headers.items()}
        assert headers.get("x-content-type-options", "").lower() == "nosniff"


class TestRateLimit:
    def test_rate_limit_does_not_error_on_normal_use(self, client) -> None:
        # A handful of requests stay below the 60/min default.
        for _ in range(3):
            response = client.post(
                "/api/v1/anonymize",
                json={"text": "Hallo", "channel": "govgpt"},
            )
            assert response.status_code == 200


class TestHardeningGracefulDegrade:
    def test_app_boots_without_slowapi(self, monkeypatch) -> None:
        # Simulate the hardening extra being absent. create_app must
        # still return a working application that serves /health.
        from anomyze.api import hardening
        monkeypatch.setattr(hardening, "_SLOWAPI", False)
        monkeypatch.setattr(hardening, "_SECURE", False)

        settings = Settings(use_anomaly_detection=False, device="cpu")
        with _build_client(settings) as c:
            response = c.get("/api/v1/health")
            assert response.status_code == 200
