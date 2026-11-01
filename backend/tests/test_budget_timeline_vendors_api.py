from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.config import MAX_EXPENSES_PER_PLAN


def test_expense_add_remove(client: TestClient, plan: dict[str, Any]) -> None:
    """Verify expense add remove."""
    path = f"/plans/{plan['id']}/expenses"
    response = client.post(
        path, json={"category": "venue", "amount": 100, "description": "Deposit"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["budget"]["total_spent"] == 100
    expense_id = data["expenses"][0]["id"]
    assert client.delete(f"{path}/{expense_id}").json()["budget"]["total_spent"] == 0
    assert client.delete(f"{path}/{expense_id}").status_code == 404
    assert (
        client.post(
            path, json={"category": "invalid", "amount": 1, "description": "Test"}
        ).status_code
        == 422
    )


def test_expense_cap(client: TestClient, plan: dict[str, Any]) -> None:
    """Verify expense cap."""
    path = f"/plans/{plan['id']}/expenses"
    for _ in range(MAX_EXPENSES_PER_PLAN):
        assert (
            client.post(
                path, json={"category": "venue", "amount": 1, "description": "Test"}
            ).status_code
            == 200
        )
    assert (
        client.post(
            path, json={"category": "venue", "amount": 1, "description": "Test"}
        ).status_code
        == 409
    )


def test_task_toggle_and_vendor_booking(
    client: TestClient, plan: dict[str, Any]
) -> None:
    """Verify task toggle and vendor booking."""
    path = f"/plans/{plan['id']}"
    for done in [True, False]:
        response = client.patch(f"{path}/tasks/task-01", json={"done": done})
        assert response.json()["tasks"][0]["done"] is done
    for status in ["contacted", "booked", "to_contact"]:
        response = client.patch(f"{path}/vendors/vendor-01", json={"status": status})
        assert response.json()["vendors"][0]["status"] == status


@pytest.mark.parametrize(
    ("suffix", "body"),
    [("tasks/missing", {"done": True}), ("vendors/missing", {"status": "booked"})],
)
def test_unknown_id(
    client: TestClient, plan: dict[str, Any], suffix: str, body: dict[str, Any]
) -> None:
    """Verify unknown id."""
    assert client.patch(f"/plans/{plan['id']}/{suffix}", json=body).status_code == 404
