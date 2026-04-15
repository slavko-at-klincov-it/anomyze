"""
Prometheus metric definitions for the Anomyze API.

The optional ``observability`` extra ships
``prometheus-fastapi-instrumentator``; when it is present we expose
a ``/metrics`` endpoint on the FastAPI app and emit the custom
counters and histograms below. When the extra is not installed the
helpers degrade to no-ops so the API still starts.

PII safety
----------

Labels are restricted to category, layer, channel and stage names —
never the entity ``word`` itself. ``document_id`` is also intentionally
absent because high-cardinality labels would inflate the time-series
database without operational benefit.
"""

from __future__ import annotations

from typing import Any

try:  # optional dependency block
    from prometheus_client import Counter, Gauge, Histogram
    from prometheus_fastapi_instrumentator import Instrumentator
    _PROM_AVAILABLE = True
except ImportError:  # pragma: no cover
    _PROM_AVAILABLE = False
    Counter = Gauge = Histogram = None  # type: ignore[assignment]
    Instrumentator = None  # type: ignore[assignment]


# --- Metric handles -------------------------------------------------------


if _PROM_AVAILABLE:
    ENTITY_DETECTED_TOTAL = Counter(
        "anomyze_entity_detected_total",
        "Number of detected entities, labelled by category, layer and channel",
        ["category", "layer", "channel"],
    )
    PIPELINE_STAGE_DURATION = Histogram(
        "anomyze_pipeline_stage_duration_seconds",
        "Duration of each pipeline stage in seconds",
        ["stage"],
        # Buckets tuned for ms-to-second range typical of CPU-bound NER.
        buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0),
    )
    CONFIDENCE_SCORE = Histogram(
        "anomyze_confidence_score",
        "Distribution of confidence scores per category and layer",
        ["category", "layer"],
        buckets=(0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0),
    )
    CHANNEL_REQUESTS_TOTAL = Counter(
        "anomyze_channel_requests_total",
        "Number of /anonymize requests per channel",
        ["channel"],
    )
    MODEL_LOADED = Gauge(
        "anomyze_model_loaded",
        "1 if all detection models are loaded, 0 otherwise",
    )
else:  # pragma: no cover
    ENTITY_DETECTED_TOTAL = None
    PIPELINE_STAGE_DURATION = None
    CONFIDENCE_SCORE = None
    CHANNEL_REQUESTS_TOTAL = None
    MODEL_LOADED = None


# --- Helper API -----------------------------------------------------------


def record_entity(category: str, layer: str, channel: str, score: float) -> None:
    """Increment per-entity counters and confidence histogram."""
    if not _PROM_AVAILABLE:
        return
    ENTITY_DETECTED_TOTAL.labels(category=category, layer=layer, channel=channel).inc()
    CONFIDENCE_SCORE.labels(category=category, layer=layer).observe(score)


def record_stage_duration(stage: str, seconds: float) -> None:
    """Observe one execution of a pipeline stage."""
    if not _PROM_AVAILABLE:
        return
    PIPELINE_STAGE_DURATION.labels(stage=stage).observe(seconds)


def record_channel_request(channel: str) -> None:
    if not _PROM_AVAILABLE:
        return
    CHANNEL_REQUESTS_TOTAL.labels(channel=channel).inc()


def set_model_loaded(loaded: bool) -> None:
    if not _PROM_AVAILABLE:
        return
    MODEL_LOADED.set(1.0 if loaded else 0.0)


def install(app: Any) -> None:
    """Install the Prometheus instrumentator on a FastAPI app.

    No-op if the optional dependency is missing.
    """
    if not _PROM_AVAILABLE:
        return
    Instrumentator(
        excluded_handlers=["/api/v1/health", "/metrics"],
    ).instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)
