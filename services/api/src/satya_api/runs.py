"""Validation runs of a case and the comparison of two of them (T4).

A run is one `check.run` ledger entry; its detail keeps the flag records of that run. Pure
functions over ledger rows: no engine is started, nothing is written.
"""

import json
from typing import Any

from satya_api.explain import rule_of
from satya_api.ledger import LedgerRow

CHECKED = "check.run"
MAX_ITEMS = 500
CHANGE_ORDER = {"new": 0, "resolved": 1, "unchanged": 2}
COMPARED_FIELDS = ("rule_version", "severity", "label")


def runs_of(rows: list[LedgerRow], case_id: str) -> list[LedgerRow]:
    """The case's check.run entries that kept their flag records, oldest first."""
    out = []
    for row in rows:
        if (
            row.event_type == CHECKED
            and row.case_id == case_id
            and row.detail_json
            and "flags" in json.loads(row.detail_json)["detail"]
        ):
            out.append(row)
    return out


def run_flags(row: LedgerRow) -> list[dict[str, Any]]:
    flags: list[dict[str, Any]] = json.loads(row.detail_json or "{}")["detail"]["flags"]
    return flags


def describe(row: LedgerRow) -> dict[str, Any]:
    detail = json.loads(row.detail_json or "{}")["detail"]
    return {
        "ledger_seq": row.seq,
        "at": row.at.isoformat(),
        "trigger": detail.get("trigger"),
        "rule_pack": detail.get("rule_pack"),
        "flag_count": len(detail.get("flags", [])),
    }


def _key(flag: dict[str, Any]) -> tuple[str, str, str]:
    return (str(flag["doc_id"]), str(flag["rule_id"]), str(flag.get("check_ref")))


def _title(rule_id: str) -> str:
    rule = rule_of(rule_id)
    head = rule.description.strip().split(". ")[0].rstrip(".") if rule and rule.description else ""
    return head or rule_id


def diff_runs(old: list[dict[str, Any]], new: list[dict[str, Any]]) -> dict[str, Any]:
    """Findings that are new in `new`, resolved since `old`, or in both. Matched by (document,
    rule, check) because flag ids carry the rule version."""
    before = {_key(f): f for f in old}
    after = {_key(f): f for f in new}
    items = []
    for key in before.keys() | after.keys():
        flag = after.get(key) or before[key]
        change = "new" if key not in before else "resolved" if key not in after else "unchanged"
        changed = (
            [f for f in COMPARED_FIELDS if before[key].get(f) != after[key].get(f)]
            if change == "unchanged"
            else []
        )
        items.append(
            {
                "change": change,
                "rule_id": flag["rule_id"],
                "title": _title(str(flag["rule_id"])),
                "doc_id": flag["doc_id"],
                "page": flag.get("page"),
                "check_ref": flag.get("check_ref"),
                "flag_id": flag["flag_id"],
                "severity": flag.get("severity"),
                "label": flag.get("label"),
                "changed_fields": changed,
            }
        )
    items.sort(key=lambda i: (CHANGE_ORDER[i["change"]], i["doc_id"], i["rule_id"], i["check_ref"]))
    counts = {c: sum(1 for i in items if i["change"] == c) for c in CHANGE_ORDER}
    return {
        "new_findings": counts["new"],
        "resolved": counts["resolved"],
        "unchanged": counts["unchanged"],
        "items": items[:MAX_ITEMS],
        "truncated": len(items) > MAX_ITEMS,
    }
