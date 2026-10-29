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
DT13 = "cas_01JD3M5A00000000000000DT13"  # B-28 scan: clean, read by OCR when an engine exists
DCE15 = "cas_01JD3M5A00000000000000CE15"  # B-28 scan: noisy, low confidence
DT17 = "cas_01JD3M5A00000000000000DT17"  # B-28 scan: mixed text and image pages


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
    assert bands == {
        DIT03: "high",
        DT11: "high",
        DCE07: "medium",
        DCE09: "medium",
        DCE05: "low",
        # B-28: a scan, even an unreadable one, does not raise the band (decision O-5)
        DT13: "low",
        DCE15: "low",
        DT17: "low",
    }
    assert body["totals"]["by_band"] == {"high": 2, "medium": 2, "low": 4}
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
    sources = [c["source"] for d in view["documents"] for c in d["checks"] if "source" in c]
    assert sources and all(
        s["mode"] == "mock" for s in sources if s["adapter_id"].endswith("-mock")
    )


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
    assert view["status"] == "all_flags_decided"
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
    # B-28: a damaged PDF is never a 5xx and is not thrown away; it lands on manual review
    assert junk.status_code == 201
    accounts = next(d for d in junk.json()["documents"] if d["slot"].endswith("audited accounts"))
    assert accounts["label"] == "manual_review_required"
    assert accounts["read"]["reason_code"] == "DOC_UNREADABLE"
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


def test_alerts_carry_severity_time_label_clause_and_source(flow: TestClient) -> None:
    items = flow.get("/v1/alerts", headers=rb()).json()["items"]
    assert {a["severity"] for a in items} <= {"critical", "warning", "info"}
    for a in items:
        assert a["created_at"] and a["alert_key"]
        assert (
            a["severity"]
            == {
                "new_high_band": "critical",
                "certificate_expired": "warning",
                "source_unavailable_task": "warning",
                "expiring_soon": "info",
            }[a["subtype"]]
        )
    anomaly = next(a for a in items if a["type"] == "suspected_anomaly" and a["case_id"] == DIT03)
    assert (
        anomaly["flag_id"]
        and anomaly["aph_clause"]
        and anomaly["label"]
        in {
            "verified",
            "mismatch_detected",
            "expired",
            "verification_pending",
            "source_unavailable",
            "manual_review_required",
        }
    )
    pending = next(a for a in items if a["type"] == "pending_source")
    assert pending["label"] == "source_unavailable" and pending["doc_id"]
    assert len({a["alert_key"] for a in items}) == len(items)


@pytest.mark.asyncio
async def test_seed_writes_a_verifiable_chain_and_is_repeatable(tmp_path: Path) -> None:
    from satya_api.demo_seed import seed_all
    from satya_api.ledger import verify_chain
    from satya_api.workflow import Workflow

    store = MemoryStore()
    workflow = Workflow(FixtureCaseRepository(CASES, TOKEN_KEY), store, tmp_path)
    assert len(await seed_all(workflow)) == 8
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


def _bands(rows: list[dict]) -> list[str]:  # type: ignore[type-arg]
    return [r["risk_band"] for r in rows]


def test_queue_sort_applies_within_each_band_group(flow: TestClient) -> None:
    default = flow.get("/v1/cases", headers=rb()).json()
    assert default["sort"] == {
        "key": "undisposed_flags",
        "dir": "desc",
        "default": True,
        "within": "risk_band",
    }
    ranks = {"high": 0, "medium": 1, "low": 2}
    for sort in ("application_id", "undisposed_flags", "submitted_at", "last_activity_at"):
        for direction in ("asc", "desc"):
            body = flow.get(f"/v1/cases?sort={sort}&dir={direction}", headers=rb()).json()
            assert body["sort"]["key"] == sort and body["sort"]["dir"] == direction
            assert body["sort"]["default"] is False
            bands = [ranks[b] for b in _bands(body["items"])]
            assert bands == sorted(bands), "band groups stay in High, Medium, Low order"
            for band in ("high", "medium", "low"):
                keys = [r[sort] for r in body["items"] if r["risk_band"] == band]
                assert keys == sorted(keys, reverse=direction == "desc")
    asc = flow.get("/v1/cases?sort=application_id&dir=asc", headers=rb()).json()["items"]
    desc = flow.get("/v1/cases?sort=application_id&dir=desc", headers=rb()).json()["items"]
    assert {r["case_id"] for r in asc} == {r["case_id"] for r in desc}
    assert all("submitted_at" in r and "last_activity_at" in r for r in asc)


def test_queue_sort_parameters_are_whitelisted(flow: TestClient) -> None:
    for query in ("sort=institution_name", "dir=sideways", "sort=application_id;drop", "sort="):
        r = flow.get(f"/v1/cases?{query}", headers=rb())
        assert r.status_code == 422 and r.json()["code"] == "VALIDATION_FAILED", query
        assert "Traceback" not in r.text


def test_case_status_is_derived_from_the_latest_decision(flow: TestClient) -> None:
    from satya_api.triage import case_status

    flags = [{"flag_id": "a"}, {"flag_id": "b"}]
    assert case_status(flags, {}) == "not_started"
    assert case_status(flags, {"a": "accept"}) == "in_review"
    assert case_status(flags, {"a": "accept", "b": "override"}) == "all_flags_decided"
    assert case_status(flags, {"a": "accept", "b": "escalate_refer"}) == "referred"
    assert case_status(flags, {"a": "escalate_clarify"}) == "waiting_on_institution"
    assert case_status(flags, {"a": "escalate_clarify", "b": "escalate_refer"}) == (
        "waiting_on_institution"
    )
    assert case_status([], {}) == "all_flags_decided"


# ---- GET /v1/overview ---------------------------------------------------------------------------
LABELS_SIX = {
    "verified",
    "mismatch_detected",
    "expired",
    "verification_pending",
    "source_unavailable",
    "manual_review_required",
}


def overview(flow: TestClient, query: str = "", **headers: str) -> dict:  # type: ignore[type-arg]
    r = flow.get(f"/v1/overview{query}", headers=headers or rb())
    assert r.status_code == 200, r.text
    return r.json()  # type: ignore[no-any-return]


def test_overview_has_the_agreed_shape_and_matches_the_queue(flow: TestClient) -> None:
    body = overview(flow)
    assert body["ay"] == "2026-27" and body["route"] == "self_disclosure" and body["as_of"]
    assert body["advisory"] is True
    queue = flow.get("/v1/cases", headers=rb()).json()
    assert body["cases"]["submitted"] == queue["totals"]["submitted"] == 8
    assert body["cases"]["by_band"] == queue["totals"]["by_band"]
    assert set(body["status"]) == {
        "not_started",
        "in_review",
        "waiting_on_institution",
        "referred",
        "all_flags_decided",
    }
    # DCE05 and the three scan cases have no flags (all decided); the other four have findings
    assert body["status"]["all_flags_decided"] == 4 and body["status"]["not_started"] == 4
    assert sum(body["status"].values()) == body["cases"]["submitted"]
    assert set(body["documents"]["by_label"]) == LABELS_SIX
    assert body["documents"]["total"] == sum(body["documents"]["by_label"].values()) == 16
    assert body["manual_tasks"]["open"] == sum(i["manual_tasks"] for i in queue["items"])
    assert len(body["manual_tasks"]["top"]) <= 5
    assert set(body["expiring"]) == {"d30", "d60", "d90", "top"}
    assert body["expiring"]["d30"] <= body["expiring"]["d60"] <= body["expiring"]["d90"]
    assert {s["adapter_id"] for s in body["sources"]} == {
        "cca-offline-chain",
        "shcil-estamp-mock",
        "icai-udin-mock",
    }
    assert all(s["status"] == "answering" for s in body["sources"])
    assert body["recent_decisions"] == []


def test_overview_tracks_decisions_and_status(flow: TestClient) -> None:
    view = flow.get(f"/v1/cases/{DT11}/review", headers=rb()).json()
    flag = view["flags"][0]["flag_id"]
    ok = flow.post(
        f"/v1/cases/{DT11}/flags/{flag}/disposition",
        json={"action": "escalate_clarify", "reason": "ask the institution to explain"},
        headers=rb(),
    )
    assert ok.status_code == 201
    body = overview(flow)
    assert body["status"]["waiting_on_institution"] == 1 and body["status"]["not_started"] == 3
    recent = body["recent_decisions"]
    assert len(recent) == 1 and recent[0]["action"] == "escalate_clarify"
    assert recent[0]["case_id"] == DT11 and recent[0]["flag_id"] == flag
    assert recent[0]["by_role"] == "RB" and recent[0]["ledger_no"] >= 1
    # the latest decision wins: referring the same flag moves the case to "referred"
    flow.post(
        f"/v1/cases/{DT11}/flags/{flag}/disposition",
        json={"action": "escalate_refer", "reason": "refer to the committee"},
        headers=rb(),
    )
    body = overview(flow)
    assert body["status"]["referred"] == 1 and body["status"]["waiting_on_institution"] == 0
    assert body["recent_decisions"][0]["action"] == "escalate_refer"


def test_overview_is_scoped_by_role_and_region(flow: TestClient) -> None:
    assert flow.get("/v1/overview").status_code == 401
    ins = auth(token(roles=["INS"]))
    assert flow.get("/v1/overview", headers=ins).status_code == 403
    north = auth(token(groups=["/regions/northern"]))
    empty = overview(flow, "", **north)
    assert empty["cases"]["submitted"] == 0 and empty["documents"]["total"] == 0
    assert empty["manual_tasks"]["open"] == 0 and empty["recent_decisions"] == []
    # asking for another region than the one the official may see is refused
    denied = flow.get("/v1/overview?region=northern", headers=rb())
    assert denied.status_code == 403 and denied.json()["code"] == "SCOPE_DENIED"
    assert flow.get("/v1/overview?region=national", headers=rb()).status_code == 403
    assert overview(flow, "?region=southern")["cases"]["submitted"] == 8
    national = auth(token(groups=["/regions/national"]))
    assert overview(flow, "", **national)["cases"]["submitted"] == 8
    assert overview(flow, "?region=southern", **national)["cases"]["submitted"] == 8
    assert overview(flow, "?region=northern", **national)["cases"]["submitted"] == 0


def test_overview_parameters_are_whitelisted(flow: TestClient) -> None:
    assert overview(flow, "?ay=2025-26")["cases"]["submitted"] == 0
    for query in ("?ay=2030-31", "?ay=2026-27;drop"):
        r = flow.get(f"/v1/overview{query}", headers=rb())
        assert r.status_code == 422 and r.json()["code"] == "UNSUPPORTED_AY", query
    for query in ("?region=South%20ern", "?region=../etc", "?region=" + "a" * 40, "?region=1"):
        r = flow.get(f"/v1/overview{query}", headers=rb())
        assert r.status_code == 422 and r.json()["code"] == "VALIDATION_FAILED", query
        assert "Traceback" not in r.text


def test_overview_has_its_own_rate_limit(tmp_path: Path) -> None:
    async def fetch() -> dict:  # type: ignore[type-arg]
        return _jwks()

    settings = Settings(
        env="test",
        rate_limit="1000/minute",
        user_rate_limit="1000/minute",
        overview_rate_limit="2/minute",
        upload_dir=str(tmp_path),
    )
    app = create_app(
        settings,
        store=MemoryStore(),
        checks={"postgres": _ok, "valkey": _ok, "keycloak": _ok},
        cases=FixtureCaseRepository(CASES, TOKEN_KEY),
        verifier=TokenVerifier(ISSUER, "satya-web", fetch),
    )
    with TestClient(app) as client:
        # Fixed window of 2 per minute: six calls span at most two windows, so one window gets
        # three or more and at least one call is refused (robust if a minute boundary passes).
        responses = [client.get("/v1/overview", headers=rb()) for _ in range(6)]
        codes = [r.status_code for r in responses]
        assert codes[0] == 200 and 429 in codes and codes.count(200) <= 4
        assert all(r.headers["retry-after"] for r in responses if r.status_code == 429)
        assert (
            client.get("/v1/cases", headers=rb()).status_code == 200
        )  # other endpoints unaffected
