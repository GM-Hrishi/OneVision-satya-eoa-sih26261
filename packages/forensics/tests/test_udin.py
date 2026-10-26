"""S2.6: P-18 UDIN structure check on the synthetic audited statement."""

from datetime import date

import pytest

from satya_forensics.engine import ACCOUNTS_SLOT
from satya_forensics.registry import Registry
from satya_forensics.synth.variants import ACCOUNTS_FILE, build_case, make_udin, prior_filings
from satya_forensics.textlayer import read_pages
from satya_forensics.udin import AccountsText, evaluate, read_accounts

from .conftest import run_case


def _acc(
    udin: str | None, member: str = "990321", fy_end: date | None = date(2026, 3, 31)
) -> AccountsText:
    return AccountsText(1, udin, None, member, None, fy_end)


def _failed(findings: list) -> set[str]:  # type: ignore[type-arg]
    return {f"{f.rule_id}:{f.key}" for f in findings if f.failed}


def test_reads_the_auditor_block() -> None:
    case = build_case(15, "clean_udin_spaced")
    acc = read_accounts(read_pages(case.files[ACCOUNTS_FILE]))
    assert acc is not None
    assert acc.udin == case.truth["printed"]["udin"]  # spaces removed
    assert acc.membership_no == case.truth["printed"]["udin.membership_no"]
    assert acc.fy_end == date(2026, 3, 31)


@pytest.mark.parametrize(
    ("udin", "failed"),
    [
        ("26990321ABCDEF1234", set()),
        ("26990321ABCDE1234", {"UDIN-STRUCT:udin:format"}),  # 17 characters
        ("26990321ABCD3F1234", {"UDIN-STRUCT:udin:format"}),  # digit among the letters
        ("25990321ABCDEF1234", {"UDIN-STRUCT:udin:year"}),  # before the FY ended
        ("28990321ABCDEF1234", {"UDIN-STRUCT:udin:year"}),  # two years after
        ("27990321ABCDEF1234", set()),  # audit signed the year after: allowed
        ("26990332ABCDEF1234", {"UDIN-MEMBER:udin:membership_no"}),
    ],
)
def test_structure_year_and_membership(udin: str, failed: set[str]) -> None:
    assert _failed(evaluate(_acc(udin), "1-9000321", Registry(), 1)) == failed


def test_membership_number_is_zero_padded() -> None:
    assert (
        _failed(evaluate(_acc("26012345ABCDEF1234", member="12345"), "1-9", Registry(), 1)) == set()
    )


def test_reuse_across_years_and_institutions_but_not_itself() -> None:
    udin = make_udin(9, "2025-26", "990963")
    registry = Registry()
    registry.add_udin(udin, "1-9000309", "2025-26")
    assert _failed(evaluate(_acc(udin, "990963"), "1-9000309", registry, 1)) == set()
    registry.add_udin(udin, "1-9009909", "2025-26")
    assert _failed(evaluate(_acc(udin, "990963"), "1-9000309", registry, 1)) == {
        "UDIN-REUSE:udin:reuse"
    }


def test_no_udin_means_no_structure_check_and_source_unavailable() -> None:
    assert evaluate(_acc(None), "1-9", Registry(), 1) == []
    case = build_case(3, "clean", demo=True)
    doc = next(d for d in run_case(case).documents if d.slot == ACCOUNTS_SLOT)
    kinds = {c["kind"]: c for c in doc.verification["checks"]}
    assert "format" not in kinds
    lookup = kinds["source_lookup"]
    assert lookup["reason_code"] == "SRC_NO_IDENTIFIER"
    assert lookup["source"]["mode"] == "none"
    assert doc.verification["label"] == "source_unavailable"  # demo F10
    assert doc.source == {"channel": "icai-udin", "adapter_mode": "none"}
    assert doc.issuer_sig is not None and doc.issuer_sig["state"] == "not_digital"


@pytest.mark.parametrize(
    ("variant", "label"),
    [
        ("clean", "source_unavailable"),
        ("udin_length", "manual_review_required"),
        ("udin_member", "manual_review_required"),
        ("udin_year", "manual_review_required"),
        ("udin_reused", "manual_review_required"),
    ],
)
def test_accounts_label(variant: str, label: str) -> None:
    result = run_case(build_case(13, variant), Registry.from_json(prior_filings()))
    doc = next(d for d in result.documents if d.slot == ACCOUNTS_SLOT)
    assert doc.verification["label"] == label
