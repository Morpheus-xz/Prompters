from fastapi.testclient import TestClient

from app.api.dependencies import (
    get_ai_client,
    get_ideas_service,
    get_plan_service,
    get_repository,
)
from app.config import EVENT_SPECS, VERSION
from app.main import create_app


def test_health_and_metadata(client: TestClient) -> None:
    """Verify health and metadata."""
    health = client.get("/health").json()
    assert health["status"] == "ok" and health["version"] == VERSION
    assert health["storage_backend"] == "in-memory"
    types = client.get("/event-types").json()
    assert len(types) == len(EVENT_SPECS)
    for item in types:
        assert sum(line["percent"] for line in item["budget_split"]) == 100
    assert client.get("/openapi.json").status_code == 200


def test_default_dependencies() -> None:
    """Verify default dependencies."""
    assert get_repository() is get_repository()
    assert get_ai_client() is get_ai_client()
    assert (
        get_ideas_service(get_ai_client()).cache
        is get_ideas_service(get_ai_client()).cache
    )


def test_service_dependency_and_detached_storage() -> None:
    """Verify service dependency and detached storage."""
    assert get_plan_service(get_repository()).repo is get_repository()


def test_api_only_mode() -> None:
    """Render starts without mounting frontend files or changing API routes."""
    with TestClient(create_app(serve_frontend=False)) as api_client:
        assert api_client.get("/health").status_code == 200
        assert api_client.get("/event-types").status_code == 200
        assert api_client.get("/plans").status_code == 200
        assert api_client.get("/").status_code == 404
        assert api_client.get("/static/js/main.js").status_code == 404
