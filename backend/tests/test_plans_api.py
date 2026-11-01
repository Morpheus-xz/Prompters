from datetime import timedelta
from typing import Any

import pytest
from conftest import Clock
from fastapi.testclient import TestClient

from app.config import MAX_LEAD_DAYS, MAX_PLANS_PER_USER, OWNER_COOKIE_NAME
from app.repositories.memory import InMemoryPlanRepository


def test_lifecycle_and_first_post_cookie(
    client: TestClient, brief: dict[str, Any]
) -> None:
    """Verify lifecycle and first post cookie."""
    response = client.post("/plans", json=brief)
    assert response.status_code == 201
    assert OWNER_COOKIE_NAME in response.cookies
    assert "HttpOnly" in response.headers["set-cookie"]
    data = response.json()
    assert "owner_id" not in data
    assert client.get("/plans").json()[0]["id"] == data["id"]
    assert client.get(f"/plans/{data['id']}").json() == data
    assert client.delete(f"/plans/{data['id']}").status_code == 204
    assert client.get("/plans").json() == []
    assert client.get(f"/plans/{data['id']}").status_code == 404


@pytest.mark.parametrize("offset", [0, -1, MAX_LEAD_DAYS + 1])
def test_invalid_date(
    client: TestClient, brief: dict[str, Any], clock: Clock, offset: int
) -> None:
    """Verify invalid date."""
    brief["event_date"] = (clock.day + timedelta(days=offset)).isoformat()
    assert client.post("/plans", json=brief).status_code == 422


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("guest_count", 0),
        ("guest_count", 5001),
        ("guest_count", 1.5),
        ("total_budget", 0),
        ("total_budget", -1),
        ("total_budget", 1000000001),
        ("total_budget", 1.001),
        ("event_type", "festival"),
    ],
)
def test_bounds(
    client: TestClient, brief: dict[str, Any], field: str, value: Any
) -> None:
    """Verify bounds."""
    brief[field] = value
    assert client.post("/plans", json=brief).status_code == 422


def test_plan_cap(client: TestClient, brief: dict[str, Any]) -> None:
    """Verify plan cap."""
    for _ in range(MAX_PLANS_PER_USER):
        assert client.post("/plans", json=brief).status_code == 201
    assert client.post("/plans", json=brief).status_code == 409


async def test_repository_copies_and_multiple_plans(
    client: TestClient, brief: dict[str, Any], repo: InMemoryPlanRepository
) -> None:
    """Verify repository copies and multiple plans."""
    first = client.post("/plans", json=brief).json()
    second = client.post("/plans", json=brief).json()
    owner = client.cookies[OWNER_COOKIE_NAME]
    detached = await repo.get(owner, first["id"])
    assert detached is not None
    detached.tasks[0].done = True
    detached.title = "Mutated locally"
    assert client.get(f"/plans/{first['id']}").json()["title"] == brief["title"]
    listed = await repo.list(owner)
    listed[0].vendors.clear()
    assert client.get(f"/plans/{first['id']}").json()["vendors"]
    client.delete(f"/plans/{first['id']}")
    assert client.get(f"/plans/{second['id']}").status_code == 200
