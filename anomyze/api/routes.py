"""
FastAPI route definitions for the Anomyze REST API.

Endpoints:
- POST /api/v1/anonymize — Main anonymization endpoint
- GET  /api/v1/health — System health and model status
- GET  /api/v1/mappings/{document_id} — Retrieve stored mapping
- DELETE /api/v1/mappings/{document_id} — Delete stored mapping only
- GET  /api/v1/audit/{document_id} — Retrieve audit trail
- DELETE /api/v1/documents/{document_id} — DSGVO Art. 17 (mapping + audit)
"""

import uuid

from fastapi import APIRouter, HTTPException, Request

from anomyze.api import metrics
from anomyze.api.models import (
    AnonymizeRequest,
    AnonymizeResponse,
    AuditEntryResponse,
    AuditResponse,
    DetectedEntityResponse,
    HealthResponse,
    MappingResponse,
    RedactionProtocolEntry,
)
from anomyze.channels.base import ChannelResult
from anomyze.channels.govgpt import GovGPTResult
from anomyze.channels.ifg import IFGResult
from anomyze.channels.kapa import KAPAResult
from anomyze.config.settings import Settings

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health(request: Request) -> HealthResponse:
    """Check system health and model loading status."""
    from anomyze import __version__

    orchestrator = request.app.state.orchestrator
    return HealthResponse(
        status="healthy",
        models_loaded=orchestrator.model_manager.is_loaded(),
        device=orchestrator.model_manager.device_name,
        version=__version__,
    )


@router.post("/anonymize", response_model=AnonymizeResponse)
async def anonymize(request: Request, body: AnonymizeRequest) -> AnonymizeResponse:
    """Filter KI-generated output through the specified channel.

    The AI tools work internally with full data. Anomyze filters the
    output before it leaves the system. Three channels:
    - **govgpt**: Reversible placeholders — output filtered before forwarding
    - **ifg**: Irreversible redaction — output filtered before publication on data.gv.at
    - **kapa**: Reversible placeholders + audit trail — output filtered for parliamentary use
    """
    orchestrator = request.app.state.orchestrator
    document_id = body.document_id or str(uuid.uuid4())
    metrics.record_channel_request(body.channel)

    # Apply per-request settings overrides
    settings = Settings(
        pii_threshold=orchestrator.settings.pii_threshold,
        org_threshold=orchestrator.settings.org_threshold,
        anomaly_threshold=orchestrator.settings.anomaly_threshold,
        perplexity_threshold=orchestrator.settings.perplexity_threshold,
        use_anomaly_detection=orchestrator.settings.use_anomaly_detection,
        kapa_review_threshold=orchestrator.settings.kapa_review_threshold,
        fix_encoding=orchestrator.settings.fix_encoding,
        use_regex_fallback=orchestrator.settings.use_regex_fallback,
        device=orchestrator.settings.device,
        pii_model=orchestrator.settings.pii_model,
        org_model=orchestrator.settings.org_model,
        mlm_model=orchestrator.settings.mlm_model,
    )

    if body.settings_override:
        override = body.settings_override
        if override.pii_threshold is not None:
            settings.pii_threshold = override.pii_threshold
        if override.org_threshold is not None:
            settings.org_threshold = override.org_threshold
        if override.anomaly_threshold is not None:
            settings.anomaly_threshold = override.anomaly_threshold
        if override.perplexity_threshold is not None:
            settings.perplexity_threshold = override.perplexity_threshold
        if override.use_anomaly_detection is not None:
            settings.use_anomaly_detection = override.use_anomaly_detection
        if override.kapa_review_threshold is not None:
            settings.kapa_review_threshold = override.kapa_review_threshold

    # Run pipeline
    original_text = body.text
    from anomyze.pipeline.context_layer import ContextLayer
    from anomyze.pipeline.ner_layer import NERLayer
    from anomyze.pipeline.normalizer import normalize_adversarial
    from anomyze.pipeline.orchestrator import fix_encoding as _fix_encoding
    from anomyze.pipeline.regex_layer import RegexLayer

    text = body.text
    if settings.fix_encoding:
        text = _fix_encoding(text)
    if settings.use_adversarial_normalization:
        text = normalize_adversarial(text)

    # Stage 1: Regex
    raw_entities: list = []
    if settings.use_regex_fallback:
        regex_layer = RegexLayer()
        raw_entities.extend(regex_layer.process(text))

    # Stage 2: NER
    ner_layer = NERLayer()
    pii_pl = orchestrator.model_manager.load_pii_pipeline(verbose=False)
    org_pl = orchestrator.model_manager.load_org_pipeline(verbose=False)
    raw_entities.extend(ner_layer.process(text, pii_pl, org_pl, settings))

    # Stage 2c: Presidio-compatible local recognizers (AT-specific)
    if settings.use_presidio_compat:
        from anomyze.pipeline.presidio_compat_layer import PresidioCompatLayer
        raw_entities.extend(PresidioCompatLayer().process(text, settings))

    # Ensemble: merge overlapping entities
    from anomyze.pipeline.ensemble import merge_entities
    entities = merge_entities(raw_entities, text)

    # Stage 3: Context
    if settings.use_anomaly_detection:
        mlm_pl = orchestrator.model_manager.load_mlm_pipeline(verbose=False)
        context_layer = ContextLayer()
        context_entities = context_layer.process(text, entities, mlm_pl, settings)
        entities.extend(context_entities)

    entities.sort(key=lambda e: e.start)

    # Format via channel
    from anomyze.channels.govgpt import GovGPTChannel
    from anomyze.channels.ifg import IFGChannel
    from anomyze.channels.kapa import KAPAChannel

    result: ChannelResult
    if body.channel == "kapa":
        kapa_channel = KAPAChannel()
        result = kapa_channel.format_output(
            text, entities, settings, original_text, document_id
        )
    elif body.channel == "ifg":
        result = IFGChannel().format_output(text, entities, settings, original_text)
    else:
        result = GovGPTChannel().format_output(text, entities, settings, original_text)

    # Store mapping if applicable
    mapping_store = request.app.state.mapping_store
    if isinstance(result, (GovGPTResult, KAPAResult)) and result.mapping:
        mapping_store.store(document_id, result.mapping)

    # Store audit entries if applicable
    if isinstance(result, KAPAResult) and result.audit_entries:
        audit_logger = request.app.state.audit_logger
        audit_logger.log_batch(result.audit_entries)

    # Emit per-entity Prometheus counters (no PII labels).
    for ent in result.entities:
        metrics.record_entity(
            category=ent.entity_group,
            layer=ent.source,
            channel=body.channel,
            score=ent.score,
        )

    # Build response
    entity_responses = [
        DetectedEntityResponse(
            word=e.word,
            entity_group=e.entity_group,
            score=round(e.score, 3),
            start=e.start,
            end=e.end,
            source=e.source,
            placeholder=e.placeholder,
        )
        for e in result.entities
    ]

    response = AnonymizeResponse(
        document_id=document_id,
        channel=body.channel,
        text=result.text,
        entities=entity_responses,
        entity_count=result.entity_count,
    )

    if isinstance(result, GovGPTResult):
        response.mapping = result.mapping
    elif isinstance(result, IFGResult):
        response.redaction_protocol = [
            RedactionProtocolEntry(
                category=entry.category,
                count=entry.count,
                min_confidence=round(entry.min_confidence, 3),
                max_confidence=round(entry.max_confidence, 3),
            )
            for entry in result.redaction_protocol
        ]
    elif isinstance(result, KAPAResult):
        response.mapping = result.mapping
        response.flagged_for_review = result.flagged_for_review
        response.audit_trail = [
            AuditEntryResponse(
                timestamp=entry.timestamp,
                document_id=entry.document_id,
                entity_group=entry.entity_group,
                confidence=round(entry.confidence, 3),
                source_layer=entry.source_layer,
                action=entry.action,
                placeholder=entry.placeholder,
                context_snippet=entry.context_snippet,
            )
            for entry in result.audit_entries
        ]

    return response


@router.get("/mappings/{document_id}", response_model=MappingResponse)
async def get_mapping(request: Request, document_id: str) -> MappingResponse:
    """Retrieve the placeholder mapping for a document.

    Only available for GovGPT and KAPA channel results.
    """
    mapping_store = request.app.state.mapping_store
    mapping = mapping_store.retrieve(document_id)
    if mapping is None:
        raise HTTPException(status_code=404, detail=f"No mapping found for document {document_id}")
    return MappingResponse(document_id=document_id, mapping=mapping)


@router.delete("/mappings/{document_id}")
async def delete_mapping(request: Request, document_id: str) -> dict:
    """Delete the mapping for a document."""
    mapping_store = request.app.state.mapping_store
    deleted = mapping_store.delete(document_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"No mapping found for document {document_id}")
    return {"status": "deleted", "document_id": document_id}


@router.delete("/documents/{document_id}")
async def delete_document(request: Request, document_id: str) -> dict:
    """DSGVO Art. 17 "Recht auf Vergessenwerden".

    Removes the document's placeholder mapping AND all audit entries
    in a single transactional call. Use this instead of the narrower
    ``DELETE /mappings/{id}`` when acting on a Betroffenen-Antrag.
    """
    mapping_store = request.app.state.mapping_store
    audit_logger = request.app.state.audit_logger
    mapping_deleted = mapping_store.delete(document_id)
    audit_removed = audit_logger.forget(document_id)
    if not mapping_deleted and audit_removed == 0:
        raise HTTPException(
            status_code=404, detail=f"Document {document_id} is unknown"
        )
    return {
        "status": "deleted",
        "document_id": document_id,
        "mapping_deleted": mapping_deleted,
        "audit_entries_removed": audit_removed,
    }


@router.get("/audit/{document_id}", response_model=AuditResponse)
async def get_audit(request: Request, document_id: str) -> AuditResponse:
    """Retrieve the audit trail for a document.

    Only available for KAPA channel results.
    """
    audit_logger = request.app.state.audit_logger
    entries = audit_logger.get_entries(document_id)
    if not entries:
        raise HTTPException(
            status_code=404, detail=f"No audit entries found for document {document_id}"
        )
    return AuditResponse(
        document_id=document_id,
        entries=[
            AuditEntryResponse(
                timestamp=e.timestamp,
                document_id=e.document_id,
                entity_group=e.entity_group,
                confidence=round(e.confidence, 3),
                source_layer=e.source_layer,
                action=e.action,
                placeholder=e.placeholder,
                context_snippet=e.context_snippet,
            )
            for e in entries
        ],
        total=len(entries),
    )
