"""
Pydantic request/response schemas for the Anomyze REST API.
"""

from typing import Dict, List, Optional, Literal
from pydantic import BaseModel, Field


class SettingsOverride(BaseModel):
    """Optional per-request settings overrides."""

    pii_threshold: Optional[float] = Field(None, ge=0.0, le=1.0)
    org_threshold: Optional[float] = Field(None, ge=0.0, le=1.0)
    anomaly_threshold: Optional[float] = Field(None, ge=0.0, le=1.0)
    perplexity_threshold: Optional[float] = Field(None, ge=0.0, le=1.0)
    use_anomaly_detection: Optional[bool] = None
    kapa_review_threshold: Optional[float] = Field(None, ge=0.0, le=1.0)


class AnonymizeRequest(BaseModel):
    """Request body for the /anonymize endpoint."""

    text: str = Field(..., min_length=1, description="Text to anonymize")
    channel: Literal["govgpt", "ifg", "kapa"] = Field(
        "govgpt", description="Output channel"
    )
    document_id: Optional[str] = Field(
        None, description="Document ID (auto-generated if omitted)"
    )
    settings_override: Optional[SettingsOverride] = Field(
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
    entities: List[DetectedEntityResponse]
    entity_count: int
    # GovGPT / KAPA fields
    mapping: Optional[Dict[str, str]] = None
    # IFG fields
    redaction_protocol: Optional[List[RedactionProtocolEntry]] = None
    # KAPA fields
    flagged_for_review: Optional[List[str]] = None
    audit_trail: Optional[List[AuditEntryResponse]] = None


class MappingResponse(BaseModel):
    """Response body for the /mappings/{document_id} endpoint."""

    document_id: str
    mapping: Dict[str, str]


class AuditResponse(BaseModel):
    """Response body for the /audit/{document_id} endpoint."""

    document_id: str
    entries: List[AuditEntryResponse]
    total: int


class HealthResponse(BaseModel):
    """Response body for the /health endpoint."""

    status: str
    models_loaded: bool
    device: str
    version: str
