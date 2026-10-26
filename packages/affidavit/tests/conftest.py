"""Shared fixtures for the M5 tests. Synthetic data only."""

import json
from pathlib import Path
from typing import Any

import pytest

from satya_affidavit.eval import Report

REPO = Path(__file__).resolve().parents[3]
METRICS_REPORTS: list[Report] = []


def pytest_terminal_summary(terminalreporter: Any) -> None:
    """Print the M5 metrics tables (test_metrics.py) after every run that computed them."""
    if not METRICS_REPORTS:
        return
    terminalreporter.section("M5 affidavit diff metrics (synthetic test set)")
    for report in METRICS_REPORTS:
        terminalreporter.write_line(report.table())
        for line in report.mismatches:
            terminalreporter.write_line(f"  {line}")
        terminalreporter.write_line("")


@pytest.fixture
def example_snapshot() -> dict[str, Any]:
    path = REPO / "packages/shared-types/examples/valid/ApplicationSnapshot.json"
    loaded: dict[str, Any] = json.loads(path.read_text("utf-8"))
    return loaded


@pytest.fixture
def example_case() -> dict[str, Any]:
    return {
        "affidavit_draft": {
            "template_id": "aff2-portal-2024-27",
            "header": {
                "institution_name": "Demo Institute of Technology 03",
                "address": "Demo Town 03, Demo District 07, Tamil Nadu",
                "town": "Demo Town 03",
            },
        }
    }
