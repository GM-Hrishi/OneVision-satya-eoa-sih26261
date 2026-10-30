"""Workbench API: GET /v1/cases, GET /v1/cases/{id}/affidavit-diff (S1.8, M6 sections S2.8),
GET /v1/cases/{id}/verification and GET /v1/cases/{id}/documents/{doc_id}/verification (S2.8).

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
    assert {i["case_id"] for i in body["items"]} >= {DIT03, DCE05}
    assert len(body["items"]) == 8  # five Slice D cases + three B-28 scan cases
    flags = {i["case_id"]: i["open_flags"] for i in body["items"]}
    assert flags[DIT03] == 7  # M5 (5) + M6 (2: image-only mark, mark after notary)
    assert flags[DCE05] == 0
    other = wb.get("/v1/cases", headers=auth(token(groups=["/regions/northern"]))).json()
    assert other["items"] == []
    national = wb.get("/v1/cases", headers=auth(token(groups=["/regions/national"]))).json()
    assert len(national["items"]) == 8


def test_affidavit_diff_matches_the_contract_and_the_planted_findings(wb: TestClient) -> None:
    response = wb.get(f"/v1/cases/{DIT03}/affidavit-diff", headers=auth(token()))
    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    diff = response.json()
    assert [e.message for e in validator("AffidavitDiff").iter_errors(diff)] == []
    truth = json.loads((CASES / "dit03-2026-27" / "truth.json").read_text("utf-8"))
    truth_m6 = json.loads((CASES / "dit03-2026-27" / "truth-m6.json").read_text("utf-8"))
    affidavit = diff["doc_id"]
    expected = [f["check_ref"] for f in truth["expected_flags"]] + [
        f["check_ref"] for f in truth_m6["expected_flags"] if f["doc_id"] == affidavit
    ]
    assert sorted(f["check_ref"] for f in diff["flags"]) == sorted(expected)
    # M6 sections are filled and no longer pending (UI §6.3)
    assert {p["section"] for p in diff["pending"]} <= {"ocr"}
    assert diff["sworn"]["issuer_sig"]["state"] == "image_only"
    assert diff["sworn"]["uploader_sig"]["trust_anchor_label"] == "TEST TRUST ANCHOR"
    assert diff["stamp"]["second_party"] == "AICTE NEW DELHI" and diff["stamp"]["duty"] == 10000
    assert diff["chronology"]["mark_after_notary"] is True
    assert truth_m6["printed"]["stamp.certificate_no"] not in response.text  # masked
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
        # A cheap authorised route (unknown case id), so the three calls fall in one window.
        codes = [
            client.get("/v1/cases/not-a-case/review", headers=headers).status_code for _ in range(3)
        ]
        assert codes == [404, 404, 429]


def test_meta_lists_the_rulesets(wb: TestClient) -> None:
    body = wb.get("/v1/meta").json()
    assert body["ruleset_versions"] == ["m5-affidavit@0.1.0", "m6-signatures@0.1.0"]
    assert body["template_profiles"] == ["aff2-portal-2024-27"]


# ---- S2.8: verification endpoints -------------------------------------------------------------
def _case_files(directory: str) -> tuple[dict[str, Any], dict[str, Any]]:
    case = json.loads((CASES / directory / "case.json").read_text("utf-8"))
    truth = json.loads((CASES / directory / "truth-m6.json").read_text("utf-8"))
    return case, truth


@pytest.mark.parametrize("path", ["verification", "documents/{doc}/verification"])
def test_verification_endpoints_apply_auth_role_and_region(wb: TestClient, path: str) -> None:
    case, _ = _case_files("dit03-2026-27")
    url = f"/v1/cases/{DIT03}/" + path.format(doc=case["documents"][0]["doc_id"])
    assert wb.get(url).json()["code"] == "AUTH_REQUIRED"
    assert wb.get(url, headers=auth(token(roles=["INS"]))).status_code == 403
    response = wb.get(url, headers=auth(token(groups=["/regions/northern"])))
    assert response.status_code == 403 and response.json()["code"] == "SCOPE_DENIED"
    assert wb.get(url, headers=auth(token())).status_code == 200


def test_case_verification_matches_ui_6_4_and_the_demo_story(wb: TestClient) -> None:
    response = wb.get(f"/v1/cases/{DIT03}/verification", headers=auth(token()))
    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    body = response.json()
    assert [e.message for e in validator("CaseVerification").iter_errors(body)] == []
    assert body["advisory"] is True and body["trust_anchor_label"] == "TEST TRUST ANCHOR"
    case, truth = _case_files("dit03-2026-27")
    rows = {d["doc_id"]: d for d in body["documents"]}
    assert {k: v["label"] for k, v in rows.items()} == truth["expected_document_labels"]
    affidavit = rows[case["documents"][0]["doc_id"]]
    assert affidavit["issuer_sig"]["state"] == "image_only"  # F5
    assert affidavit["uploader_sig"]["state"] == "present"  # F6, never makes it verified
    assert affidavit["label"] == "manual_review_required"
    accounts = rows[case["documents"][1]["doc_id"]]
    assert accounts["label"] == "source_unavailable"  # F10
    assert accounts["source"] == {"channel": "icai-udin", "adapter_mode": "none"}
    assert "route_manual" in accounts["actions"]
    assert body["label_counts"]["manual_review_required"] == 1
    assert body["label_counts"]["source_unavailable"] == 1


def test_clean_case_verification(wb: TestClient) -> None:
    body = wb.get(f"/v1/cases/{DCE05}/verification", headers=auth(token())).json()
    labels = sorted(d["label"] for d in body["documents"])
    # The ICAI answer for the audited statement is a stored simulated source answer (SRC_MATCH).
    assert labels == ["verified", "verified"]
    assert all(d["flag_count"] == 0 for d in body["documents"])


def test_document_verification_matches_portal_2_7(wb: TestClient) -> None:
    case, truth = _case_files("dit03-2026-27")
    doc_id = case["documents"][0]["doc_id"]
    response = wb.get(f"/v1/cases/{DIT03}/documents/{doc_id}/verification", headers=auth(token()))
    body = response.json()
    assert [e.message for e in validator("VerificationResult").iter_errors(body)] == []
    assert body["doc_id"] == doc_id and body["decided_by"] == "system"
    kinds = [c["kind"] for c in body["checks"]]
    assert kinds.count("issuer_signature") == 1 and kinds.count("uploader_signature") == 1
    expected = {(c["kind"], c["reason_code"]) for c in truth["expected_checks"]}
    assert expected <= {(c["kind"], c["reason_code"]) for c in body["checks"]}


@pytest.mark.parametrize(
    "doc_id", ["doc_00000000000000000000000000", "not-a-doc", "doc_QRQ9XKV1GHAT0J10S45FKAMK5R"]
)
def test_unknown_document_is_404(wb: TestClient, doc_id: str) -> None:
    response = wb.get(f"/v1/cases/{DIT03}/documents/{doc_id}/verification", headers=auth(token()))
    assert response.status_code == 404 and response.json()["code"] == "NOT_FOUND"


def test_document_of_another_case_is_404(wb: TestClient) -> None:
    other, _ = _case_files("dce05-2026-27")
    doc_id = other["documents"][0]["doc_id"]
    response = wb.get(f"/v1/cases/{DIT03}/documents/{doc_id}/verification", headers=auth(token()))
    assert response.status_code == 404


def test_verification_counts_against_the_user_quota() -> None:
    for client in _client(user_rate_limit="2/minute"):
        headers = auth(token())
        url = f"/v1/cases/{DCE05}/verification"
        codes = [client.get(url, headers=headers).status_code for _ in range(3)]
        assert codes == [200, 200, 429]
