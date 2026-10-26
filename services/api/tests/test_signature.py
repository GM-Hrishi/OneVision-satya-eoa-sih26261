"""HMAC signature: valid, invalid (tampered, wrong key, malformed, missing) and expired."""

import json
import time

import pytest

from satya_api.signature import sign
from tests.conftest import KID, SECRET, Post, envelope


def test_valid_signature_is_accepted(post_event: Post) -> None:
    response = post_event(envelope())
    assert response.status_code == 202
    assert response.json()["duplicate"] is False
    assert response.json()["receipt_id"].startswith("rcp_")


def test_tampered_body_is_rejected(post_event: Post) -> None:
    env = envelope()
    signed_body = json.dumps(env).encode()
    header = sign(signed_body, SECRET, KID)
    tampered = json.dumps(env | {"sequence": 2}).encode()
    response = post_event(env, signature=header, body=tampered)
    assert response.status_code == 401
    assert response.headers["content-type"] == "application/problem+json"
    assert response.json()["code"] == "SIGNATURE_INVALID"


def test_tampered_mac_is_rejected(post_event: Post) -> None:
    env = envelope()
    header = sign(json.dumps(env).encode(), SECRET, KID)
    flipped = header[:-1] + ("0" if header[-1] != "0" else "1")
    assert post_event(env, signature=flipped).json()["code"] == "SIGNATURE_INVALID"


def test_unknown_kid_or_wrong_secret_is_rejected(post_event: Post) -> None:
    env = envelope()
    body = json.dumps(env).encode()
    assert post_event(env, signature=sign(body, SECRET, "unknown-kid")).status_code == 401
    wrong = sign(body, b"another-synthetic-secret-value-0000000000", KID)
    assert post_event(env, signature=wrong).json()["code"] == "SIGNATURE_INVALID"


@pytest.mark.parametrize("header", ["", "garbage", "t=abc,kid=test-k1,v1=00", "t=1,v1=00"])
def test_missing_or_malformed_header_is_rejected(post_event: Post, header: str) -> None:
    response = post_event(envelope(), signature=header)
    assert response.status_code == 401
    assert response.json()["code"] == "SIGNATURE_INVALID"


@pytest.mark.parametrize("offset", [-301, 301, -3600])
def test_timestamp_outside_window_is_expired(post_event: Post, offset: int) -> None:
    env = envelope()
    body = json.dumps(env).encode()
    header = sign(body, SECRET, KID, timestamp=int(time.time()) + offset)
    response = post_event(env, signature=header)
    assert response.status_code == 401
    assert response.json()["code"] == "SIGNATURE_EXPIRED"


def test_timestamp_inside_window_is_accepted(post_event: Post) -> None:
    env = envelope()
    body = json.dumps(env).encode()
    header = sign(body, SECRET, KID, timestamp=int(time.time()) - 290)
    assert post_event(env, signature=header).status_code == 202
