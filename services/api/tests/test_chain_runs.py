"""T4: audit chain verify, replay check (digest comparison) and run diff.

Synthetic data and a throwaway in-memory ledger only; nothing here touches demo data. The tamper
tests alter one ledger row of that throwaway store and show how the chain verdict changes.
"""

import dataclasses
import json
import re
from typing import Any

import pytest

from satya_api.replay import run_digest
from satya_api.runs import diff_runs

from .test_replay import DCE05, DIT03, PACK, Harness, h  # noqa: F401
from .test_workbench_api import auth, token

HEX64 = re.compile(r"[0-9a-f]{64}")


def au() -> dict[str, str]:
    return auth(token(roles=["AU"]))


def get(h: Harness, url: str, headers: dict[str, str] | None = None, **params: Any) -> Any:  # noqa: F811
    return h.client.get(url, params=params or None, headers=headers or auth(token()))


# ---- /v1/audit/verify ---------------------------------------------------------------------------
def test_verify_reports_intact_with_entry_count_and_writes_nothing(h: Harness) -> None:  # noqa: F811
    h.check(DIT03)
    h.check(DCE05)
    before = len(h.store.rows)
    for headers in (auth(token()), au()):
        body = get(h, "/v1/audit/verify", headers).json()
        assert body["status"] == "intact" and body["first_bad_entry"] is None
        assert body["entries"] == before and body["checked_at"]
    assert len(h.store.rows) == before


def test_tampering_one_ledger_row_breaks_the_chain_at_that_row(h: Harness) -> None:  # noqa: F811
    h.check(DIT03)
    h.check(DCE05)
    rows = h.store.rows
    assert len(rows) >= 4
    victim = 2  # index; the entry's seq is 3
    untouched = rows[victim]
    rows[victim] = dataclasses.replace(rows[victim], payload_sha256="0" * 64)
    body = get(h, "/v1/audit/verify").json()
    assert body["status"] == "broken"
    assert body["first_bad_entry"] == rows[victim].seq == 3
    assert body["entries"] == len(rows)
    # the same row, restored, reads intact again: the verdict is recomputed on every call
    rows[victim] = untouched
    assert get(h, "/v1/audit/verify").json()["status"] == "intact"


def test_verify_names_the_earliest_bad_entry_and_catches_a_changed_detail(h: Harness) -> None:  # noqa: F811
    h.check(DIT03)
    h.check(DCE05)
    rows = h.store.rows
    original = list(rows)
    rows[-1] = dataclasses.replace(rows[-1], hash="f" * 64)
    rows[1] = dataclasses.replace(rows[1], detail_json=(rows[1].detail_json or "") + " ")
    assert get(h, "/v1/audit/verify").json()["first_bad_entry"] == rows[1].seq
    rows[:] = original
    assert get(h, "/v1/audit/verify").json()["status"] == "intact"


def test_verify_access_control(h: Harness) -> None:  # noqa: F811
    assert h.client.get("/v1/audit/verify").status_code == 401
    assert get(h, "/v1/audit/verify", auth(token(roles=["INS"]))).status_code == 403
    assert h.client.post("/v1/audit/verify", headers=auth(token())).status_code == 405
    # the numbered route keeps working next to it
    h.check(DCE05)
    assert get(h, "/v1/audit/1").status_code == 200


# ---- /v1/cases/{id}/replay-check ----------------------------------------------------------------
def test_replay_check_reproduces_identically_and_is_deterministic(h: Harness) -> None:  # noqa: F811
    h.check(DIT03)
    before = len(h.store.rows)
    url = f"/v1/cases/{DIT03}/replay-check"
    body = get(h, url).json()
    assert body["reproduced_identically"] is True and body["reasons"] == []
    assert body["ruleset_id"] == PACK and HEX64.fullmatch(body["ruleset_hash"])
    assert (
        HEX64.fullmatch(body["digest_original"])
        and body["digest_original"] == body["digest_replayed"]
    )
    assert body["as_of"] and body["advisory"] is True and body["regulatory_effect"] == "none"
    assert get(h, url).json() == body
    assert len(h.store.rows) == before  # read-only, unlike /replay


def test_replay_check_without_a_run_or_with_a_changed_document(h: Harness) -> None:  # noqa: F811
    body = get(h, f"/v1/cases/{DCE05}/replay-check").json()
    assert body["reproduced_identically"] is False and body["digest_original"] is None
    assert body["reasons"][0]["code"] == "NO_ORIGINAL_RECORD"
    h.check(DIT03)
    pdf = h.cases_dir / "dit03-2026-27" / "affidavit-sworn.pdf"
    pdf.write_bytes(pdf.read_bytes() + b"\n%changed")
    body = get(h, f"/v1/cases/{DIT03}/replay-check").json()
    assert body["reproduced_identically"] is False and body["digest_replayed"] is None
    assert body["reasons"][0]["code"] == "HASH_MISMATCH"


def test_replay_check_access_control(h: Harness) -> None:  # noqa: F811
    h.check(DCE05)
    url = f"/v1/cases/{DCE05}/replay-check"
    assert h.client.get(url).status_code == 401
    assert get(h, url, auth(token(roles=["INS"]))).status_code == 403
    assert get(h, url, auth(token(groups=["/regions/northern"]))).status_code == 403
    assert get(h, url, au()).status_code == 200
    assert get(h, "/v1/cases/not-a-case/replay-check").status_code == 404


def test_digest_depends_on_flags_and_labels_only() -> None:
    flag = {"flag_id": "flg_1", "doc_id": "doc_1", "rule_id": "AFF-HEADER", "severity": "warning"}
    base = run_digest([flag], {"doc_1": "verified"})
    assert base == run_digest([dict(reversed(flag.items()))], {"doc_1": "verified"})
    assert base != run_digest([{**flag, "severity": "critical"}], {"doc_1": "verified"})
    assert base != run_digest([flag], {"doc_1": "mismatch_detected"})
    assert base != run_digest([], {"doc_1": "verified"})


# ---- /v1/cases/{id}/run-diff --------------------------------------------------------------------
def _second_run(h: Harness, case_id: str, drop: int = 1, add: bool = True) -> list[dict[str, Any]]:  # noqa: F811
    """Append a later check.run: the first run minus `drop` flags, plus one new flag."""
    first = next(r for r in h.store.rows if r.event_type == "check.run" and r.case_id == case_id)
    detail = json.loads(first.detail_json or "")["detail"]
    flags = detail["flags"][drop:]
    if add:
        flags = [
            *flags,
            {
                **detail["flags"][0],
                "rule_id": "UDIN-REUSE",
                "check_ref": "m6:UDIN-REUSE:x",
                "flag_id": "flg_new",
            },
        ]
    detail = {**detail, "trigger": "upload", "flags": flags}
    flow = h.client.app.state.workflow  # type: ignore[attr-defined]
    h.client.portal.call(flow.store.append, "check.run", case_id, "tester", detail)  # type: ignore[union-attr]
    return list(detail["flags"])


def test_run_diff_counts_new_resolved_unchanged(h: Harness) -> None:  # noqa: F811
    h.check(DIT03)
    url = f"/v1/cases/{DIT03}/run-diff"
    single = get(h, url).json()
    assert single["comparable"] is False and single["items"] == [] and single["from_run"] is None
    _second_run(h, DIT03)
    body = get(h, url).json()
    assert body["comparable"] is True
    assert (body["new_findings"], body["resolved"], body["unchanged"]) == (1, 1, 6)
    changes = [i["change"] for i in body["items"]]
    assert changes == ["new"] + ["resolved"] + ["unchanged"] * 6
    new = body["items"][0]
    assert new["rule_id"] == "UDIN-REUSE" and new["title"] and new["changed_fields"] == []
    assert body["from_run"]["trigger"] == "seed" and body["to_run"]["trigger"] == "upload"
    assert body["from_run"]["ledger_seq"] < body["to_run"]["ledger_seq"]
    # explicit run numbers give the same answer; reversed or unknown ones are handled
    seqs = (body["from_run"]["ledger_seq"], body["to_run"]["ledger_seq"])
    assert get(h, url, from_seq=seqs[0], to_seq=seqs[1]).json() == body
    reversed_ = get(h, url, from_seq=seqs[1], to_seq=seqs[0]).json()
    assert reversed_["comparable"] is False
    assert get(h, url, from_seq=99999).status_code == 404
    assert get(h, url, from_seq="x").status_code == 400


def test_run_diff_marks_a_changed_severity_without_a_new_counter() -> None:
    old = [
        {
            "flag_id": "a",
            "doc_id": "d",
            "rule_id": "AFF-HEADER",
            "check_ref": "c",
            "severity": "warning",
        }
    ]
    new = [{**old[0], "severity": "critical"}]
    got = diff_runs(old, new)
    assert (got["new_findings"], got["resolved"], got["unchanged"]) == (0, 0, 1)
    assert got["items"][0]["changed_fields"] == ["severity"]
    assert diff_runs([], []) == {
        "new_findings": 0,
        "resolved": 0,
        "unchanged": 0,
        "items": [],
        "truncated": False,
    }


def test_run_diff_access_control_and_scope(h: Harness) -> None:  # noqa: F811
    h.check(DCE05)
    url = f"/v1/cases/{DCE05}/run-diff"
    assert h.client.get(url).status_code == 401
    assert get(h, url, auth(token(roles=["INS"]))).status_code == 403
    assert get(h, url, auth(token(groups=["/regions/northern"]))).status_code == 403
    assert get(h, url, au()).status_code == 200
    # a run of another case is not reachable through this case
    h.check(DIT03)
    other = next(r.seq for r in h.store.rows if r.case_id == DIT03 and r.event_type == "check.run")
    assert get(h, url, from_seq=other).status_code == 404


@pytest.mark.parametrize("path", ["replay-check", "run-diff"])
def test_new_routes_reject_bad_case_ids(h: Harness, path: str) -> None:  # noqa: F811
    assert get(h, f"/v1/cases/..%2F..%2Fetc/{path}").status_code == 404
