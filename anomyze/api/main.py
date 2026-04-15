"""
FastAPI application factory for Anomyze.

Creates and configures the FastAPI application with:
- Model preloading on startup
- Mapping store and audit logger initialization
- API route registration
"""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI

from anomyze.api import hardening, metrics
from anomyze.api.logging_config import configure_logging, get_logger
from anomyze.api.routes import router
from anomyze.audit.logger import AuditLogger
from anomyze.config.settings import Settings, get_settings
from anomyze.mappings.mapping_store import MappingStore
from anomyze.pipeline.orchestrator import PipelineOrchestrator


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: load models on startup."""
    settings = app.state.settings
    log = get_logger("anomyze.api")

    log.info("anomyze.startup", message="loading models")
    orchestrator = PipelineOrchestrator(settings)
    orchestrator.load_models(verbose=True)
    app.state.orchestrator = orchestrator
    metrics.set_model_loaded(orchestrator.model_manager.is_loaded())

    # Initialize mapping store
    persist_path = None
    if settings.mapping_persist_path:
        persist_path = Path(settings.mapping_persist_path)
    app.state.mapping_store = MappingStore(persist_path=persist_path)

    # Initialize audit logger
    audit_path = None
    if settings.audit_log_path:
        audit_path = Path(settings.audit_log_path)
    app.state.audit_logger = AuditLogger(log_path=audit_path)

    log.info("anomyze.startup.complete", message="ready")
    yield
    log.info("anomyze.shutdown")


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create and configure the FastAPI application.

    Args:
        settings: Application settings. Uses global settings if None.

    Returns:
        Configured FastAPI application instance.
    """
    if settings is None:
        settings = get_settings()

    configure_logging()

    app = FastAPI(
        title="Anomyze API",
        description=(
            "Souveräne KI-Anonymisierungsschicht für die österreichische "
            "Bundesverwaltung. Filtert KI-generierten Output — erkennt und "
            "anonymisiert personenbezogene Daten (PII), bevor sie das "
            "System verlassen."
        ),
        version="2.0.0",
        lifespan=lifespan,
    )

    app.state.settings = settings
    app.include_router(router, prefix="/api/v1")
    metrics.install(app)
    hardening.install(app, max_body_bytes=settings.max_request_body_bytes)

    return app


# Default application instance for uvicorn
app = create_app()
