"""Tests for the Anomyze REST API.

These tests use FastAPI's TestClient and mock the ML pipelines
to avoid downloading models during testing.
"""

import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from anomyze.api.main import create_app
from anomyze.config.settings import Settings
from anomyze.pipeline.orchestrator import PipelineOrchestrator
from anomyze.mappings.mapping_store import MappingStore
from anomyze.audit.logger import AuditLogger


@pytest.fixture
def mock_settings():
    """Create test settings with anomaly detection disabled."""
    return Settings(
        use_anomaly_detection=False,
        device="cpu",
    )


@pytest.fixture
def mock_orchestrator(mock_settings):
    """Create an orchestrator with mocked ML pipelines."""
    orchestrator = PipelineOrchestrator(mock_settings)

    # Mock the model manager to return mock pipelines
    mock_pii = MagicMock(return_value=[])
    mock_org = MagicMock(return_value=[])
    mock_mlm = MagicMock(return_value=[])

    orchestrator.model_manager._pii_pipeline = mock_pii
    orchestrator.model_manager._org_pipeline = mock_org
    orchestrator.model_manager._mlm_pipeline = mock_mlm
    orchestrator.model_manager._device = "cpu"
    orchestrator.model_manager._device_name = "CPU [test]"

    return orchestrator


@pytest.fixture
def client(mock_settings, mock_orchestrator):
    """Create a test client with mocked dependencies."""
    from anomyze.config.settings import configure
    configure(mock_settings)

    app = create_app(mock_settings)

    # Override lifespan by setting state directly
    app.state.orchestrator = mock_orchestrator
    app.state.mapping_store = MappingStore()
    app.state.audit_logger = AuditLogger()
    app.state.settings = mock_settings

    # Need to use the app without lifespan for testing
    with TestClient(app, raise_server_exceptions=True) as test_client:
        yield test_client


class TestHealthEndpoint:
    """Tests for GET /api/v1/health."""

    def test_health_returns_ok(self, client):
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "CPU" in data["device"]
        assert "version" in data

    def test_health_shows_models_loaded(self, client):
        response = client.get("/api/v1/health")
        data = response.json()
        assert data["models_loaded"] is True


class TestAnonymizeEndpoint:
    """Tests for POST /api/v1/anonymize."""

    def test_govgpt_channel_basic(self, client):
        response = client.post("/api/v1/anonymize", json={
            "text": "Kontakt: test@example.com",
            "channel": "govgpt",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["channel"] == "govgpt"
        assert "text" in data
        assert "entities" in data
        assert "entity_count" in data
        assert data["mapping"] is not None

    def test_ifg_channel_basic(self, client):
        response = client.post("/api/v1/anonymize", json={
            "text": "Kontakt: test@example.com",
            "channel": "ifg",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["channel"] == "ifg"
        assert data["mapping"] is None
        assert data["redaction_protocol"] is not None

    def test_kapa_channel_basic(self, client):
        response = client.post("/api/v1/anonymize", json={
            "text": "Kontakt: test@example.com",
            "channel": "kapa",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["channel"] == "kapa"
        assert data["mapping"] is not None
        assert data["audit_trail"] is not None

    def test_govgpt_detects_email(self, client):
        response = client.post("/api/v1/anonymize", json={
            "text": "Mail an maria@example.at",
            "channel": "govgpt",
        })
        data = response.json()
        assert data["entity_count"] >= 1
        assert "[EMAIL_1]" in data["text"]
        assert "maria@example.at" not in data["text"]

    def test_ifg_no_mapping_stored(self, client):
        response = client.post("/api/v1/anonymize", json={
            "text": "Mail an maria@example.at",
            "channel": "ifg",
            "document_id": "test-ifg-doc",
        })
        assert response.status_code == 200

        # Should NOT be able to retrieve mapping
        mapping_response = client.get("/api/v1/mappings/test-ifg-doc")
        assert mapping_response.status_code == 404

    def test_custom_document_id(self, client):
        response = client.post("/api/v1/anonymize", json={
            "text": "Mail an maria@example.at",
            "channel": "govgpt",
            "document_id": "my-custom-id",
        })
        data = response.json()
        assert data["document_id"] == "my-custom-id"

    def test_auto_generated_document_id(self, client):
        response = client.post("/api/v1/anonymize", json={
            "text": "Mail an maria@example.at",
            "channel": "govgpt",
        })
        data = response.json()
        assert data["document_id"]  # Should be a UUID

    def test_invalid_channel_returns_422(self, client):
        response = client.post("/api/v1/anonymize", json={
            "text": "Some text",
            "channel": "invalid",
        })
        assert response.status_code == 422

    def test_empty_text_returns_422(self, client):
        response = client.post("/api/v1/anonymize", json={
            "text": "",
            "channel": "govgpt",
        })
        assert response.status_code == 422

    def test_settings_override(self, client):
        response = client.post("/api/v1/anonymize", json={
            "text": "Kontakt: test@example.com",
            "channel": "govgpt",
            "settings_override": {
                "anomaly_threshold": 0.99,
            },
        })
        assert response.status_code == 200


class TestRequestSizeLimits:
    """Tests for configurable text-length and body-size limits."""

    def test_text_at_default_limit_accepted(self, client):
        # Default limit is 50_000; 49_999 chars must pass.
        text = "a" * 49_999
        response = client.post("/api/v1/anonymize", json={
            "text": text,
            "channel": "govgpt",
        })
        assert response.status_code == 200

    def test_text_above_default_limit_rejected(self, client):
        text = "a" * 60_000
        response = client.post("/api/v1/anonymize", json={
            "text": text,
            "channel": "govgpt",
        })
        # field_validator raises ValueError -> 422 from Pydantic
        assert response.status_code == 422
        assert "exceeds" in response.text.lower() or "value error" in response.text.lower()

    def test_body_size_middleware_rejects_oversized(self, client):
        # Default body cap is 500_000 bytes; send 600 KB raw body.
        oversize = "x" * 600_000
        response = client.post(
            "/api/v1/anonymize",
            content=f'{{"text":"{oversize}","channel":"govgpt"}}',
            headers={"content-type": "application/json"},
        )
        assert response.status_code == 413


class TestConfigurableTextLimit:
    """Settings-driven text limit can be raised."""

    def test_raised_limit_accepts_larger_text(self, mock_settings) -> None:
        from anomyze.api.models import AnonymizeRequest
        from anomyze.config.settings import Settings, configure

        big = Settings(use_anomaly_detection=False, device="cpu",
                       max_request_text_chars=200_000)
        configure(big)
        try:
            req = AnonymizeRequest(text="y" * 150_000, channel="govgpt")
            assert len(req.text) == 150_000
        finally:
            configure(mock_settings)

    def test_default_limit_rejects_oversized(self, mock_settings) -> None:
        from anomyze.api.models import AnonymizeRequest
        from anomyze.config.settings import configure

        configure(mock_settings)
        try:
            AnonymizeRequest(text="z" * 60_000, channel="govgpt")
            raise AssertionError("should have raised")
        except Exception:
            pass

    def test_kapa_channel_has_audit_trail(self, client):
        response = client.post("/api/v1/anonymize", json={
            "text": "Mail: test@example.com, IBAN AT61 1904 3002 3457 3201",
            "channel": "kapa",
            "document_id": "audit-test-doc",
        })
        data = response.json()
        assert data["audit_trail"] is not None
        assert len(data["audit_trail"]) >= 1

        # Verify audit entries
        for entry in data["audit_trail"]:
            assert "timestamp" in entry
            assert "entity_group" in entry
            assert "confidence" in entry
            assert "action" in entry


class TestMappingEndpoint:
    """Tests for /api/v1/mappings endpoints."""

    def test_store_and_retrieve_mapping(self, client):
        # First anonymize to store a mapping
        client.post("/api/v1/anonymize", json={
            "text": "Mail an test@example.com",
            "channel": "govgpt",
            "document_id": "mapping-test",
        })

        # Retrieve
        response = client.get("/api/v1/mappings/mapping-test")
        assert response.status_code == 200
        data = response.json()
        assert data["document_id"] == "mapping-test"
        assert isinstance(data["mapping"], dict)

    def test_mapping_not_found(self, client):
        response = client.get("/api/v1/mappings/nonexistent")
        assert response.status_code == 404

    def test_delete_mapping(self, client):
        # Store
        client.post("/api/v1/anonymize", json={
            "text": "Mail an test@example.com",
            "channel": "govgpt",
            "document_id": "delete-test",
        })

        # Delete
        response = client.delete("/api/v1/mappings/delete-test")
        assert response.status_code == 200

        # Verify deleted
        response = client.get("/api/v1/mappings/delete-test")
        assert response.status_code == 404

    def test_delete_nonexistent_mapping(self, client):
        response = client.delete("/api/v1/mappings/nonexistent")
        assert response.status_code == 404


class TestAuditEndpoint:
    """Tests for GET /api/v1/audit/{document_id}."""

    def test_audit_trail_retrieval(self, client):
        # Create KAPA result with audit
        client.post("/api/v1/anonymize", json={
            "text": "Mail: test@example.com",
            "channel": "kapa",
            "document_id": "audit-retrieve-test",
        })

        response = client.get("/api/v1/audit/audit-retrieve-test")
        assert response.status_code == 200
        data = response.json()
        assert data["document_id"] == "audit-retrieve-test"
        assert data["total"] >= 1
        assert len(data["entries"]) >= 1

    def test_audit_not_found(self, client):
        response = client.get("/api/v1/audit/nonexistent")
        assert response.status_code == 404
