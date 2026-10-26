"""Workbench API (S1.8): GET /v1/cases and GET /v1/cases/{id}/affidavit-diff.

Tokens are signed with a throwaway RSA key standing in for Keycloak; cases are the committed
synthetic demo cases. Synthetic data only.
"""

import json
import time
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient
from jwt.algorithms import RSAAlgorithm

from satya_api.auth import TokenVerifier
from satya_api.cases import FixtureCaseRepository
from satya_api.config import Settings
from satya_api.main import create_app
from satya_api.store import MemoryStore
from satya_shared_types import validator

ISSUER = "https://auth.localhost/realms/satya"
KID = "test-signing-key"
CASES = Path(__file__).resolve().parents[3] / "data" / "synthetic" / "cases"
DIT03 = "cas_01JD3M5A00000000000000DT03"
DCE05 = "cas_01JD3M5A00000000000000CE05"
TOKEN_KEY = b"synthetic-tokenisation-key-for-tests-0001"

_KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)
_OTHER = rsa.generate_private_key(public_exponent=65537, key_size=2048)


def _jwks() -> dict[str, Any]:
    jwk = json.loads(RSAAlgorithm.to_jwk(_KEY.public_key()))
    jwk.update({"kid": KID, "use": "sig", "alg": "RS256"})
    return {"keys": [jwk]}


def token(
    roles: list[str] | None = None,
    groups: list[str] | None = None,
    *,
    key: Any = _KEY,
    azp: str = "satya-web",
    typ: str = "Bearer",
    exp_in: int = 300,
) -> str:
    now = int(time.time())
    claims = {
        "iss": ISSUER,
        "sub": "user-rb-southern-demo",
        "azp": azp,
        "typ": typ,
        "iat": now,
        "exp": now + exp_in,
        "preferred_username": "rb.southern.demo",
        "roles": ["RB"] if roles is None else roles,
        "groups": ["/regions/southern"] if groups is None else groups,
    }
    return jwt.encode(claims, key, algorithm="RS256", headers={"kid": KID})


def auth(raw: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {raw}"}


async def _ok() -> None:
    return None


def _client(user_rate_limit: str = "1000/minute") -> Iterator[TestClient]:
    async def fetch() -> dict[str, Any]:
        return _jwks()

    settings = Settings(env="test", rate_limit="1000/minute", user_rate_limit=user_rate_limit)
    app = create_app(
        settings,
        store=MemoryStore(),
        checks={"postgres": _ok, "valkey": _ok, "keycloak": _ok},
        cases=FixtureCaseRepository(CASES, TOKEN_KEY),
        verifier=TokenVerifier(ISSUER, "satya-web", fetch),
    )
    with TestClient(app) as client:
        yield client


@pytest.fixture(scope="module")
def wb() -> Iterator[TestClient]:
    yield from _client()


def test_no_token_is_401_auth_required(wb: TestClient) -> None:
    response = wb.get(f"/v1/cases/{DIT03}/affidavit-diff")
    assert response.status_code == 401
    assert response.headers["content-type"].startswith("application/problem+json")
    assert response.json()["code"] == "AUTH_REQUIRED"


@pytest.mark.parametrize(
    "raw",
    [
        "not-a-jwt",
        token(key=_OTHER),
        token(exp_in=-120),
        token(azp="satya-mock-portal"),
        token(typ="ID"),
    ],
    ids=["malformed", "wrong-key", "expired", "other-client", "id-token"],
)
def test_bad_tokens_are_401_invalid_token(wb: TestClient, raw: str) -> None:
    response = wb.get("/v1/cases", headers=auth(raw))
    assert response.status_code == 401
    assert response.json()["code"] == "INVALID_TOKEN"


def test_wrong_role_is_403(wb: TestClient) -> None:
    response = wb.get(f"/v1/cases/{DIT03}/affidavit-diff", headers=auth(token(roles=["INS"])))
    assert response.status_code == 403
    assert response.json()["code"] == "SCOPE_DENIED"


def test_case_list_is_scoped_to_the_officials_region(wb: TestClient) -> None:
    body = wb.get("/v1/cases", headers=auth(token())).json()
    assert {i["case_id"] for i in body["items"]} == {DIT03, DCE05}
    flags = {i["case_id"]: i["open_flags"] for i in body["items"]}
    assert flags == {DIT03: 5, DCE05: 0}
    other = wb.get("/v1/cases", headers=auth(token(groups=["/regions/northern"]))).json()
    assert other["items"] == []
    national = wb.get("/v1/cases", headers=auth(token(groups=["/regions/national"]))).json()
    assert len(national["items"]) == 2


def test_affidavit_diff_matches_the_contract_and_the_planted_findings(wb: TestClient) -> None:
    response = wb.get(f"/v1/cases/{DIT03}/affidavit-diff", headers=auth(token()))
    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    diff = response.json()
    assert [e.message for e in validator("AffidavitDiff").iter_errors(diff)] == []
    truth = json.loads((CASES / "dit03-2026-27" / "truth.json").read_text("utf-8"))
    assert sorted(f["check_ref"] for f in diff["flags"]) == sorted(
        f["check_ref"] for f in truth["expected_flags"]
    )
    assert diff["advisory"] is True
    assert "DEMO-DEED-0301" not in response.text


def test_out_of_region_case_is_403(wb: TestClient) -> None:
    response = wb.get(
        f"/v1/cases/{DIT03}/affidavit-diff", headers=auth(token(groups=["/regions/northern"]))
    )
    assert response.status_code == 403
    assert response.json()["code"] == "SCOPE_DENIED"


@pytest.mark.parametrize("case_id", ["cas_01JD3M5A00000000000000ZZ99", "not-a-case", "cas_.."])
def test_unknown_or_malformed_case_is_404(wb: TestClient, case_id: str) -> None:
    response = wb.get(f"/v1/cases/{case_id}/affidavit-diff", headers=auth(token()))
    assert response.status_code == 404
    assert response.json()["code"] == "NOT_FOUND"


def test_per_user_quota() -> None:
    for client in _client(user_rate_limit="2/minute"):
        headers = auth(token())
        codes = [client.get("/v1/cases", headers=headers).status_code for _ in range(3)]
        assert codes == [200, 200, 429]


def test_meta_lists_the_m5_ruleset(wb: TestClient) -> None:
    body = wb.get("/v1/meta").json()
    assert body["ruleset_versions"] == ["m5-affidavit@0.1.0"]
    assert body["template_profiles"] == ["aff2-portal-2024-27"]
