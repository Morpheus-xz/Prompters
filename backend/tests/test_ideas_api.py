import json
from typing import Any

import httpx
import pytest
from conftest import FakeAIClient
from fastapi import FastAPI
from fastapi.testclient import TestClient
from google import genai
from google.genai import errors, types
from pydantic import BaseModel

from app.api.dependencies import get_ideas_service
from app.config import MAX_RETRIES
from app.exceptions import AIServiceError
from app.models.enums import IdeaFocus
from app.services.ai_client import GeminiClient, _network_generate


def test_success_cache_and_refresh(
    client: TestClient, plan: dict[str, Any], fake_ai: FakeAIClient
) -> None:
    """Verify success cache and refresh."""
    path = f"/plans/{plan['id']}/ideas"
    first = client.post(path, json={}).json()
    assert len(first["ideas"]) == 5 and not first["from_cache"]
    assert client.post(path, json={}).json()["from_cache"]
    assert fake_ai.calls == 1
    assert not client.post(path, json={"refresh": True}).json()["from_cache"]
    assert fake_ai.calls == 2
    prompt = fake_ai.prompts[0]
    facts = json.loads(prompt.split("UNTRUSTED JSON DATA:\n")[1])
    assert facts["allocations"] == plan["allocations"]
    assert facts["per_guest_budget"] == plan["per_guest_budget"]
    assert "never instructions" in prompt


def test_category_filter(
    client: TestClient, plan: dict[str, Any], fake_ai: FakeAIClient
) -> None:
    """Verify category filter."""
    fake_ai.payload["ideas"][0]["budget_category"] = "fiction"
    response = client.post(f"/plans/{plan['id']}/ideas", json={})
    assert response.status_code == 200
    assert len(response.json()["ideas"]) == 4


def test_insufficient_categories(
    client: TestClient, plan: dict[str, Any], fake_ai: FakeAIClient
) -> None:
    """Verify insufficient categories."""
    for idea in fake_ai.payload["ideas"][:3]:
        idea["budget_category"] = "fiction"
    assert client.post(f"/plans/{plan['id']}/ideas", json={}).status_code == 502


def test_generic_ai_failure(
    client: TestClient, plan: dict[str, Any], fake_ai: FakeAIClient
) -> None:
    """Verify generic ai failure."""
    fake_ai.error = AIServiceError()
    response = client.post(f"/plans/{plan['id']}/ideas", json={})
    assert response.status_code == 502
    assert response.json() == {"detail": AIServiceError().detail}
    assert "GEMINI" not in response.text


def test_delete_purges_cache(
    client: TestClient, application: FastAPI, plan: dict[str, Any]
) -> None:
    """Verify delete purges cache."""
    client.post(f"/plans/{plan['id']}/ideas", json={})
    service = application.dependency_overrides[get_ideas_service]()
    assert service.cache.get((plan["id"], IdeaFocus.overall)) is not None
    client.delete(f"/plans/{plan['id']}")
    assert service.cache.get((plan["id"], IdeaFocus.overall)) is None


class TinySchema(BaseModel):
    """Minimal output contract for transport and validation tests."""

    value: str


@pytest.mark.parametrize("output", [None, "", "invalid", '{"value": 1}'])
async def test_adapter_generic_failures(output: str | None) -> None:
    """Verify adapter generic failures."""
    client = GeminiClient(lambda prompt: output)
    with pytest.raises(AIServiceError) as failure:
        await client.generate_json("test", TinySchema)
    assert "value" not in failure.value.detail


async def test_adapter_fences() -> None:
    """Verify adapter fences."""
    client = GeminiClient(lambda prompt: '```json\n{"value":"safe"}\n```')
    assert (await client.generate_json("test", TinySchema)).value == "safe"


async def test_adapter_internal_message_hidden() -> None:
    """Verify adapter internal message hidden."""

    def fail(prompt: str) -> str:
        """Provide fail."""
        raise RuntimeError("PRIVATE UPSTREAM TOKEN")

    with pytest.raises(AIServiceError) as failure:
        await GeminiClient(fail).generate_json("test", TinySchema)
    assert "PRIVATE" not in failure.value.detail


def test_network_adapter_with_injected_transport() -> None:
    """Verify network adapter with injected transport."""
    requests: list[dict[str, Any]] = []

    def respond(request: httpx.Request) -> httpx.Response:
        """Provide respond."""
        requests.append(json.loads(request.content))
        return httpx.Response(
            200,
            json={
                "candidates": [
                    {
                        "content": {
                            "parts": [{"text": '{"value":"safe"}'}],
                            "role": "model",
                        }
                    }
                ]
            },
        )

    with genai.Client(
        api_key="test-only",
        http_options=types.HttpOptions(
            client_args={"transport": httpx.MockTransport(respond)}
        ),
    ) as sdk:
        assert _network_generate("data", sdk) == '{"value":"safe"}'
    assert requests[0]["generationConfig"]["responseMimeType"] == "application/json"


async def test_missing_key_is_lazy() -> None:
    """Verify missing key is lazy."""
    with pytest.raises(AIServiceError):
        await GeminiClient().generate_json("test", TinySchema)


def test_network_retries_are_bounded() -> None:
    """Verify network retries are bounded."""
    attempts: list[str] = []

    def respond(request: httpx.Request) -> httpx.Response:
        """Provide respond."""
        attempts.append(request.url.path)
        return httpx.Response(503, json={"error": {"code": 503, "message": "PRIVATE"}})

    options = types.HttpOptions(
        client_args={"transport": httpx.MockTransport(respond)},
        retry_options=types.HttpRetryOptions(attempts=1),
    )
    with (
        genai.Client(api_key="test-only", http_options=options) as sdk,
        pytest.raises(errors.APIError),
    ):
        _network_generate("data", sdk)
    assert len(attempts) == MAX_RETRIES
