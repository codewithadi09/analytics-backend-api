"""
Security headers middleware.

Adds standard defensive headers to every response. None of these
are exotic -- they're baseline hardening that costs nothing and
closes off well-known attack classes (clickjacking, MIME sniffing,
referrer leakage).
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)

        # Prevents browsers from MIME-sniffing a response away from
        # the declared Content-Type -- blocks some XSS vectors.
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Prevents this API's responses from being framed in an
        # iframe -- relevant mainly for any HTML error pages, but
        # cheap defense-in-depth regardless.
        response.headers["X-Frame-Options"] = "DENY"

        # Limits how much referrer information leaks when a link
        # from this API (e.g. a redirect) is followed elsewhere.
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Opts out of legacy browser features (camera, mic, geo,
        # etc.) that a pure JSON API has no reason to ever request.
        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=(), payment=()"
        )

        return response