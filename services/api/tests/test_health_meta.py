"""Health (liveness + readiness) and meta."""

from fastapi.testclient import TestClient

from satya_api.config import Settings
from satya_api.main import create_app
from satya_api.store import MemoryStore


def test_health_ok_when_all_dependencies_ok(client: TestClient) -> None:
    response = client.get("/v1/health")
    assert response.status_code == 200
    assert response.json()["checks"] == {"postgres": "ok", "valkey": "ok", "keycloak": "ok"}


def test_health_503_when_a_dependency_fails(settings: Settings) -> None:
    async def ok() -> None:
        return None

    async def down() -> None:
        raise ConnectionError("synthetic outage")

    app = create_app(settings, store=MemoryStore(), checks={"postgres": ok, "keycloak": down})
    with TestClient(app) as c:
        response = c.get("/v1/health")
    assert response.status_code == 503
    assert response.json()["status"] == "degraded"
    assert response.json()["checks"]["keycloak"] == "fail"
    assert "synthetic outage" not in response.text


def test_liveness(client: TestClient) -> None:
    assert client.get("/v1/health/live").json() == {"status": "ok"}


def test_meta(client: TestClient) -> None:
    body = client.get("/v1/meta").json()
    assert body["schema_version"] == "satya.event/1"
    assert body["supported_ays"] == ["2024-25", "2025-26", "2026-27"]
    assert body["adapters"] == []
    assert body["advisory"] is True and body["regulatory_effect"] == "none"


def test_cors_allows_only_configured_origins(client: TestClient) -> None:
    ok = client.options(
        "/v1/meta",
        headers={"Origin": "https://localhost", "Access-Control-Request-Method": "GET"},
    )
    assert ok.headers.get("access-control-allow-origin") == "https://localhost"
    bad = client.options(
        "/v1/meta",
        headers={"Origin": "https://evil.example.invalid", "Access-Control-Request-Method": "GET"},
    )
    assert "access-control-allow-origin" not in bad.headers
