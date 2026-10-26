"""M5 metrics over the T2 synthetic test set (docs/SYNTHETIC-TESTSET-PLAN.md §3, §5.1).

Runs all 104 synthetic sworn affidavits (8 institutions x 4 clean controls + 9 planted anomalies),
prints precision, recall, false-flag rate and extraction accuracy per rule (see the pytest summary),
and holds every rule to the Phase-1 targets. A miss is reported, never hidden.
"""

import pytest

from satya_affidavit.eval import Report, corpus, evaluate
from satya_affidavit.rules import load_ruleset
from satya_affidavit.synth.institutions import DEV_PROFILES, HELD_OUT_PROFILES

from .conftest import METRICS_REPORTS

PRECISION_TARGET = 0.95
RECALL_TARGET = 0.95
FFR_TARGET = 0.02
EXTRACTION_TARGET = 0.98


@pytest.mark.parametrize(
    ("name", "profiles"), [("dev seeds", DEV_PROFILES), ("held-out seeds", HELD_OUT_PROFILES)]
)
def test_metrics_meet_phase_1_targets(name: str, profiles: tuple[int, ...]) -> None:
    report: Report = evaluate(corpus(profiles), name)
    METRICS_REPORTS.append(report)
    assert report.cases == len(profiles) * 13
    failures = []
    for rule_id in load_ruleset().rules:
        score = report.rules[rule_id]
        assert score.tp + score.fn > 0, f"{rule_id} has no planted case"
        assert score.controls > 0, f"{rule_id} has no clean control"
        if score.precision < PRECISION_TARGET or score.recall < RECALL_TARGET:
            failures.append(
                f"{rule_id}: precision {score.precision:.3f}, recall {score.recall:.3f}"
            )
        if score.false_flag_rate > FFR_TARGET:
            failures.append(f"{rule_id}: false-flag rate {score.false_flag_rate:.3f}")
        if report.extraction(rule_id) < EXTRACTION_TARGET:
            failures.append(f"{rule_id}: extraction accuracy {report.extraction(rule_id):.3f}")
    assert failures == [], "\n".join(failures + report.mismatches)
