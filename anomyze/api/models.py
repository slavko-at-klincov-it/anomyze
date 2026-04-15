"""
Pydantic request/response schemas for the Anomyze REST API.
"""

from typing import Literal

from pydantic import BaseModel, Field


class SettingsOverride(BaseModel):
    """Optional per-request settings overrides."""

    pii_threshold: float | None = Field(None, ge=0.0, le=1.0)
    org_threshold: float | None = Field(None, ge=0.0, le=1.0)
    anomaly_threshold: float | None = Field(None, ge=0.0, le=1.0)
    perplexity_threshold: float | None = Field(None, ge=0.0, le=1.0)
    use_anomaly_detection: bool | None = None
    kapa_review_threshold: float | None = Field(None, ge=0.0, le=1.0)


class AnonymizeRequest(BaseModel):
    """Request body for the /anonymize endpoint."""

    text: str = Field(
        ...,
        min_length=1,
        max_length=50_000,
        description="Text to anonymize (max 50,000 characters)",
    )
    channel: Literal["govgpt", "ifg", "kapa"] = Field(
        "govgpt", description="Output channel"
    )
    document_id: str | None = Field(
        None, description="Document ID (auto-generated if omitted)"
    )
    settings_override: SettingsOverride | None = Field(
        None, description="Per-request settings overrides"
    )


class DetectedEntityResponse(BaseModel):
    """A single detected PII entity in the API response."""

    word: str
    entity_group: str
    score: float
    start: int
    end: int
    source: str
    placeholder: str = ""


class RedactionProtocolEntry(BaseModel):
    """A single entry in the IFG redaction protocol."""

    category: str
    count: int
    min_confidence: float
    max_confidence: float


class AuditEntryResponse(BaseModel):
    """A single audit trail entry in the KAPA response."""

    timestamp: str
    document_id: str
    entity_group: str
    confidence: float
    source_layer: str
    action: str
    placeholder: str
    context_snippet: str


class AnonymizeResponse(BaseModel):
    """Response body for the /anonymize endpoint."""

    document_id: str
    channel: str
    text: str
    entities: list[DetectedEntityResponse]
    entity_count: int
    # GovGPT / KAPA fields
    mapping: dict[str, str] | None = None
    # IFG fields
    redaction_protocol: list[RedactionProtocolEntry] | None = None
    # KAPA fields
    flagged_for_review: list[str] | None = None
    audit_trail: list[AuditEntryResponse] | None = None


class MappingResponse(BaseModel):
    """Response body for the /mappings/{document_id} endpoint."""

    document_id: str
    mapping: dict[str, str]


class AuditResponse(BaseModel):
    """Response body for the /audit/{document_id} endpoint."""

    document_id: str
    entries: list[AuditEntryResponse]
    total: int


class HealthResponse(BaseModel):
    """Response body for the /health endpoint."""

    status: str
    models_loaded: bool
    device: str
    version: str
