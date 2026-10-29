"""Minimal source hub (Slice D): three adapters, all offline or simulated, on synthetic data.

Adapters
- `cca-offline-chain` (offline): the chain check M6 already ran against the TEST TRUST ANCHOR. Not
  CCA, not a live lookup; it is described here so the panel names the channel.
- `shcil-estamp-mock` (mock): looks the e-stamp certificate number up in a synthetic register made
  of the earlier filings plus every current case. No SHCIL connection exists.
- `icai-udin-mock` (mock): accepts a UDIN whose structure, year and membership number passed the
  M6 checks and that no other filing uses. No ICAI connection exists.
A document without a usable source ends `source_unavailable` and gets a manual task (RB-09).
Every response carries `mode: "mock"` (the workbench shows a Simulated source tag) and a
response hash for the ledger.
"""

from __future__ import annotations

import copy
import hashlib
import json
from typing import Any

from satya_forensics.labels import document_label
from satya_forensics.registry import Registry

SHCIL = {
    "adapter_id": "shcil-estamp-mock",
    "mode": "mock",
    "name": "SHCIL e-stamp lookup",
}
ICAI = {"adapter_id": "icai-udin-mock", "mode": "mock", "name": "ICAI UDIN lookup"}
# Every source the hub knows, for the Overview source line (name_key is a workbench message key).
SOURCES: tuple[dict[str, str], ...] = (
    {"adapter_id": "cca-offline-chain", "name_key": "cca_offline_chain", "mode": "offline"},
    {"adapter_id": SHCIL["adapter_id"], "name_key": "shcil_estamp", "mode": SHCIL["mode"]},
    {"adapter_id": ICAI["adapter_id"], "name_key": "icai_udin", "mode": ICAI["mode"]},
)
AFFIDAVIT_SLOT = "annex2.1(i) affidavit"
ACCOUNTS_SLOT = "annex2.1(vii) audited accounts"


def _response_sha(adapter: dict[str, str], request: dict[str, Any], outcome: str, code: str) -> str:
    body = json.dumps(
        {"adapter": adapter["adapter_id"], "request": request, "outcome": outcome, "code": code},
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(body.encode()).hexdigest()


def _check(
    adapter: dict[str, str], request: dict[str, Any], outcome: str, code: str, checked_at: str
) -> dict[str, Any]:
    return {
        "kind": "source_lookup",
        "outcome": outcome,
        "reason_code": code,
        "source": dict(adapter),
        "checked_at": checked_at,
        "response_sha256": _response_sha(adapter, request, outcome, code),
        "attempts": 1,
    }


def apply_hub(
    doc: dict[str, Any],
    slot: str,
    stamp_no: str | None,
    udin: str | None,
    registry: Registry,
    application_id: str,
    ay: str,
    checked_at: str,
    ocr_number: bool = False,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Returns (document verification with hub checks and the final label, source responses)."""
    verification = copy.deepcopy(doc)
    checks: list[dict[str, Any]] = verification["checks"]
    responses: list[dict[str, Any]] = []
    if slot == AFFIDAVIT_SLOT:
        if stamp_no is None:
            new = _check(
                SHCIL,
                {"certificate_no": None},
                "source_unavailable",
                "SRC_NO_IDENTIFIER",
                checked_at,
            )
        elif not ocr_number and registry.stamp_reused(stamp_no, application_id, ay):
            new = _check(
                SHCIL,
                {"certificate_no": stamp_no},
                "manual_review_required",
                "SRC_BOUND_TO_OTHER_FILING",
                checked_at,
            )
        else:
            new = _check(SHCIL, {"certificate_no": stamp_no}, "verified", "SRC_MATCH", checked_at)
        checks.append(new)
        responses.append(new)
    elif slot == ACCOUNTS_SLOT:
        structure_ok = udin is not None and not any(
            c["outcome"] in ("manual_review_required", "mismatch_detected")
            for c in checks
            if c["kind"] == "format"
        )
        if structure_ok:
            checks[:] = [c for c in checks if c["kind"] != "source_lookup"]
            new = _check(ICAI, {"udin_present": True}, "verified", "SRC_MATCH", checked_at)
            checks.append(new)
            responses.append(new)
    verification["label"] = document_label(checks)
    return verification, responses


ADAPTERS = {SHCIL["adapter_id"]: SHCIL, ICAI["adapter_id"]: ICAI}


def apply_stored(
    doc: dict[str, Any], slot: str, stored: list[dict[str, Any]], checked_at: str
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Replay (P-11): like `apply_hub`, but the source answers are the ones kept in the ledger.

    Nothing is looked up; a response whose adapter is unknown is ignored (and shows up as a
    difference to the original).
    """
    verification = copy.deepcopy(doc)
    checks: list[dict[str, Any]] = verification["checks"]
    responses: list[dict[str, Any]] = []
    for item in stored:
        adapter = ADAPTERS.get(item["adapter_id"])
        if adapter is None:
            continue
        if slot == ACCOUNTS_SLOT:
            checks[:] = [c for c in checks if c["kind"] != "source_lookup"]
        check = {
            "kind": "source_lookup",
            "outcome": item["outcome"],
            "reason_code": item["reason_code"],
            "source": dict(adapter),
            "checked_at": checked_at,
            "response_sha256": item["response_sha256"],
            "attempts": 1,
        }
        checks.append(check)
        responses.append(check)
    verification["label"] = document_label(checks)
    return verification, responses
