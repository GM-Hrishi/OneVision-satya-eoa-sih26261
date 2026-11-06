"""T2: deterministic plain "why" sentences, golden strings, fallbacks and the case summary."""

from fastapi.testclient import TestClient

from satya_api.explain import generic_why, why_detail, why_summary

from .test_demo_flow import DIT03, flow, rb  # noqa: F401


def test_land_area_golden_sentence() -> None:
    flag = {
        "rule_id": "LAND-AREA-RECON",
        "extracted_value": 6.2,
        "expected_value": 4.8,
        "value_unit": "acre",
        "page": 3,
        "aph_clause": "Annex-3 3.1g",
    }
    got = why_detail(flag)
    assert (
        got["text"] == "The affidavit declares 6.20 acres of land; the portal form says 4.80 acres."
    )
    assert got["key"] == "why.LAND-AREA-RECON"
    assert got["params"]["extracted"] == "6.20" and got["params"]["page"] == "3"


def test_document_title_and_page_are_filled() -> None:
    got = why_detail({"rule_id": "SIG-MODIFIED", "doc_title": "Audited statement", "page": 1})
    assert got["text"] == "Audited statement was changed after it was signed."
    got = why_detail({"rule_id": "PDF-FONT-DIFF", "doc_title": "Affidavit", "page": 2})
    assert got["text"] == (
        "A key value on page 2 of Affidavit is set in a different font or size from the text "
        "around it."
    )


def test_hindi_template_is_used_when_asked_and_english_otherwise() -> None:
    flag = {"rule_id": "UDIN-REUSE", "doc_title": "X"}
    assert why_detail(flag, "hi")["text"] != why_detail(flag, "en")["text"]
    assert why_detail(flag, "xx")["text"] == why_detail(flag, "en")["text"]


def test_fallback_uses_rule_title_and_clause_and_is_never_empty() -> None:
    assert why_detail({"rule_id": "NO-SUCH", "aph_clause": "7.4(a)"})["text"] == (
        "A check against APH clause 7.4(a) found a difference to review."
    )
    assert why_detail({"rule_id": "NO-SUCH"})["text"] == "A check found a difference to review."
    assert why_detail({"rule_id": "NO-SUCH"})["key"] == "why.generic"
    assert generic_why({"rule_id": "ROOM-ID-DUP", "aph_clause": "Affidavit-2 NOTE"}) == (
        "The same room ID appears more than once across the four room tables "
        "(APH clause Affidavit-2 NOTE)."
    )


def test_sentences_hold_no_rule_ids_or_unfilled_placeholders() -> None:
    from satya_affidavit.catalogue import load_catalogue

    flag = {"extracted_value": "a", "expected_value": "b", "doc_title": "Doc", "page": 1}
    for rule_id in load_catalogue("en").why:
        text = why_detail({**flag, "rule_id": rule_id})["text"]
        assert rule_id not in text and "{" not in text and text.endswith("."), rule_id


def test_summary_is_most_severe_first_distinct_and_at_most_three() -> None:
    flags = [
        {"flag_id": "f4", "rule_id": "ROOM-ID-DUP", "severity": "warning", "extracted_value": "R1"},
        {"flag_id": "f1", "rule_id": "SIG-DIGEST", "severity": "critical", "doc_title": "Deed"},
        {"flag_id": "f2", "rule_id": "SIG-DIGEST", "severity": "critical", "doc_title": "Deed"},
        {"flag_id": "f3", "rule_id": "AFF-HEADER", "severity": "warning"},
        {"flag_id": "f5", "rule_id": "UDIN-REUSE", "severity": "info", "doc_title": "Accounts"},
    ]
    assert why_summary(flags) == [
        "The content of Deed no longer matches what its digital signature covers.",
        "A field in the opening block of the sworn copy differs from the portal form.",
        "Room ID R1 appears in more than one room table of the affidavit.",
    ]
    assert why_summary([]) == []
    assert why_summary(flags) == why_summary(list(reversed(flags)))  # same input set, same output


def test_review_has_why_detail_and_why_summary_and_keeps_old_fields(
    flow: TestClient,  # noqa: F811
) -> None:
    view = flow.get(f"/v1/cases/{DIT03}/review", headers=rb()).json()
    for flag in view["flags"]:
        assert isinstance(flag["why"], str) and flag["why"]
        assert flag["why_detail"]["text"] and set(flag["why_detail"]) == {"key", "params", "text"}
    assert 1 <= len(view["why_summary"]) <= 3
    land = next(f for f in view["flags"] if f["rule_id"] == "LAND-AREA-RECON")
    assert (
        "acres" in land["why_detail"]["text"]
        and land["doc_title"] in land["why_detail"]["params"]["doc_title"]
    )
    assert (
        flow.get(f"/v1/cases/{DIT03}/review", headers=rb()).json()["why_summary"]
        == view["why_summary"]
    )


def test_queue_rows_carry_why_summary(flow: TestClient) -> None:  # noqa: F811
    items = flow.get("/v1/cases", headers=rb()).json()["items"]
    row = next(i for i in items if i["case_id"] == DIT03)
    assert (
        row["why_summary"]
        == flow.get(f"/v1/cases/{DIT03}/review", headers=rb()).json()["why_summary"]
    )
    assert all(len(i["why_summary"]) <= 3 for i in items)
