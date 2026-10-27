"""S2.2: synthetic signed documents, stamp/notary pages and audited statements."""

import io
import json

import pdfplumber
import pytest
from pyhanko.pdf_utils.reader import PdfFileReader

from satya_forensics.synth.corpus import DEMO_CASES, check_all, synthetic_root
from satya_forensics.synth.variants import (
    ACCOUNTS_FILE,
    AFFIDAVIT_FILE,
    CONTROLS,
    PLANTED,
    VARIANTS,
    build_case,
    prior_filings,
)
from satya_shared_types import validator


def _signatures(pdf: bytes) -> list[str]:
    return [s.field_name for s in PdfFileReader(io.BytesIO(pdf)).embedded_signatures]


def _text(pdf: bytes) -> list[str]:
    with pdfplumber.open(io.BytesIO(pdf)) as doc:
        return [page.extract_text() or "" for page in doc.pages]


def test_controls_are_at_least_ten_percent() -> None:
    assert len(VARIANTS) == len(set(VARIANTS))
    assert len(CONTROLS) / len(VARIANTS) >= 0.10
    assert set(CONTROLS).isdisjoint(PLANTED)


def test_generation_is_deterministic() -> None:
    a, b = build_case(7, "sig_modified"), build_case(7, "sig_modified")
    assert a.files == b.files
    assert a.truth == b.truth


@pytest.mark.parametrize(
    ("variant", "fields"),
    [
        ("clean", ["DeponentSignature", "UploaderSignature"]),
        ("sig_image_only", ["UploaderSignature"]),
        ("uploader_missing", ["DeponentSignature"]),
        ("clean_odd_metadata", ["Signature1", "UploaderSignature"]),
    ],
)
def test_real_signatures_carry_a_byte_range(variant: str, fields: list[str]) -> None:
    case = build_case(11, variant)
    assert _signatures(case.files[AFFIDAVIT_FILE]) == fields
    assert b"/ByteRange" in case.files[AFFIDAVIT_FILE]
    assert _signatures(case.files[ACCOUNTS_FILE]) == ["UploaderSignature"]


def test_image_mark_is_printed_text_without_a_signature() -> None:
    case = build_case(5, "chrono_mark_after_notary")
    last = _text(case.files[AFFIDAVIT_FILE])[-1]
    assert "Digitally signed by Demo Trustee 05" in last
    assert "Signature valid" in last
    assert case.truth["timeline"]["mark"] > case.truth["timeline"]["notarised"]
    assert "DeponentSignature" not in _signatures(case.files[AFFIDAVIT_FILE])


def test_edits_after_signing_add_revisions() -> None:
    clean = build_case(9, "clean").files[AFFIDAVIT_FILE]
    for variant in ("sig_modified", "clean_benign_info", "clean_benign_dss"):
        edited = build_case(9, variant).files[AFFIDAVIT_FILE]
        assert edited.count(b"%%EOF") == clean.count(b"%%EOF") + 1, variant


def test_stamp_page_fields_and_physical_paper() -> None:
    estamp = _text(build_case(13, "clean").files[AFFIDAVIT_FILE])[0]
    for label in (
        "Certificate No.",
        "Second Party",
        "Stamp Duty Amount",
        "Description of Document",
    ):
        assert label in estamp
    assert "AICTE NEW DELHI" in estamp and "IN-TN9" in estamp
    physical = _text(build_case(13, "stamp_physical").files[AFFIDAVIT_FILE])[0]
    assert "NON-JUDICIAL STAMP PAPER" in physical and "Certificate No." not in physical


def test_audited_statement_prints_udin_and_membership() -> None:
    case = build_case(15, "clean_udin_spaced")
    text = _text(case.files[ACCOUNTS_FILE])[0]
    udin = case.truth["printed"]["udin"]
    assert len(udin) == 18
    assert udin[2:8] == case.truth["printed"]["udin.membership_no"]
    assert f"UDIN: {udin[:2]} {udin[2:8]}" in text
    assert "Firm Registration No.: 0" in text  # 7+1 form with a leading zero


def test_every_page_says_synthetic() -> None:
    case = build_case(3, "clean")
    for name in (AFFIDAVIT_FILE, ACCOUNTS_FILE):
        for page in _text(case.files[name]):
            assert "SYNTHETIC" in page


@pytest.mark.parametrize("variant", PLANTED)
def test_planted_variants_record_findings(variant: str) -> None:
    truth = build_case(17, variant).truth
    assert truth["control"] is False
    assert truth["expected_flags"]
    for flag in truth["expected_flags"]:
        assert flag["check_ref"].startswith(f"m6:{flag['rule_id']}:")


@pytest.mark.parametrize("variant", CONTROLS)
def test_controls_expect_nothing(variant: str) -> None:
    case = build_case(17, variant)
    assert case.truth["control"] is True
    assert case.truth["expected_flags"] == []
    labels = set(case.truth["expected_document_labels"].values())
    assert labels == {"verified", "source_unavailable"}


def test_snapshots_stay_valid() -> None:
    for variant in ("clean", "clean_ambiguous_dates"):
        case = build_case(3, variant)
        assert list(validator("ApplicationSnapshot").iter_errors(case.snapshot)) == []


def test_registry_is_unique_and_clean_numbers_are_not_in_it() -> None:
    registry = prior_filings()
    stamps = [s["certificate_no"] for s in registry["stamps"]]
    udins = [u["udin"] for u in registry["udins"]]
    assert len(stamps) == len(set(stamps)) and len(udins) == len(set(udins))
    clean = build_case(7, "clean")
    assert clean.case["stamp"]["certificate_no"] not in stamps
    assert clean.truth["printed"]["udin"] not in udins


def test_demo_case_story() -> None:
    root = synthetic_root()
    truth = json.loads((root / "cases/dit03-2026-27/truth-m6.json").read_text("utf-8"))
    refs = {f["check_ref"] for f in truth["expected_flags"]}
    assert refs == {"m6:SIG-IMAGE:issuer", "m6:STAMP-CHRONO:chronology:mark_after_notary"}
    assert truth["printed"]["udin"] is None  # F10: no UDIN on the audited statement
    clean = json.loads((root / "cases/dce05-2026-27/truth-m6.json").read_text("utf-8"))
    assert clean["expected_flags"] == []
    assert len(DEMO_CASES) == 5


def test_committed_synthetic_files_match_a_fresh_generation() -> None:
    assert check_all() == [], "run `make synth` and commit data/synthetic"
