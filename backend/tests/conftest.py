import os
from collections.abc import Iterator
from datetime import date, timedelta
from typing import Any, TypeVar

os.environ["ENV"] = "test"

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel

from app.api.dependencies import (
    get_ai_client,
    get_ideas_service,
    get_plan_service,
    get_repository,
)
from app.main import create_app
from app.repositories.memory import InMemoryPlanRepository
from app.services.cache import TTLCache
from app.services.ideas_service import IdeasService
from app.services.plan_service import PlanService

T = TypeVar("T", bound=BaseModel)


class FakeAIClient:
    """Schema-validating test adapter with observable calls and injected failures."""

    def __init__(self) -> None:
        """Provide init."""
        self.calls = 0
        self.prompts: list[str] = []
        self.error: Exception | None = None
        self.payload: dict[str, Any] = {
            "ideas": [
                {
                    "title": f"Thoughtful idea {i}",
                    "description": "Use local seasonal touches.",
                    "budget_category": "venue",
                    "cost_level": "low",
                }
                for i in range(5)
            ],
            "pro_tip": "Confirm accessibility with the venue.",
        }

    async def generate_json(self, prompt: str, schema: type[T]) -> T:
        """Provide generate json."""
        self.calls += 1
        self.prompts.append(prompt)
        if self.error:
            raise self.error
        return schema.model_validate(self.payload)


class Clock:
    """Controllable date and monotonic clocks."""

    def __init__(self) -> None:
        """Provide init."""
        self.day = date(2026, 1, 1)
        self.seconds = 0.0

    def today(self) -> date:
        """Provide today."""
        return self.day

    def monotonic(self) -> float:
        """Provide monotonic."""
        return self.seconds


@pytest.fixture
def clock() -> Clock:
    """Provide clock."""
    return Clock()


@pytest.fixture
def repo() -> InMemoryPlanRepository:
    """Provide repo."""
    return InMemoryPlanRepository()


@pytest.fixture
def fake_ai() -> FakeAIClient:
    """Provide fake ai."""
    return FakeAIClient()


@pytest.fixture
def application(
    repo: InMemoryPlanRepository, clock: Clock, fake_ai: FakeAIClient
) -> FastAPI:
    """Provide application."""
    app = create_app()
    service = PlanService(repo, clock.today)
    creative = IdeasService(fake_ai, TTLCache(1800, 500, clock.monotonic))
    app.dependency_overrides[get_repository] = lambda: repo
    app.dependency_overrides[get_plan_service] = lambda: service
    app.dependency_overrides[get_ai_client] = lambda: fake_ai
    app.dependency_overrides[get_ideas_service] = lambda: creative
    return app


@pytest.fixture
def client(application: FastAPI) -> Iterator[TestClient]:
    """Provide client."""
    with TestClient(application) as test_client:
        yield test_client


@pytest.fixture
def other_client(application: FastAPI) -> Iterator[TestClient]:
    """Provide other client."""
    with TestClient(application) as test_client:
        yield test_client


@pytest.fixture
def brief(clock: Clock) -> dict[str, Any]:
    """Provide brief."""
    return {
        "title": "A joyful day",
        "event_type": "wedding",
        "event_date": (clock.day + timedelta(days=100)).isoformat(),
        "guest_count": 50,
        "total_budget": 10000.01,
        "currency": "INR",
        "city": "Pune",
        "preferences": "Vegetarian, accessible garden venue",
    }


@pytest.fixture
def plan(client: TestClient, brief: dict[str, Any]) -> dict[str, Any]:
    """Provide plan."""
    response = client.post("/plans", json=brief)
    assert response.status_code == 201
    return response.json()
