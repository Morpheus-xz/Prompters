"""Lazy Gemini adapter with network-only retries and validated JSON output."""

import asyncio
import logging
import re
from collections.abc import Callable
from functools import lru_cache
from typing import Protocol, TypeVar

from google import genai
from google.genai import errors, types
from pydantic import BaseModel
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.config import (
    AI_MAX_OUTPUT_TOKENS,
    AI_THINKING_BUDGET,
    AI_TIMEOUT_MS,
    GEMINI_MODEL,
    MAX_RETRIES,
    RETRY_MAX_SECONDS,
    RETRY_MIN_SECONDS,
    SDK_NETWORK_ATTEMPTS,
)
from app.exceptions import AIServiceError
from app.settings import get_settings

T = TypeVar("T", bound=BaseModel)
logger = logging.getLogger(__name__)


class AIClient(Protocol):
    """Typed creative-generation boundary for dependency injection."""

    async def generate_json(self, prompt: str, schema: type[T]) -> T:
        """Generate and validate one schema instance."""
        ...


@lru_cache
def _sdk_client() -> genai.Client:
    """Construct the SDK only when ideas are requested."""
    key = get_settings().gemini_api_key
    if not key:
        raise ValueError("GEMINI_API_KEY is missing")
    return genai.Client(
        api_key=key,
        http_options=types.HttpOptions(
            timeout=AI_TIMEOUT_MS,
            retry_options=types.HttpRetryOptions(attempts=SDK_NETWORK_ATTEMPTS),
        ),
    )


@retry(
    retry=retry_if_exception_type(errors.APIError),
    stop=stop_after_attempt(MAX_RETRIES),
    wait=wait_exponential(min=RETRY_MIN_SECONDS, max=RETRY_MAX_SECONDS),
    reraise=True,
)
def _network_generate(prompt: str, client: genai.Client | None = None) -> str | None:
    """Retry only the SDK network call, never parsing or validation."""
    sdk = client if client is not None else _sdk_client()
    response = sdk.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            max_output_tokens=AI_MAX_OUTPUT_TOKENS,
            thinking_config=types.ThinkingConfig(thinking_budget=AI_THINKING_BUDGET),
        ),
    )
    return response.text


class GeminiClient:
    """Offload the synchronous SDK and contain all upstream failures."""

    def __init__(
        self, network: Callable[[str], str | None] = _network_generate
    ) -> None:
        """Accept a synchronous transport, offloaded on every request."""
        self.network = network

    async def generate_json(self, prompt: str, schema: type[T]) -> T:
        """Return a validated model or a single safe application error."""
        try:
            text = await asyncio.to_thread(self.network, prompt)
            if not text:
                raise ValueError("Gemini returned empty text")
            text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip())
            return schema.model_validate_json(text)
        except Exception as exc:
            logger.exception("Creative generation failed: %s", type(exc).__name__)
            raise AIServiceError() from exc
