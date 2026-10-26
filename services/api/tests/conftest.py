"""Shared fixtures. Unit tests need no stack: memory store, no Valkey, fake health checks."""

import json
from collections.abc import Callable, Iterator
from typing import Any

import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr
from ulid import ULID

from satya_api.config import Settings
from satya_api.main import create_app
from satya_api.signature import sign
from satya_api.store import MemoryStore

KID = "test-k1"
SECRET = b"synthetic-test-secret-not-used-anywhere-else-0001"


def envelope(**overrides: Any) -> dict[str, Any]:
    env: dict[str, Any] = {
        "spec": "satya.event/1",
        "event_id": f"evt_{ULID()}",
        "type": "application.precheck_requested",
        "occurred_at": "2026-12-14T11:05:42+05:30",
        "producer": "mock-portal",
        "subject": {
            "application_id": "1-90000004217",
            "permanent_id": "1-9000317",
            "ay": "2026-27",
        },
        "sequence": 1,
        "correlation_id": f"cor_{ULID()}",
        "data": {},
    }
    env.update(overrides)
    return env


@pytest.fixture
def settings() -> Settings:
    return Settings(
        env="test",
        hmac_keys=SecretStr(f"{KID}={SECRET.decode()}"),
        max_body_bytes=4096,
        rate_limit="1000/minute",
        client_rate_limit="1000/minute",
    )


@pytest.fixture
def store() -> MemoryStore:
    return MemoryStore()


async def _ok() -> None:
    return None


@pytest.fixture
def client(settings: Settings, store: MemoryStore) -> Iterator[TestClient]:
    checks = {"postgres": _ok, "valkey": _ok, "keycloak": _ok}
    app = create_app(settings, store=store, checks=checks)
    with TestClient(app) as test_client:
        yield test_client


Post = Callable[..., Any]


@pytest.fixture
def post_event(client: TestClient) -> Post:
    def _post(
        env: dict[str, Any], *, signature: str | None = None, body: bytes | None = None
    ) -> Any:
        raw = body if body is not None else json.dumps(env).encode()
        headers = {"Content-Type": "application/json"}
        headers["X-SATYA-Signature"] = (
            signature if signature is not None else sign(raw, SECRET, KID)
        )
        return client.post("/v1/portal-events", content=raw, headers=headers)

    return _post
