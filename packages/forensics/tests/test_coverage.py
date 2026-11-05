"""T5: certificate coverage of the submission date: boundaries, labels, session window."""

from datetime import date

import pytest

from satya_forensics.coverage import (
    COVERS,
    EXPIRED,
    NOT_YET,
    UNKNOWN,
    CoverageConfig,
    certificate_coverage,
    coverage_check,
    coverage_outcome,
    is_time_bound,
    load_config,
    session_coverage,
    session_end_of,
)
from satya_forensics.flags import FlagFactory
from satya_forensics.labels import document_label
from satya_forensics.rules import load_ruleset

SUBMITTED = date(2026, 11, 20)
LABELS = {
    "verified",
    "mismatch_detected",
    "expired",
    "verification_pending",
    "source_unavailable",
    "manual_review_required",
}


def cov(valid_from: date | None, valid_to: date | None) -> dict[str, object]:
    return certificate_coverage(valid_from, valid_to, SUBMITTED)


def test_validity_ending_on_the_submission_date_still_covers() -> None:
    assert cov(None, SUBMITTED) == {
        "status": COVERS,
        "valid_from": None,
        "valid_to": "2026-11-20",
        "days_off": 0,
    }


def test_validity_ending_one_day_before_is_expired_by_one_day() -> None:
    got = cov(date(2025, 11, 20), date(2026, 11, 19))
    assert (got["status"], got["days_off"]) == (EXPIRED, 1)


def test_validity_ending_one_day_after_covers() -> None:
    assert cov(None, date(2026, 11, 21))["status"] == COVERS


def test_validity_starting_on_the_submission_date_covers_and_one_day_after_is_not_yet_valid() -> (
    None
):
    assert cov(SUBMITTED, date(2027, 11, 19))["status"] == COVERS
    got = cov(date(2026, 11, 21), date(2027, 11, 20))
    assert (got["status"], got["days_off"]) == (NOT_YET, 1)


def test_long_expiry_counts_days() -> None:
    assert cov(None, date(2026, 8, 14))["days_off"] == 98


def test_unknown_when_no_end_date_or_dates_contradict() -> None:
    assert cov(None, None) == {
        "status": UNKNOWN,
        "valid_from": None,
        "valid_to": None,
        "days_off": None,
    }
    assert cov(date(2025, 1, 1), None)["status"] == UNKNOWN
    assert cov(date(2027, 1, 1), date(2026, 1, 1))["status"] == UNKNOWN


def test_statuses_map_to_existing_labels_only() -> None:
    cases = {
        EXPIRED: ("expired", "CERT_EXPIRED_BEFORE_SUBMISSION"),
        NOT_YET: ("manual_review_required", "CERT_NOT_YET_VALID"),
        UNKNOWN: ("manual_review_required", "CERT_VALIDITY_UNKNOWN"),
        COVERS: ("verified", "CERT_COVERS_SUBMISSION"),
    }
    for status, (label, reason) in cases.items():
        check = coverage_check(
            {"status": status, "valid_from": None, "valid_to": None, "days_off": 0}
        )
        assert (check["outcome"], check["reason_code"], check["kind"]) == (label, reason, "expiry")
        assert check["outcome"] in LABELS
    assert document_label([coverage_check(cov(None, date(2026, 8, 14)))]) == "expired"


def factory() -> FlagFactory:
    return FlagFactory(load_ruleset(), "doc_X", "a" * 64, "Fire safety certificate")


def test_expired_certificate_raises_one_flag_with_dates() -> None:
    checks = [
        {
            "kind": "expiry",
            "outcome": "verified",
            "valid_from": "2025-03-01",
            "valid_to": "2026-08-14",
        }
    ]
    check, flags = coverage_outcome(checks, SUBMITTED, "2026-27", factory())
    assert check["outcome"] == "expired" and check["coverage"]["days_off"] == 98
    assert [f["rule_id"] for f in flags] == ["CERT-COVERAGE-EXPIRED"]
    flag = flags[0]
    assert flag["label"] == "expired" and flag["preliminary_indicator"] is True
    assert flag["why_extra"]["valid_to"] == "2026-08-14" and flag["why_extra"]["days_off"] == 98
    assert flag["disposition"] is None


def test_covering_certificate_raises_nothing_and_missing_dates_ask_for_a_person() -> None:
    ok = [{"kind": "expiry", "valid_from": "2025-03-01", "valid_to": "2028-02-29"}]
    check, flags = coverage_outcome(ok, SUBMITTED, "2026-27", factory())
    assert check["outcome"] == "verified" and flags == []
    check, flags = coverage_outcome([], SUBMITTED, "2026-27", factory())
    assert check["outcome"] == "manual_review_required"
    assert [f["rule_id"] for f in flags] == ["CERT-COVERAGE-UNKNOWN"]


def test_session_window_is_off_by_default() -> None:
    config = load_config()
    assert config.session_enabled is False
    assert session_coverage(date(2027, 1, 1), "2026-27") is None
    ok = [{"kind": "expiry", "valid_to": "2027-01-01"}]
    check, flags = coverage_outcome(ok, SUBMITTED, "2026-27", factory())
    assert "session" not in check["coverage"] and flags == []


def test_session_window_when_enabled_by_configuration() -> None:
    config = CoverageConfig(("fire_safety_certificate",), session_enabled=True)
    assert session_end_of("2026-27", config) == date(2027, 6, 30)
    short = session_coverage(date(2027, 1, 1), "2026-27", config)
    assert short == {
        "status": "ends_before_session_end",
        "session_end": "2027-06-30",
        "days_short": 180,
    }
    assert session_coverage(date(2027, 6, 30), "2026-27", config)["status"] == "covers_session"  # type: ignore[index]
    check, flags = coverage_outcome(
        [{"kind": "expiry", "valid_to": "2027-01-01"}], SUBMITTED, "2026-27", factory(), config
    )
    assert check["outcome"] == "verified"  # still covers the submission date
    assert [f["rule_id"] for f in flags] == ["CERT-SESSION-GAP"]
    assert flags[0]["why_extra"]["session_end"] == "2027-06-30"


def test_config_lists_the_time_bound_types_and_marks_the_open_clause() -> None:
    assert is_time_bound("fire_safety_certificate")
    assert not is_time_bound("affidavit-2") and not is_time_bound(None)
    text = (load_ruleset_path() / "coverage.yaml").read_text("utf-8")
    assert "[VERIFY APH clause]" in text


def load_ruleset_path():  # type: ignore[no-untyped-def]
    from satya_affidavit.paths import rules_dir

    return rules_dir()


@pytest.mark.parametrize(
    "rule_id",
    ["CERT-COVERAGE-EXPIRED", "CERT-COVERAGE-NOT-YET", "CERT-COVERAGE-UNKNOWN", "CERT-SESSION-GAP"],
)
def test_coverage_rules_have_limitation_and_cite_a_clause(rule_id: str) -> None:
    rule = load_ruleset()[rule_id]
    assert rule.limitation_key == "certificate_dates" and "VERIFY" in rule.aph_clause
