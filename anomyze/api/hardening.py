"""Optional API hardening: rate limiting, security headers, body-size cap.

Each helper degrades gracefully if its underlying optional dependency
(``slowapi``, ``secure``) is not installed — the API still starts and
serves traffic, only without the corresponding protection. Operators
opt in via the ``hardening`` extra (``pip install 'anomyze[hardening]'``).
"""

from __future__ import annotations

from typing import Any

# --- Optional imports -------------------------------------------------------

try:
    from slowapi import Limiter
    from slowapi.errors import RateLimitExceeded
    from slowapi.middleware import SlowAPIMiddleware
    from slowapi.util import get_remote_address
    _SLOWAPI = True
except ImportError:  # pragma: no cover
    Limiter = None  # type: ignore[assignment]
    RateLimitExceeded = Exception  # type: ignore[assignment,misc]
    SlowAPIMiddleware = None  # type: ignore[assignment]
    get_remote_address = None  # type: ignore[assignment]
    _SLOWAPI = False

try:
    import secure as _secure
    _SECURE = True
except ImportError:  # pragma: no cover
    _secure = None  # type: ignore[assignment]
    _SECURE = False

# --- Body-size middleware (always available, stdlib only) ------------------

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import PlainTextResponse


class BodySizeLimitMiddleware(BaseHTTPMiddleware):
    """Reject requests whose body exceeds ``max_bytes``."""

    def __init__(self, app: Any, max_bytes: int) -> None:
        super().__init__(app)
        self.max_bytes = max_bytes

    async def dispatch(self, request, call_next):  # type: ignore[override]
        cl = request.headers.get("content-length")
        if cl is not None:
            try:
                if int(cl) > self.max_bytes:
                    return PlainTextResponse(
                        f"request body exceeds {self.max_bytes} bytes",
                        status_code=413,
                    )
            except ValueError:
                pass
        return await call_next(request)


# --- Public install helper -------------------------------------------------


def install(
    app: Any,
    *,
    rate_limit_anonymize: str = "60/minute",
    rate_limit_health: str = "300/minute",
    max_body_bytes: int = 500_000,
) -> None:
    """Install rate-limit, security-header and body-size middleware.

    Safe to call regardless of which optional dependencies are
    installed — missing pieces are silently skipped.
    """
    app.add_middleware(BodySizeLimitMiddleware, max_bytes=max_body_bytes)

    if _SLOWAPI:
        limiter = Limiter(key_func=get_remote_address, default_limits=[rate_limit_anonymize])
        app.state.limiter = limiter
        app.add_middleware(SlowAPIMiddleware)
        # The decorator-based per-route limit is set in routes.py; here
        # we only register the middleware and the default fallback.

    if _SECURE:
        # secure 1.x API: with_default_headers() returns a configured
        # Secure instance; set_headers(response) copies the headers
        # onto an outgoing Starlette / FastAPI response.
        sec = _secure.Secure.with_default_headers()

        @app.middleware("http")
        async def _security_headers(request, call_next):
            response = await call_next(request)
            sec.set_headers(response)
            return response


__all__ = ["install", "BodySizeLimitMiddleware"]
