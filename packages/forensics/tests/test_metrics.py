"""S2.7: per-rule precision, recall and false-flag rate on dev and held-out seeds (synthetic).

Targets from docs/SYNTHETIC-TESTSET-PLAN.md §3: precision >= 0.95, recall >= 0.95, FFR <= 0.02.
The tables are printed in the pytest summary (and by `make eval-m6`).
"""

import pytest

from satya_affidavit.synth.institutions import DEV_PROFILES, HELD_OUT_PROFILES
from satya_forensics.eval import (
    ADVISORY_NOTES_WITHOUT_PLANTED_CASES,
    RuleScore,
    corpus,
    evaluate,
    scored_rule_ids,
)
from satya_forensics.rules import load_ruleset

from .conftest import METRICS_REPORTS


def assert_planted(rule_id: str, score: RuleScore, name: str) -> None:
    assert score.tp > 0, f"{rule_id} has no planted case in {name}"


def test_allowlist_holds_only_advisory_notes() -> None:
    rules = load_ruleset().rules
    for rule_id in ADVISORY_NOTES_WITHOUT_PLANTED_CASES:
        rule = rules[rule_id]  # also fails if the rule no longer exists
        assert rule.severity == "info", rule_id
        assert rule.preliminary_indicator, rule_id
        assert rule.label == "manual_review_required", rule_id


def test_allowlisted_notes_never_enter_the_figures() -> None:
    scored = scored_rule_ids()
    assert not set(scored) & ADVISORY_NOTES_WITHOUT_PLANTED_CASES
    assert set(scored) | ADVISORY_NOTES_WITHOUT_PLANTED_CASES == set(load_ruleset().rules)


def test_a_new_detection_rule_without_a_planted_case_still_fails() -> None:
    assert "NEW-DETECTION" in scored_rule_ids([*load_ruleset().rules, "NEW-DETECTION"])
    with pytest.raises(AssertionError, match="no planted case"):
        assert_planted("NEW-DETECTION", RuleScore(), "dev seeds")


@pytest.mark.parametrize(
    ("name", "profiles"), [("dev seeds", DEV_PROFILES), ("held-out seeds", HELD_OUT_PROFILES)]
)
def test_metrics_meet_targets(name: str, profiles: tuple[int, ...]) -> None:
    report = evaluate(corpus(profiles), name)
    METRICS_REPORTS.append(report)
    assert report.controls / report.cases >= 0.10
    for rule_id in scored_rule_ids():
        score = report.rules[rule_id]
        assert_planted(rule_id, score, name)
        assert score.precision >= 0.95, (rule_id, report.mismatches)
        assert score.recall >= 0.95, (rule_id, report.mismatches)
        assert score.false_flag_rate <= 0.02, (rule_id, report.mismatches)
    assert report.labels.value >= 0.95, report.mismatches
    for group, ratio in report.extraction.items():
        assert ratio.value >= 0.98, group
