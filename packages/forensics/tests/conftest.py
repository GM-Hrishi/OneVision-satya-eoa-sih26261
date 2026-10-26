"""Shared helpers for the M6 tests. Synthetic data only."""

from typing import Any

from satya_forensics import pki
from satya_forensics.engine import M6Input, M6Result, run
from satya_forensics.eval import Report
from satya_forensics.registry import Registry
from satya_forensics.signatures import TrustStore
from satya_forensics.synth.variants import M6Case, prior_filings

KEY = b"satya-m6-test-token-key-synthetic-0001"
CHECKED_AT = "2026-11-25T10:00:00+05:30"


def run_case(case: M6Case, registry: Registry | None = None) -> M6Result:
    files = {d["doc_id"]: case.files[d["file"]] for d in case.case["documents"]}
    return run(
        M6Input(
            case=case.case,
            snapshot=case.snapshot,
            files=files,
            token_key=KEY,
            trust=TrustStore.test_anchor(),
            revocation=pki.standard_crl_endpoints(list(case.crl_specs)),
            registry=registry or Registry.from_json(prior_filings()),
            checked_at=CHECKED_AT,
        )
    )


METRICS_REPORTS: list[Report] = []


def pytest_terminal_summary(terminalreporter: Any) -> None:
    """Print the M6/P-18 metrics tables (test_metrics.py) after every run that computed them."""
    if not METRICS_REPORTS:
        return
    terminalreporter.section("M6 signatures, stamp chronology, UDIN metrics (synthetic test set)")
    for report in METRICS_REPORTS:
        terminalreporter.write_line(report.table())
        for line in report.mismatches:
            terminalreporter.write_line(f"  {line}")
        terminalreporter.write_line("")
