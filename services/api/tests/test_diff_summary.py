"""T3: affidavit-diff summary counts and per-declaration why sentences (additive fields)."""

from typing import Any

from fastapi.testclient import TestClient

from satya_api.explain import diff_summary
from satya_shared_types import validator

from .test_demo_flow import DIT03, DT13, flow, rb  # noqa: F401


def _diff(ops: list[str], state: str = "compared", total: int = 5) -> dict[str, Any]:
    return {
        "expected": {"declarations": [{"no": n} for n in range(1, total + 1)]},
        "comparison": {"state": state},
        "ops": [
            {
                "op": op,
                "decl_no": None if op == "added" else i + 1,
                "sworn_no": None if op == "removed" else i + 1,
                "flag_id": None if op == "equal" else f"flg_{i}",
            }
            for i, op in enumerate(ops)
        ],
        "flags": [
            {"flag_id": "flg_1", "rule_id": "AFF-DECL-CHANGED"},
            {"flag_id": "flg_2", "rule_id": "AFF-DECL-MISSING"},
            {"flag_id": "flg_5", "rule_id": "AFF-DECL-ADDED"},
        ],
    }


def test_counts_for_known_differences_and_missing_declarations() -> None:
    got = diff_summary(_diff(["equal", "changed", "removed", "equal", "equal", "added"]))
    assert {k: v for k, v in got.items() if k != "differing"} == {
        "total": 5,
        "match": 3,
        "differ": 1,
        "missing_in_sworn": 1,
        "not_comparable": 0,
        "added_in_sworn": 1,
    }
    assert [(i["op"], i["decl_no"], i["sworn_no"]) for i in got["differing"]] == [
        ("changed", 2, 2),
        ("removed", 3, None),
        ("added", None, 6),
    ]
    assert got["differing"][0]["why"] == (
        "A declaration in the sworn copy is worded differently from the portal form."
    )
    assert got["differing"][1]["why"] == (
        "A declaration printed in the portal form does not appear in the sworn copy."
    )


def test_a_copy_that_was_not_compared_has_every_declaration_not_comparable() -> None:
    got = diff_summary(_diff([], state="not_compared", total=7))
    assert (got["total"], got["match"], got["differ"], got["not_comparable"]) == (7, 0, 0, 7)
    assert got["differing"] == []
    # even if ops were present, a not_compared copy reports nothing as matching
    assert diff_summary(_diff(["equal", "equal"], "not_compared", 2))["not_comparable"] == 2


def test_all_equal_and_empty_draft() -> None:
    got = diff_summary(_diff(["equal"] * 5))
    assert (got["match"], got["differ"], got["not_comparable"], got["differing"]) == (5, 0, 0, [])
    assert diff_summary({})["total"] == 0


def test_served_diff_has_summary_and_existing_fields_unchanged(flow: TestClient) -> None:  # noqa: F811
    diff = flow.get(f"/v1/cases/{DIT03}/affidavit-diff", headers=rb()).json()
    assert [e.message for e in validator("AffidavitDiff").iter_errors(diff)] == []
    summary = diff["summary"]
    kinds = [o["op"] for o in diff["ops"]]
    assert summary["differ"] == kinds.count("changed") >= 1
    assert summary["match"] == kinds.count("equal")
    assert summary["total"] == len(diff["expected"]["declarations"])
    assert (
        summary["match"]
        + summary["differ"]
        + summary["missing_in_sworn"]
        + summary["not_comparable"]
        == summary["total"]
    )
    assert {i["flag_id"] for i in summary["differing"]} <= {f["flag_id"] for f in diff["flags"]}
    assert all(i["why"] for i in summary["differing"])
    assert "ops" in diff and "comparison" in diff and "flags" in diff  # old keys still there


def test_scan_case_summary_is_not_comparable(flow: TestClient) -> None:  # noqa: F811
    diff = flow.get(f"/v1/cases/{DT13}/affidavit-diff", headers=rb()).json()
    assert diff["comparison"]["state"] == "not_compared"
    assert diff["summary"]["match"] == 0
    assert diff["summary"]["not_comparable"] == diff["summary"]["total"] > 0
