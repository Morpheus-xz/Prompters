"""ASGI request bounds, security, caching and privacy-conscious logging."""

import logging
from time import perf_counter

from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.config import (
    CSP,
    DOCS_CSP,
    HSTS_MAX_AGE,
    MAX_BODY_BYTES,
    MILLISECONDS_PER_SECOND,
    STATIC_MAX_AGE,
)

logger = logging.getLogger(__name__)


def response_headers(path: str) -> dict[str, str]:
    """Apply security headers consistently, including application errors."""
    cache = "no-store"
    if path.startswith("/static/"):
        cache = f"public, max-age={STATIC_MAX_AGE}"
    elif path == "/":
        cache = "no-cache"
    return {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Strict-Transport-Security": f"max-age={HSTS_MAX_AGE}; includeSubDomains",
        "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
        "Cross-Origin-Opener-Policy": "same-origin",
        "Content-Security-Policy": DOCS_CSP
        if path in {"/docs", "/redoc", "/openapi.json"}
        else CSP,
        "Cache-Control": cache,
    }


def secured_sender(scope: Scope, send: Send, started: float) -> Send:
    """Decorate response start once, including rejected request bodies."""

    async def secured(message: Message) -> None:
        """Attach headers and log metadata without user content."""
        if message["type"] == "http.response.start":
            headers = response_headers(scope["path"])
            message["headers"] = list(message.get("headers", [])) + [
                (k.lower().encode(), v.encode()) for k, v in headers.items()
            ]
            elapsed = (perf_counter() - started) * MILLISECONDS_PER_SECOND
            logger.info(
                "%s %s %s %.2fms",
                scope["method"],
                scope["path"],
                message["status"],
                elapsed,
            )
        await send(message)

    return secured


class RequestPolicyMiddleware:
    """Bound actual body bytes, including requests without Content-Length."""

    def __init__(self, app: ASGIApp) -> None:
        """Wrap the application with a request policy."""
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """Buffer only bounded bytes and instrument all response starts."""
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        scope["festiva_started"] = perf_counter()
        secured = secured_sender(scope, send, scope["festiva_started"])
        message = await self._body(scope, receive)
        if message is None:
            await secured(
                {
                    "type": "http.response.start",
                    "status": 413,
                    "headers": [(b"content-type", b"application/json")],
                }
            )
            await secured(
                {
                    "type": "http.response.body",
                    "body": b'{"detail":"Request too large."}',
                }
            )
            return
        pending = [message]

        async def replay() -> Message:
            """Replay the combined body once, then read disconnect events."""
            return pending.pop() if pending else await receive()

        await self.app(scope, replay, secured)

    async def _body(self, scope: Scope, receive: Receive) -> Message | None:
        """Reject oversized declared or chunked requests without chunk overhead."""
        declared = dict(scope["headers"]).get(b"content-length", b"0")
        if declared.isdigit() and int(declared) > MAX_BODY_BYTES:
            return None
        body = bytearray()
        while True:
            message = await receive()
            chunk = message.get("body", b"")
            if len(body) + len(chunk) > MAX_BODY_BYTES:
                return None
            body.extend(chunk)
            if not message.get("more_body", False):
                return {**message, "body": bytes(body)}
