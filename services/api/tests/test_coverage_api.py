"""T5 in the API: the coverage check lands in the document, its flag carries why and limitation."""

from datetime import date

from satya_api.explain import limitation_for, why_detail
from satya_api.workflow import apply_coverage, submission_date

CASE = {
    "ay": "2026-27",
    "documents": [
        {"uploaded_at": "2026-11-18T10:00:00+05:30"},
        {"uploaded_at": "2026-11-20T09:00:00+05:30"},
    ],
}
META = {"declared_type": "fire_safety_certificate", "sha256": "b" * 64}


def test_submission_date_is_the_latest_upload_day() -> None:
    assert submission_date(CASE) == date(2026, 11, 20)


def test_expired_certificate_turns_the_document_label_to_expired_with_a_plain_sentence() -> None:
    verification = {
        "label": "verified",
        "checks": [
            {
                "kind": "expiry",
                "outcome": "verified",
                "valid_from": "2025-03-01",
                "valid_to": "2026-08-14",
            }
        ],
    }
    flags = apply_coverage(verification, META, "doc_1", "Fire safety certificate", CASE)
    assert verification["label"] == "expired"
    assert verification["checks"][-1]["coverage"]["status"] == "expired_before_submission"
    flag = flags[0]
    titled = {**flag, "doc_title": "Fire safety certificate"}
    text = why_detail(titled)["text"]
    assert text == (
        "The Fire safety certificate ended on 2026-08-14, 98 days before the submission date "
        "of 2026-11-20."
    )
    assert limitation_for(flag)["key"] == "limitation.certificate_dates"  # type: ignore[index]


def test_other_document_types_are_untouched() -> None:
    verification = {"label": "verified", "checks": []}
    assert apply_coverage(verification, {"declared_type": "affidavit-2"}, "d", "t", CASE) == []
    assert verification == {"label": "verified", "checks": []}
