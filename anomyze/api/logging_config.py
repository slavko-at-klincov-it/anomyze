"""
Structured logging configuration for the Anomyze API.

Uses :mod:`structlog` when available and falls back to the standard
library otherwise so that the basic API still works without the
``observability`` extra installed.

PII safety
----------

The structured emitter never logs the input ``text`` or any
``entity.word`` value. Records carry only:

* ``document_id`` (UUID)
* ``channel``
* ``entity_count`` per category
* ``duration_ms`` per pipeline stage
* ``layer`` source

Audit-trail data (with sanitised PII context) lives in the separate
``audit/logger.py`` and is intentionally not piped through this
emitter.
"""

from __future__ import annotations

import logging
import sys
from typing import Any

try:  # optional dependency
    import structlog
    _STRUCTLOG_AVAILABLE = True
except ImportError:  # pragma: no cover
    structlog = None  # type: ignore[assignment]
    _STRUCTLOG_AVAILABLE = False


def configure_logging(level: str = "INFO") -> None:
    """Initialise structured logging.

    Falls back to ``logging.basicConfig`` when structlog is not
    installed. Safe to call multiple times.
    """
    log_level = getattr(logging, level.upper(), logging.INFO)

    if not _STRUCTLOG_AVAILABLE:
        logging.basicConfig(
            level=log_level,
            format="%(asctime)s %(levelname)s %(name)s %(message)s",
            stream=sys.stdout,
        )
        return

    logging.basicConfig(
        format="%(message)s",
        level=log_level,
        stream=sys.stdout,
    )

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str = "anomyze") -> Any:
    """Return a structured logger when available, else stdlib logger."""
    if _STRUCTLOG_AVAILABLE:
        return structlog.get_logger(name)
    return logging.getLogger(name)
