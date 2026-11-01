"""Verify Vercel packaging and the Render proxy contract without network calls."""

import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

from app.config import CSP


def _node(script: str, *arguments: str) -> subprocess.CompletedProcess[str]:
    """Run a deployment module in Node without a shell or external requests."""
    module = Path(__file__).resolve().parents[2] / "frontend/build.mjs"
    code = f"import {{build, deploymentConfig}} from {json.dumps(module.as_uri())};"
    return subprocess.run(
        ["node", "--input-type=module", "-e", code + script, *arguments],
        capture_output=True,
        text=True,
        check=False,
    )


@pytest.fixture
def deployment() -> dict[str, Any]:
    """Generate routes for a reserved test origin, never a live service."""
    result = _node(
        "console.log(JSON.stringify(deploymentConfig(process.argv[1])));",
        "https://festiva.test/",
    )
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


@pytest.mark.parametrize(
    "origin",
    [
        "",
        "invalid",
        "http://festiva.test",
        "https://user:password@festiva.test",
        "https://festiva.test/path",
        "https://festiva.test?query=1",
        "https://festiva.test#fragment",
    ],
)
def test_backend_origin_validation(origin: str) -> None:
    """Reject absent or unsafe targets instead of silently misrouting API traffic."""
    result = _node("deploymentConfig(process.argv[1]);", origin)
    assert result.returncode != 0


def test_proxy_paths_and_cache_policy(deployment: dict[str, Any]) -> None:
    """Every UI API path uses Render; static files never use the API proxy."""
    proxy = deployment["routes"][1]
    script = "const r=deploymentConfig(process.argv[1]).routes[1];" + (
        "const matches=process.argv.slice(2).map(p=>new RegExp(r.src).test(p));"
        "console.log(JSON.stringify(matches));"
    )
    paths = [
        "/plans",
        "/plans/id",
        "/plans/id/expenses",
        "/plans/id/tasks/task-01",
        "/plans/id/vendors/vendor-01",
        "/plans/id/ideas",
        "/event-types",
        "/health",
        "/",
        "/static/js/main.js",
        "/plans-other",
        "/health-other",
    ]
    result = _node(script, "https://festiva.test", *paths)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == [True] * 8 + [False] * 4
    assert proxy["dest"] == "https://festiva.test/$1"
    assert proxy["headers"]["Cache-Control"] == "no-store"
    assert "methods" not in proxy


def test_frontend_security_policy(deployment: dict[str, Any]) -> None:
    """Keep the Vercel HTML policy aligned with the existing backend CSP."""
    headers = deployment["routes"][0]["headers"]
    assert headers["Content-Security-Policy"] == CSP
    assert headers["X-Frame-Options"] == "DENY"
    assert headers["X-Content-Type-Options"] == "nosniff"
    assert deployment["routes"][0]["continue"] is True


def test_build_copies_only_public_assets(tmp_path: Path) -> None:
    """Package the existing UI URLs without exposing source configs or env files."""
    result = _node(
        "await build(process.argv[1], process.argv[2]);",
        "https://festiva.test",
        str(tmp_path),
    )
    assert result.returncode == 0, result.stderr
    source = Path(__file__).resolve().parents[2] / "frontend"
    assert (tmp_path / "static/index.html").read_bytes() == (
        source / "index.html"
    ).read_bytes()
    for directory in ("css", "js"):
        for file in (source / directory).rglob("*"):
            if file.is_file():
                target = tmp_path / "static/static" / file.relative_to(source)
                assert target.read_bytes() == file.read_bytes()
    config = json.loads((tmp_path / "config.json").read_text())
    assert config["version"] == 3
    assert not (tmp_path / "static/.env").exists()
    assert not (tmp_path / "static/build.mjs").exists()
    assert not (tmp_path / "static/vercel.json").exists()


def test_render_starts_without_frontend_files(tmp_path: Path) -> None:
    """Honor Render's environment in a backend-only filesystem, without patching."""
    shutil.copytree(
        "app", tmp_path / "app", ignore=shutil.ignore_patterns("__pycache__")
    )
    script = (
        "from fastapi.testclient import TestClient; from app.main import app; "
        "client=TestClient(app); "
        "assert client.get('/health').status_code == 200; "
        "assert client.get('/').status_code == 404"
    )
    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=tmp_path,
        env={"SERVE_FRONTEND": "false", "ENV": "test"},
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
