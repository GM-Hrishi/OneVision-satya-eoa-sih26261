"""Synthetic generator (S1.3): deterministic, schema-valid, marked SYNTHETIC, truth recorded."""

import io
from typing import Any

import pdfplumber
import pytest

from satya_affidavit.synth.institutions import DEV_PROFILES, HELD_OUT_PROFILES, PROFILES
from satya_affidavit.synth.variants import CONTROL_STYLES, PLANTED, VARIANTS, generate
from satya_shared_types import validator


def test_profiles_split_into_dev_and_held_out() -> None:
    assert set(DEV_PROFILES) | set(HELD_OUT_PROFILES) == set(PROFILES)
    assert not set(DEV_PROFILES) & set(HELD_OUT_PROFILES)
    assert len(VARIANTS) == 13


@pytest.mark.parametrize("profile", sorted(PROFILES))
def test_snapshots_are_valid_application_snapshots(profile: int) -> None:
    case = generate(profile, "clean")
    errors = [e.message for e in validator("ApplicationSnapshot").iter_errors(case.snapshot)]
    assert errors == []
    assert case.case["application_id"].startswith("1-9")


def test_generation_is_deterministic() -> None:
    assert generate(7, "clause_narrowed").pdf == generate(7, "clause_narrowed").pdf


def test_every_page_says_synthetic() -> None:
    case = generate(3, "clean_hyphenated")
    with pdfplumber.open(io.BytesIO(case.pdf)) as pdf:
        for page in pdf.pages:
            assert "SYNTHETIC" in (page.extract_text() or "")


@pytest.mark.parametrize("variant", PLANTED)
def test_planted_variants_record_their_flags(variant: str) -> None:
    truth: dict[str, Any] = generate(11, variant).truth
    assert truth["control"] is False
    assert truth["expected_flags"], variant
    for flag in truth["expected_flags"]:
        assert flag["check_ref"].startswith(f"m5:{flag['rule_id']}:")


@pytest.mark.parametrize("variant", sorted(CONTROL_STYLES))
def test_controls_expect_no_flags(variant: str) -> None:
    truth = generate(5, variant).truth
    assert truth["control"] is True
    assert truth["expected_flags"] == []


def test_demo_case_plants_the_four_demo_findings() -> None:
    truth = generate(3, "clean", demo=True).truth
    refs = {f["check_ref"] for f in truth["expected_flags"]}
    assert refs == {
        "m5:AFF-CAT-LINE:category_line",
        "m5:AFF-DECL-CHANGED:decl:9",
        "m5:LAND-AREA-RECON:land:2:area_acre",
        "m5:LAND-AREA-RECON:land:total",
        "m5:ROOM-ID-DUP:room_id:I-201",
    }
