"""S2.7: per-rule precision, recall and false-flag rate on dev and held-out seeds (synthetic).

Targets from docs/SYNTHETIC-TESTSET-PLAN.md §3: precision >= 0.95, recall >= 0.95, FFR <= 0.02.
The tables are printed in the pytest summary (and by `make eval-m6`).
"""

import pytest

from satya_affidavit.synth.institutions import DEV_PROFILES, HELD_OUT_PROFILES
from satya_forensics.eval import corpus, evaluate
from satya_forensics.rules import load_ruleset

from .conftest import METRICS_REPORTS


@pytest.mark.parametrize(
    ("name", "profiles"), [("dev seeds", DEV_PROFILES), ("held-out seeds", HELD_OUT_PROFILES)]
)
def test_metrics_meet_targets(name: str, profiles: tuple[int, ...]) -> None:
    report = evaluate(corpus(profiles), name)
    METRICS_REPORTS.append(report)
    assert report.controls / report.cases >= 0.10
    for rule_id in load_ruleset().rules:
        score = report.rules[rule_id]
        assert score.tp > 0, f"{rule_id} has no planted case in {name}"
        assert score.precision >= 0.95, (rule_id, report.mismatches)
        assert score.recall >= 0.95, (rule_id, report.mismatches)
        assert score.false_flag_rate <= 0.02, (rule_id, report.mismatches)
    assert report.labels.value >= 0.95, report.mismatches
    for group, ratio in report.extraction.items():
        assert ratio.value >= 0.98, group
