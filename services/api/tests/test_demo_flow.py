"""Slice D demo flow: queue bands, review view, upload rules, dispositions, audit chain, alerts.

Synthetic data only. Tokens come from a throwaway RSA key standing in for Keycloak.
"""

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from satya_api.auth import TokenVerifier
from satya_api.cases import FixtureCaseRepository
from satya_api.config import Settings
from satya_api.main import create_app
from satya_api.store import MemoryStore
from satya_api.triage import risk_band, why_sentence

from .test_workbench_api import (
    CASES,
    DCE05,
    DIT03,
    ISSUER,
    TOKEN_KEY,
    _jwks,
    _ok,
    auth,
    token,
)

DCE07 = "cas_01JD3M5A00000000000000CE07"
DT11 = "cas_01JD3M5A00000000000000DT11"
DCE09 = "cas_01JD3M5A00000000000000CE09"


@pytest.fixture
def flow(tmp_path: Path) -> Iterator[TestClient]:
    async def fetch() -> dict:  # type: ignore[type-arg]
        return _jwks()

    settings = Settings(
        env="test",
        rate_limit="1000/minute",
        user_rate_limit="1000/minute",
        upload_dir=str(tmp_path),
        upload_rate_limit="1000/minute",
    )
    app = create_app(
        settings,
        store=MemoryStore(),
        checks={"postgres": _ok, "valkey": _ok, "keycloak": _ok},
        cases=FixtureCaseRepository(CASES, TOKEN_KEY),
        verifier=TokenVerifier(ISSUER, "satya-web", fetch),
    )
    with TestClient(app) as client:
        yield client


def rb() -> dict[str, str]:
    return auth(token())


def test_queue_has_five_cases_with_a_deterministic_band(flow: TestClient) -> None:
    body = flow.get("/v1/cases", headers=rb()).json()
    bands = {i["case_id"]: i["risk_band"] for i in body["items"]}
    assert bands == {DIT03: "high", DT11: "high", DCE07: "medium", DCE09: "medium", DCE05: "low"}
    assert body["totals"]["by_band"] == {"high": 2, "medium": 2, "low": 1}
    assert all(set(i["label_counts"]) >= {"verified", "source_unavailable"} for i in body["items"])
    assert flow.get("/v1/cases", headers=rb()).json() == body  # same data every time


def test_band_rule_is_severity_driven() -> None:
    assert risk_band([{"severity": "critical"}], ["verified"]) == "high"
    assert risk_band([], ["mismatch_detected"]) == "high"
    assert risk_band([{"severity": "warning"}], ["verified"]) == "medium"
    assert risk_band([], ["expired"]) == "medium"
    assert risk_band([{"severity": "info"}], ["verified", "source_unavailable"]) == "low"


def test_review_lists_labels_flags_and_template_why(flow: TestClient) -> None:
    view = flow.get(f"/v1/cases/{DIT03}/review", headers=rb()).json()
    assert {d["label"] for d in view["documents"]} <= {
        "verified",
        "mismatch_detected",
        "expired",
        "verification_pending",
        "source_unavailable",
        "manual_review_required",
    }
    assert len(view["flags"]) == 7
    land = next(f for f in view["flags"] if f["rule_id"] == "LAND-AREA-RECON")
    assert "acre" in land["why"] and land["page"] and land["regions"] and land["aph_clause"]
    assert why_sentence({"rule_id": "UNKNOWN"})
    # no UDIN on the audited statement: source unavailable plus a manual task
    accounts = next(d for d in view["documents"] if "accounts" in d["slot"])
    assert accounts["label"] == "source_unavailable" and accounts["manual_task"]
    assert view["tasks"]


def test_mock_sources_are_tagged_and_clean_case_is_verified(flow: TestClient) -> None:
    view = flow.get(f"/v1/cases/{DCE05}/review", headers=rb()).json()
    assert {d["label"] for d in view["documents"]} == {"verified"}
    names = [c["source"]["name"] for d in view["documents"] for c in d["checks"] if "source" in c]
    assert names and all("MOCK SOURCE" in n for n in names)


def test_stamp_reuse_is_manual_review_not_mismatch(flow: TestClient) -> None:
    view = flow.get(f"/v1/cases/{DT11}/review", headers=rb()).json()
    affidavit = next(d for d in view["documents"] if "affidavit" in d["slot"])
    assert affidavit["label"] == "manual_review_required"


def test_disposition_needs_reason_and_goes_to_the_ledger(flow: TestClient) -> None:
    flag = flow.get(f"/v1/cases/{DT11}/review", headers=rb()).json()["flags"][0]["flag_id"]
    url = f"/v1/cases/{DT11}/flags/{flag}/disposition"
    short = flow.post(url, json={"action": "accept", "reason": "short"}, headers=rb())
    assert short.status_code == 422 and short.json()["code"] == "DISPOSITION_REASON_REJECTED"
    approve = flow.post(
        url, json={"action": "approve", "reason": "long enough reason"}, headers=rb()
    )
    assert approve.status_code == 422  # there is no approve
    ok = flow.post(
        url, json={"action": "escalate_manual", "reason": "check with the register"}, headers=rb()
    )
    assert ok.status_code == 201
    assert ok.json()["advisory"] is True and ok.json()["regulatory_effect"] == "none"
    view = flow.get(f"/v1/cases/{DT11}/review", headers=rb()).json()
    assert view["flags"][0]["disposition"]["action"] == "escalate_manual"
    assert view["status"] == "reviewed"
    audit = flow.get(f"/v1/audit?case_id={DT11}", headers=rb()).json()
    assert audit["chain"]["ok"] is True
    assert audit["entries"][0]["event_type"] == "disposition.recorded"
    detail = flow.get(f"/v1/audit/{audit['entries'][0]['seq']}", headers=rb()).json()
    assert detail["detail"]["action"] == "escalate_manual"


def test_upload_rules_and_rerun(flow: TestClient) -> None:
    url = f"/v1/cases/{DCE05}/documents?slot=accounts&filename="
    pdf_headers = {**rb(), "Content-Type": "application/pdf"}
    bad_ext = flow.post(url + "x.exe", content=b"%PDF-1.7\n%%EOF", headers=pdf_headers)
    assert bad_ext.json()["code"] == "UPLOAD_NAME_REJECTED"
    bad_body = flow.post(url + "x.pdf", content=b"MZ not a pdf", headers=pdf_headers)
    assert bad_body.json()["code"] == "UPLOAD_CONTENT_REJECTED"
    junk = flow.post(url + "x.pdf", content=b"%PDF-1.7\njunk\n%%EOF", headers=pdf_headers)
    assert junk.status_code == 422 and junk.json()["code"] == "UPLOAD_UNREADABLE"
    wrong_type = flow.post(
        url + "x.pdf", content=b"x", headers={**rb(), "Content-Type": "text/plain"}
    )
    assert wrong_type.status_code == 415
    big = flow.post(url + "x.pdf", content=b"%PDF-" + b"0" * (6 * 1024 * 1024), headers=pdf_headers)
    assert big.status_code == 413
    # a real synthetic PDF with a problem replaces the clean one: the case now has findings
    data = (CASES / "dce07-2026-27" / "audited-accounts.pdf").read_bytes()
    ok = flow.post(url + "audited-accounts.pdf", content=data, headers=pdf_headers)
    assert ok.status_code == 201, ok.text
    assert any(f["rule_id"].startswith("UDIN") for f in ok.json()["flags"])
    types = [
        e["event_type"]
        for e in flow.get(f"/v1/audit?case_id={DCE05}", headers=rb()).json()["entries"]
    ]
    assert "document.uploaded" in types and "check.run" in types and "source.response" in types


def test_pick_seeded_document(flow: TestClient) -> None:
    r = flow.post(
        f"/v1/cases/{DCE05}/documents/pick",
        json={"slot": "accounts", "source_case_id": DCE07},
        headers=rb(),
    )
    assert r.status_code == 201
    bad = flow.post(
        f"/v1/cases/{DCE05}/documents/pick",
        json={"slot": "nope", "source_case_id": DCE07},
        headers=rb(),
    )
    assert bad.status_code == 422


def test_roles_regions_and_files(flow: TestClient) -> None:
    ins = auth(token(roles=["INS"]))
    assert flow.get("/v1/cases", headers=ins).status_code == 403
    assert flow.get("/v1/alerts", headers=ins).status_code == 403
    assert flow.get("/v1/audit", headers=ins).status_code == 403
    north = auth(token(groups=["/regions/northern"]))
    assert flow.get(f"/v1/cases/{DIT03}/review", headers=north).status_code == 403
    assert flow.get("/v1/audit", headers=north).json()["entries"] == []
    assert flow.get("/v1/audit", headers=auth(token(roles=["AU"], groups=[]))).status_code == 200
    view = flow.get(f"/v1/cases/{DIT03}/review", headers=rb()).json()
    doc = view["documents"][0]["doc_id"]
    pdf = flow.get(f"/v1/cases/{DIT03}/documents/{doc}/file", headers=rb())
    assert pdf.status_code == 200 and pdf.content.startswith(b"%PDF-")
    assert pdf.headers["x-content-type-options"] == "nosniff"
    assert (
        flow.get(
            f"/v1/cases/{DIT03}/documents/doc_AAAAAAAAAAAAAAAAAAAAAAAAAA/file", headers=rb()
        ).status_code
        == 404
    )


def test_alerts_are_derived_and_link_to_cases(flow: TestClient) -> None:
    items = flow.get("/v1/alerts", headers=rb()).json()["items"]
    kinds = {(a["type"], a["case_id"]) for a in items}
    assert ("suspected_anomaly", DIT03) in kinds  # new High band
    assert ("expired", DCE09) in kinds  # signing certificate had expired
    assert ("pending_source", DIT03) in kinds  # source unavailable task
    assert not any(a["case_id"] == DCE05 for a in items)


@pytest.mark.asyncio
async def test_seed_writes_a_verifiable_chain_and_is_repeatable(tmp_path: Path) -> None:
    from satya_api.demo_seed import seed_all
    from satya_api.ledger import verify_chain
    from satya_api.workflow import Workflow

    store = MemoryStore()
    workflow = Workflow(FixtureCaseRepository(CASES, TOKEN_KEY), store, tmp_path)
    assert len(await seed_all(workflow)) == 5
    assert await seed_all(workflow) == []  # already seeded
    rows = await store.ledger_rows()
    assert verify_chain(rows).ok
    kinds = {r.event_type for r in rows}
    assert {"document.uploaded", "source.response", "check.run", "manual_task.created"} <= kinds
    # edit one entry after the fact: the recomputed chain must flag exactly that row
    import dataclasses

    tampered = [*rows[:2], dataclasses.replace(rows[2], detail_json="{}"), *rows[3:]]
    report = verify_chain(tampered)
    assert not report.ok and report.broken_at == rows[2].seq
