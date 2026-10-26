"""S2.5: stamp page, notary block and signing-order rules (packages/rules/m6-signatures.yaml)."""

from typing import Any

import pytest

from satya_forensics.engine import AFFIDAVIT_SLOT
from satya_forensics.registry import Registry
from satya_forensics.rules import load_ruleset
from satya_forensics.stamp import read_notary, read_stamp
from satya_forensics.synth.variants import AFFIDAVIT_FILE, build_case, prior_filings
from satya_forensics.textlayer import read_pages
from satya_shared_types import models, validator

from .conftest import run_case

STAMP_RULES = {
    "STAMP-CHRONO",
    "STAMP-PARTY",
    "STAMP-DUTY",
    "STAMP-INSTRUMENT",
    "STAMP-REUSE",
    "NOTARY-EXPIRY",
}


def _m6_refs(result: Any) -> set[str]:
    return {f["check_ref"] for f in result.flags if f["rule_id"] in STAMP_RULES}


def test_rules_cite_aph_clauses() -> None:
    rules = load_ruleset()
    for rule_id in STAMP_RULES:
        rule = rules[rule_id]
        assert rule.aph_clause in {"2.3.4b", "Annex-2.1(i)"}
        assert rule.reason_code != rule.pass_code


def test_stamp_page_and_notary_block_are_read() -> None:
    case = build_case(5, "clean")
    pages = read_pages(case.files[AFFIDAVIT_FILE])
    stamp = read_stamp(pages)
    assert stamp is not None and stamp.instrument == "e-stamp" and stamp.page == 1
    assert stamp.certificate_no == case.truth["printed"]["stamp.certificate_no"]
    assert stamp.second_party == "AICTE NEW DELHI"
    assert stamp.duty_rupees == 100
    assert stamp.article == "Article 4 Affidavit"
    assert (
        stamp.issued is not None
        and stamp.issued.isoformat() == case.truth["printed"]["stamp.issued"]
    )
    notary = read_notary(pages, "MM/DD/YYYY")
    assert notary is not None and notary.reg_no == "DEMO-NOT-0005"
    assert (
        notary.notarised is not None
        and notary.notarised.isoformat() == case.truth["printed"]["notary.date"]
    )
    assert notary.seal_valid_till is not None
    assert notary.seal_valid_till.isoformat() == case.truth["printed"]["notary.valid_till"]


@pytest.mark.parametrize(
    ("variant", "refs"),
    [
        ("clean", set()),
        ("clean_same_day", set()),
        ("clean_ambiguous_dates", set()),
        ("chrono_stamp_after_notary", {"m6:STAMP-CHRONO:chronology:order"}),
        ("chrono_dsc_before_notary", {"m6:STAMP-CHRONO:chronology:order"}),
        ("chrono_mark_after_notary", {"m6:STAMP-CHRONO:chronology:mark_after_notary"}),
        ("sig_image_only", set()),
        ("stamp_party", {"m6:STAMP-PARTY:stamp:second_party"}),
        ("stamp_duty", {"m6:STAMP-DUTY:stamp:duty"}),
        ("stamp_physical", {"m6:STAMP-INSTRUMENT:stamp:instrument"}),
        ("stamp_reused", {"m6:STAMP-REUSE:stamp:certificate_no"}),
        ("notary_expired", {"m6:NOTARY-EXPIRY:notary:seal_expiry"}),
    ],
)
def test_each_rule_fires_only_on_its_variant(variant: str, refs: set[str]) -> None:
    assert _m6_refs(run_case(build_case(11, variant))) == refs


def test_ambiguous_dates_follow_the_template_order() -> None:
    case = build_case(15, "clean_ambiguous_dates")
    result = run_case(case)
    chrono = result.affidavit["chronology"]  # type: ignore[index]
    assert chrono["application_date"].endswith("-03")
    assert chrono["notary_date"] == case.truth["printed"]["notary.date"]
    assert chrono["order_ok"] is True


def test_affidavit_section_matches_the_contract() -> None:
    result = run_case(build_case(3, "chrono_mark_after_notary"))
    section = result.affidavit
    assert section is not None
    models.AffidavitStamp.model_validate(section["stamp"])  # Pydantic contract (strict extras)
    models.AffidavitChronology.model_validate(section["chronology"])
    chrono = section["chronology"]
    assert chrono["dsc_kind"] == "image_mark" and chrono["mark_after_notary"] is True
    assert chrono["order_ok"] is True  # the order itself holds; the mark is the finding
    stamp = section["stamp"]
    assert stamp["duty"] == 10000  # paise
    assert stamp["certificate_no"].startswith("•••")  # identifiers masked (Portal §3)
    assert stamp["state"] == "verification_pending"  # format passed; SHCIL lookup is M7


def test_stamp_state_takes_the_worst_stamp_finding() -> None:
    result = run_case(build_case(7, "stamp_duty"))
    assert result.affidavit["stamp"]["state"] == "mismatch_detected"  # type: ignore[index]
    doc = next(d for d in result.documents if d.slot == AFFIDAVIT_SLOT)
    assert doc.verification["label"] == "mismatch_detected"


def test_reuse_against_current_cases_and_not_against_itself() -> None:
    case = build_case(13, "clean")
    number = case.case["stamp"]["certificate_no"]
    registry = Registry.from_json(prior_filings())
    registry.add_stamp(number, case.case["application_id"], case.case["ay"])  # the case itself
    assert _m6_refs(run_case(case, registry)) == set()
    registry.add_stamp(number, "1-90000099999", case.case["ay"])  # another application
    flag = next(f for f in run_case(case, registry).flags if f["rule_id"] == "STAMP-REUSE")
    assert flag["extracted_value"].startswith("•••")


def test_checks_carry_pass_codes_and_evidence() -> None:
    doc = next(d for d in run_case(build_case(5, "clean")).documents if d.slot == AFFIDAVIT_SLOT)
    codes = {c["reason_code"] for c in doc.verification["checks"]}
    assert {
        "STAMP_E_STAMP",
        "STAMP_PARTY_OK",
        "STAMP_DUTY_OK",
        "STAMP_NO_UNIQUE",
        "NOTARY_SEAL_VALID",
        "CHRONO_OK",
    } <= codes
    expiry = next(c for c in doc.verification["checks"] if c["kind"] == "expiry")
    assert expiry["basis"] == "printed" and expiry["evidence"]["page"] >= 1
    assert list(validator("VerificationResult").iter_errors(doc.verification)) == []
