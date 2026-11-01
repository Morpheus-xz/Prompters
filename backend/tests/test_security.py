from typing import Any
from uuid import UUID

import pytest
from conftest import FakeAIClient
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.requests import Request
from starlette.types import Message, Receive, Scope, Send

from app.api.limiter import client_address, limiter
from app.api.middleware import RequestPolicyMiddleware
from app.config import MAX_BODY_BYTES, OWNER_COOKIE_NAME
from app.exceptions import AIServiceError


@pytest.mark.parametrize(
    ("method", "path", "status"),
    [("GET", "/health", 200), ("GET", "/missing", 404), ("POST", "/plans", 422)],
)
def test_headers(client: TestClient, method: str, path: str, status: int) -> None:
    """Verify headers."""
    response = client.request(method, path, json={} if method == "POST" else None)
    assert response.status_code == status
    for key in [
        "x-content-type-options",
        "x-frame-options",
        "x-xss-protection",
        "referrer-policy",
        "strict-transport-security",
        "permissions-policy",
        "cross-origin-opener-policy",
        "content-security-policy",
    ]:
        assert key in response.headers
    assert "access-control-allow-origin" not in response.headers
    assert response.headers["cache-control"] == "no-store"


def test_ai_error_headers(
    client: TestClient, plan: dict[str, Any], fake_ai: FakeAIClient
) -> None:
    """Verify ai error headers."""
    fake_ai.error = AIServiceError()
    response = client.post(f"/plans/{plan['id']}/ideas", json={})
    assert response.status_code == 502
    assert response.headers["x-frame-options"] == "DENY"


def test_csp_and_caching(client: TestClient) -> None:
    """Verify csp and caching."""
    root = client.get("/")
    assert "cdn.jsdelivr.net" not in root.headers["content-security-policy"]
    assert root.headers["cache-control"] == "no-cache"
    assert "cdn.jsdelivr.net" in client.get("/docs").headers["content-security-policy"]
    assert (
        client.get("/static/js/main.js").headers["cache-control"]
        == "public, max-age=3600"
    )


def test_body_cap(client: TestClient) -> None:
    """Verify body cap."""
    response = client.post("/plans", content="x" * (MAX_BODY_BYTES + 1))
    assert response.status_code == 413
    assert response.headers["x-content-type-options"] == "nosniff"


def test_owner_isolation(other_client: TestClient, plan: dict[str, Any]) -> None:
    """Verify owner isolation."""
    assert other_client.get("/plans").json() == []
    for method, suffix in [("GET", ""), ("DELETE", ""), ("POST", "/ideas")]:
        assert (
            other_client.request(
                method, f"/plans/{plan['id']}{suffix}", json={} if suffix else None
            ).status_code
            == 404
        )


def test_cookie_replacement_and_secure(
    client: TestClient, brief: dict[str, Any]
) -> None:
    """Verify cookie replacement and secure."""
    client.cookies.set(OWNER_COOKIE_NAME, "broken")
    response = client.post("/plans", json=brief, headers={"x-forwarded-proto": "https"})
    assert response.status_code == 201
    assert UUID(response.cookies[OWNER_COOKIE_NAME])
    assert "Secure" in response.headers["set-cookie"]


def test_rate_limit(client: TestClient, brief: dict[str, Any]) -> None:
    """Verify rate limit."""
    original = limiter.enabled
    limiter.enabled = True
    limiter.reset()
    try:
        statuses = [
            client.post(
                "/plans", json=brief, headers={"x-forwarded-for": "192.0.2.17"}
            ).status_code
            for _ in range(61)
        ]
        assert statuses[-1] == 429
    finally:
        limiter.enabled = original
        limiter.reset()


def test_proxy_key() -> None:
    """Verify proxy key."""
    assert (
        client_address(
            Request({"type": "http", "headers": [(b"x-forwarded-for", b"one, two")]})
        )
        == "one"
    )
    assert client_address(Request({"type": "http", "headers": []})) == "unknown"


async def test_chunked_body_limit() -> None:
    """Verify chunked body limit."""
    sent: list[Message] = []
    chunks: list[Message] = [
        {"type": "http.request", "body": b"x", "more_body": True},
        {"type": "http.request", "body": b"x" * MAX_BODY_BYTES},
    ]

    async def receive() -> Message:
        """Provide receive."""
        return chunks.pop(0)

    async def downstream(scope: Scope, receive: Receive, send: Send) -> None:
        """Provide downstream."""
        pytest.fail("Oversized body reached the application")

    async def send(message: Message) -> None:
        """Provide send."""
        sent.append(message)

    scope: Scope = {"type": "http", "headers": [], "path": "/plans", "method": "POST"}
    await RequestPolicyMiddleware(downstream)(scope, receive, send)
    assert sent[0]["status"] == 413


def test_native_accessibility_contract(client: TestClient) -> None:
    """Verify native accessibility contract."""
    html = client.get("/").text
    assert '<html lang="en">' in html
    assert html.index('class="skip"') < html.index("<header")
    for marker in [
        "<main",
        "<header",
        "<nav",
        "<footer",
        "<dialog",
        'role="status"',
        'aria-live="polite"',
    ]:
        assert marker in html


def test_unexpected_errors_remain_private(application: FastAPI) -> None:
    """Verify unexpected errors remain private."""

    async def fail() -> None:
        """Provide fail."""
        raise RuntimeError("PRIVATE INTERNAL ERROR")

    application.add_api_route("/test-error", fail)
    with TestClient(application, raise_server_exceptions=False) as test_client:
        response = test_client.get("/test-error")
    assert response.status_code == 500
    assert response.json() == {"detail": "Internal server error."}
    assert response.headers["x-frame-options"] == "DENY"
