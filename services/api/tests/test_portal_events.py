"""Dedupe, ledger chain, body limits, validation errors and problem+json shape."""

import json
from dataclasses import replace

import pytest
from fastapi.testclient import TestClient

from satya_api.ledger import verify_chain
from satya_api.signature import sign
from satya_api.store import MemoryStore
from tests.conftest import KID, SECRET, Post, envelope


def test_duplicate_event_returns_200_with_same_receipt(post_event: Post) -> None:
    env = envelope()
    first = post_event(env)
    second = post_event(env)
    assert first.status_code == 202
    assert second.status_code == 200
    assert second.json() == {"duplicate": True, "receipt_id": first.json()["receipt_id"]}


def test_duplicate_is_not_appended_to_ledger(post_event: Post, store: MemoryStore) -> None:
    env = envelope()
    post_event(env)
    post_event(env)
    assert len(store.rows) == 1


@pytest.mark.anyio
async def test_ledger_chain_verifies_and_detects_tampering(
    post_event: Post, store: MemoryStore
) -> None:
    for seq in range(1, 6):
        assert post_event(envelope(sequence=seq)).status_code == 202
    rows = await store.ledger_rows()
    report = verify_chain(rows)
    assert report.ok and report.rows == 5
    assert rows[0].prev_hash == "0" * 64
    tampered = list(rows)
    tampered[2] = replace(rows[2], payload_sha256="f" * 64)
    broken = verify_chain(tampered)
    assert not broken.ok and broken.broken_at == 3
    reordered = [rows[0], rows[2], rows[1], *rows[3:]]
    assert verify_chain(reordered).broken_at == rows[2].seq


def test_oversize_body_is_rejected_with_413(post_event: Post) -> None:
    env = envelope(data={"padding": "x" * 5000})
    response = post_event(env)
    assert response.status_code == 413
    assert response.json()["code"] == "PAYLOAD_TOO_LARGE"


def test_oversize_streamed_body_without_length_is_rejected(client: TestClient) -> None:
    def chunks():  # type: ignore[no-untyped-def]
        for _ in range(10):
            yield b"x" * 1000

    response = client.post(
        "/v1/portal-events", content=chunks(), headers={"Content-Type": "application/json"}
    )
    assert response.status_code == 413


@pytest.mark.parametrize(
    ("override", "status", "code"),
    [
        ({"spec": "satya.event/2"}, 400, "SCHEMA_VERSION_UNSUPPORTED"),
        ({"type": "application.approved"}, 400, "UNSUPPORTED_EVENT_TYPE"),
        ({"type": "case.validation_completed"}, 400, "UNSUPPORTED_EVENT_TYPE"),
        ({"sequence": 0}, 400, "VALIDATION_FAILED"),
        ({"event_id": "evt_not-a-ulid"}, 400, "VALIDATION_FAILED"),
        (
            {"subject": {"application_id": "1-90000004217", "ay": "2019-20"}},
            400,
            "UNSUPPORTED_AY",
        ),
    ],
)
def test_invalid_envelopes_are_rejected(
    post_event: Post, override: dict[str, object], status: int, code: str
) -> None:
    response = post_event(envelope(**override))
    assert response.status_code == status
    body = response.json()
    assert body["code"] == code
    assert body["type"] == "urn:satya:problem:" + code.lower()
    assert body["trace_id"]
    assert "Traceback" not in response.text


def test_validation_errors_list_paths(post_event: Post) -> None:
    body = post_event(envelope(sequence=0)).json()
    assert {"path": "/sequence", "code": "minimum"} in body["errors"]


def test_non_json_body_is_rejected(post_event: Post) -> None:
    raw = b"not json"
    response = post_event({}, body=raw, signature=sign(raw, SECRET, KID))
    assert response.json()["code"] == "VALIDATION_FAILED"


def test_x_field_in_snapshot_is_rejected(post_event: Post) -> None:
    snapshot = {
        "ay": "2026-27",
        "basic": {
            "application_id": "1-90000004217",
            "regional_office": "Southern",
            "overall_deficiency": "unknown",
        },
        "bank": {"bank_name": "Demo Bank", "account_number": "DEMO-ACCOUNT"},
    }
    response = post_event(envelope(data={"snapshot": snapshot}))
    assert response.status_code == 403
    assert response.json()["code"] == "PERSONAL_DATA_REJECTED"
    assert response.json()["errors"] == [{"path": "bank.account_number", "code": "x_field"}]


def test_non_json_content_type_is_rejected(client: TestClient) -> None:
    response = client.post(
        "/v1/portal-events", content=b"{}", headers={"Content-Type": "text/plain"}
    )
    assert response.status_code == 415


def test_unknown_route_is_problem_json(client: TestClient) -> None:
    response = client.get("/v1/nope")
    assert response.status_code == 404
    assert response.json()["code"] == "NOT_FOUND"


def test_rate_limit_per_ip(settings, store) -> None:  # type: ignore[no-untyped-def]
    from satya_api.main import create_app

    async def ok() -> None:
        return None

    limited = settings.model_copy(update={"rate_limit": "3/minute"})
    app = create_app(limited, store=store, checks={"postgres": ok})
    with TestClient(app) as c:
        codes = [c.get("/v1/meta").status_code for _ in range(5)]
    assert codes[:3] == [200, 200, 200]
    assert codes[3] == 429


def test_signature_header_never_logged(post_event: Post, caplog: pytest.LogCaptureFixture) -> None:
    env = envelope()
    header = sign(json.dumps(env).encode(), SECRET, KID)
    post_event(env, signature=header)
    assert header.split("v1=")[1] not in caplog.text
