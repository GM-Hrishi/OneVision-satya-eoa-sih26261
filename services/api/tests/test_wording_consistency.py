"""B-43: the tabs of one case agree, and a page never says "compared" for a file nobody compared.

Synthetic data only. D1: the affidavit diff carries an explicit comparison state. D4: the Case tab
(`/review`) and the Verification tab (`/verification`) read one source of truth.
"""

import asyncio

import pytest
from fastapi.testclient import TestClient

from satya_api.cases import FixtureCaseRepository
from satya_forensics.registry import Registry
from satya_ocr.testing import fake_from_source_pdf

from .test_demo_flow import DCE15, DT13, DT17, flow, rb  # noqa: F401
from .test_ocr_fallback import _source
from .test_workbench_api import CASES, TOKEN_KEY, validator

SCANS = (DT13, DCE15, DT17)


def _case_ids(client: TestClient) -> list[str]:
    return [i["case_id"] for i in client.get("/v1/cases", headers=rb()).json()["items"]]


def test_every_demo_case_shows_the_same_labels_and_counts_on_both_tabs(
    flow: TestClient,  # noqa: F811
) -> None:
    case_ids = _case_ids(flow)
    assert len(case_ids) == 8
    for case_id in case_ids:
        review = flow.get(f"/v1/cases/{case_id}/review", headers=rb()).json()
        tab = flow.get(f"/v1/cases/{case_id}/verification", headers=rb()).json()
        assert [e.message for e in validator("CaseVerification").iter_errors(tab)] == []
        assert {d["doc_id"]: d["label"] for d in review["documents"]} == {
            d["doc_id"]: d["label"] for d in tab["documents"]
        }, case_id
        assert review["label_counts"] == tab["label_counts"], case_id
        # the source and the reason each tab shows come from the same checks
        for doc in review["documents"]:
            row = next(d for d in tab["documents"] if d["doc_id"] == doc["doc_id"])
            assert row["checks"] == doc["checks"], case_id
            assert row["source"] == doc["source"], case_id
            assert row["read"]["reason_code"] == doc["read"]["reason_code"], case_id
            one = flow.get(
                f"/v1/cases/{case_id}/documents/{doc['doc_id']}/verification", headers=rb()
            ).json()
            assert one["label"] == doc["label"] and one["checks"] == doc["checks"], case_id


def test_the_audited_statement_is_verified_on_both_tabs_with_the_simulated_source(
    flow: TestClient,  # noqa: F811
) -> None:
    """Conflict X-42: the stored source answer is SRC_MATCH, so neither tab says unavailable."""
    case_id = "cas_01JD3M5A00000000000000CE05"
    review = flow.get(f"/v1/cases/{case_id}/review", headers=rb()).json()
    tab = flow.get(f"/v1/cases/{case_id}/verification", headers=rb()).json()
    accounts = next(d for d in tab["documents"] if d["source"]["adapter_mode"] == "mock")
    assert accounts["label"] == "verified"
    assert accounts["source"]["adapter_mode"] == "mock"
    assert tab["label_counts"] == review["label_counts"]
    assert tab["label_counts"]["verified"] == 2 and tab["label_counts"]["source_unavailable"] == 0


def test_a_text_layer_file_is_compared_and_a_scan_is_not(flow: TestClient) -> None:  # noqa: F811
    for case_id in _case_ids(flow):
        diff = flow.get(f"/v1/cases/{case_id}/affidavit-diff", headers=rb()).json()
        assert [e.message for e in validator("AffidavitDiff").iter_errors(diff)] == []
        comparison = diff["comparison"]
        if case_id in SCANS:
            assert comparison["state"] == "not_compared", case_id
            assert comparison["read"]["reason_code"] is not None
        else:
            assert comparison["state"] == "compared" and comparison["source"] == "text_layer"
            assert comparison["read"]["reason_code"] is None


def _diff(engine, case_id: str) -> dict:  # type: ignore[no-untyped-def,type-arg]
    repo = FixtureCaseRepository(CASES, TOKEN_KEY, ocr_engine=engine)
    repo._registry = Registry.from_file(repo.registry_file)
    return asyncio.run(repo.m5_diff(case_id))["comparison"]


@pytest.mark.parametrize(
    ("engine", "source", "variant"),
    [
        (None, "ocr_unavailable", "unavailable"),
        (fake_from_source_pdf(_source(13), 0.93), "scan_read", "scan_read"),
        (fake_from_source_pdf(_source(13), 0.2), "scan_unreliable", "low_confidence"),
    ],
)
def test_a_scan_is_never_compared_whatever_the_ocr_gave(engine, source, variant) -> None:  # type: ignore[no-untyped-def]
    comparison = _diff(engine, DT13)
    assert comparison["state"] == "not_compared"
    assert comparison["source"] == source
    assert comparison["read"]["variant"] == variant
    if variant == "scan_read":
        assert 0 < comparison["read"]["ocr_mean_confidence"] <= 1
