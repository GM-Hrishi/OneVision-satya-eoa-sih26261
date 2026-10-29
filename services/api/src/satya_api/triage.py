# ruff: noqa: E501
"""Risk band, "why" sentences, status and alerts for the demo workflow (Slice D). Pure functions.

Everything here is deterministic and derived from stored results: no model, no score.

Risk band rule (decision D-3, documented in docs/progress/DECISIONS-SLICE-D.md):
  HIGH    any flag of severity `critical`, or any document labelled `mismatch_detected`;
  MEDIUM  else any flag of severity `warning`, or any document `manual_review_required` / `expired`;
  LOW     else.
The band uses the stored flags whether or not an official has disposed of them: it orders review
only, it is not a finding, and the institution never sees it. The stage-1 private pre-check is
never an input (Portal D-1, MASTER #19).
"""

from __future__ import annotations

import hashlib
from datetime import date, timedelta
from typing import Any

SEVERITY_RANK = {"critical": 0, "warning": 1, "info": 2}
BAND_RANK = {"high": 0, "medium": 1, "low": 2}
STATUSES = ("not_started", "in_review", "waiting_on_institution", "referred", "all_flags_decided")
SOON_DAYS = 30

# Fixed "why" sentences, one per rule. Placeholders come from the flag's own values only.
WHY: dict[str, str] = {
    "AFF-CAT-LINE": "The numbered category line of the portal draft is missing from the sworn copy.",
    "AFF-DECL-MISSING": "A declaration in the portal draft does not appear in the sworn copy.",
    "AFF-DECL-CHANGED": "A declaration in the sworn copy has different wording from the portal draft.",
    "AFF-DECL-ADDED": "The sworn copy has a declaration that the portal draft does not have.",
    "AFF-HEADER": "The header of the sworn copy differs from the portal draft.",
    "LAND-AREA-RECON": "The sworn land area is {extracted} {unit} but the application report has {expected} {unit}.",
    "LAND-ROW-RECON": "A land row in the sworn copy differs from the application report.",
    "ROOM-RECON": "A room value in the sworn copy differs from the application report.",
    "ROOM-ID-DUP": "Room ID {extracted} appears in more than one room table.",
    "SIG-DIGEST": "The document content no longer matches its digital signature.",
    "SIG-MODIFIED": "The document was changed after it was signed.",
    "SIG-REVOKED": "The signer's certificate was revoked before the signing time.",
    "SIG-CERT-EXPIRED": "The signer's certificate had expired at the time of signing.",
    "SIG-UNTRUSTED": "The signer's certificate does not chain to the trust anchor.",
    "SIG-IMAGE": "The 'digitally signed' mark is printed text or an image, not a real signature.",
    "SIG-SIGNER": "The name on the signing certificate does not match the signatory in the application.",
    "SIG-REVOCATION": "The revocation list could not be reached, so revocation was not checked.",
    "SIG-UPLOADER-MISSING": "The uploaded file carries no digital signature from the institution.",
    "STAMP-CHRONO": "The dates of stamp, notarisation or signing are not in the expected order.",
    "STAMP-PARTY": "The e-stamp names a second party other than the one the template requires.",
    "STAMP-DUTY": "The stamp duty paid is lower than the amount the template requires.",
    "STAMP-INSTRUMENT": "The stamp is on physical paper, so no e-stamp number can be looked up.",
    "STAMP-REUSE": "This e-stamp certificate number was already used on another filing.",
    "STAMP-OCR-MATCH": "Stamp number read by OCR matches another case. Needs human verification.",
    "NOTARY-EXPIRY": "The notary's seal had expired on the date of notarisation.",
    "UDIN-STRUCT": "The UDIN does not have the expected structure or year.",
    "UDIN-MEMBER": "The membership number inside the UDIN differs from the one printed on the statement.",
    "UDIN-REUSE": "This UDIN already appears on another filing.",
}
DEFAULT_WHY = "This finding comes from a rule that cites the APH clause shown. Review the evidence."


def _fmt(value: Any) -> str:
    if value is None:
        return "nothing"
    if isinstance(value, float):
        return f"{value:g}"
    text = str(value)
    return text if len(text) <= 60 else text[:57] + "..."


def why_sentence(flag: dict[str, Any]) -> str:
    template = WHY.get(str(flag.get("rule_id")), DEFAULT_WHY)
    return template.format(
        extracted=_fmt(flag.get("extracted_value")),
        expected=_fmt(flag.get("expected_value")),
        unit=flag.get("value_unit") or "",
    ).replace("  ", " ")


def flag_order(flag: dict[str, Any]) -> tuple[int, str, str]:
    return (
        SEVERITY_RANK.get(str(flag.get("severity")), 3),
        str(flag.get("rule_id")),
        str(flag.get("flag_id")),
    )


def risk_band(flags: list[dict[str, Any]], labels: list[str]) -> str:
    if any(f.get("severity") == "critical" for f in flags) or "mismatch_detected" in labels:
        return "high"
    if any(f.get("severity") == "warning" for f in flags) or any(
        label in ("manual_review_required", "expired") for label in labels
    ):
        return "medium"
    return "low"


def top_reasons(flags: list[dict[str, Any]], limit: int = 3) -> list[dict[str, Any]]:
    out, seen = [], set()
    for flag in sorted(flags, key=flag_order):
        if flag["rule_id"] in seen:
            continue
        seen.add(flag["rule_id"])
        out.append(
            {
                "flag_id": flag["flag_id"],
                "rule_id": flag["rule_id"],
                "aph_clause": flag.get("aph_clause"),
                "short_text": why_sentence(flag),
            }
        )
    return out[:limit]


def case_status(flags: list[dict[str, Any]], decisions: dict[str, str]) -> str:
    """Case progress, derived from the latest decision on each flag (`decisions`: flag_id -> action).

    waiting_on_institution  a flag's latest decision is escalate_clarify (still open);
    referred                else a flag's latest decision is escalate_refer (still open);
    all_flags_decided       else every flag has a decision (also a case without flags);
    in_review               else some flags have a decision;
    not_started             else no flag has a decision.
    The status describes the officials' work only. It is advisory and has no regulatory effect.
    """
    latest = [decisions.get(f["flag_id"]) for f in flags]
    if "escalate_clarify" in latest:
        return "waiting_on_institution"
    if "escalate_refer" in latest:
        return "referred"
    done = sum(1 for action in latest if action)
    if done == len(flags):
        return "all_flags_decided"
    return "in_review" if done else "not_started"


SEVERITY_BY_SUBTYPE = {
    "new_high_band": "critical",
    "certificate_expired": "warning",
    "source_unavailable_task": "warning",
    "expiring_soon": "info",
}


def alerts_for(
    case: dict[str, Any], view: dict[str, Any], today: date, at: str = ""
) -> list[dict[str, Any]]:
    """Alerts derived from stored data (never typed in): expiry dates, High band, manual tasks.

    Each alert carries a severity (critical, warning, info: shown as High, Medium, Low), the time it
    was raised (`created_at`, the case's latest check run), the document and its label, the APH
    clause and flag when a rule is behind it, and `source` when a source answer is involved.
    """
    base = {"case_id": case["case_id"], "application_id": case["application_id"]}
    docs = {d["doc_id"]: d for d in view["documents"]}
    out: list[dict[str, Any]] = []

    def add(
        type_: str,
        subtype: str,
        text: str,
        doc: dict[str, Any] | None = None,
        flag: dict[str, Any] | None = None,
    ) -> None:
        source = None
        if doc is not None:
            mocked = [
                c["source"]["mode"]
                for c in doc["checks"]
                if c.get("source", {}).get("mode") == "mock"
            ]
            source = {"mode": "mock"} if mocked else None
        out.append(
            {
                **base,
                "type": type_,
                "subtype": subtype,
                "severity": SEVERITY_BY_SUBTYPE[subtype],
                "text": text,
                "created_at": at or view["checked_at"],
                "doc_id": doc["doc_id"] if doc else None,
                "label": doc["label"] if doc else None,
                "flag_id": flag["flag_id"] if flag else None,
                "aph_clause": flag.get("aph_clause") if flag else None,
                "source": source,
                "alert_key": hashlib.sha256(
                    f"{case['case_id']}|{subtype}|{doc['doc_id'] if doc else ''}".encode()
                ).hexdigest()[:12],
            }
        )

    if view["risk"]["band"] == "high":
        top = min(view["flags"], key=flag_order) if view["flags"] else None
        add(
            "suspected_anomaly",
            "new_high_band",
            "High band case. Review first. The band orders review only.",
            docs.get(top["doc_id"]) if top else None,
            top,
        )
    for doc in view["documents"]:
        for check in doc["checks"]:
            valid_to = check.get("valid_to")
            if valid_to:
                left = date.fromisoformat(valid_to) - today
                if left < timedelta(0):
                    add(
                        "expired",
                        "certificate_expired",
                        f"{doc['title']}: certificate or seal ended on {valid_to}.",
                        doc,
                    )
                elif left <= timedelta(days=SOON_DAYS):
                    add(
                        "expired",
                        "expiring_soon",
                        f"{doc['title']}: certificate or seal ends on {valid_to}.",
                        doc,
                    )
        if doc["label"] == "expired":
            add(
                "expired",
                "certificate_expired",
                f"{doc['title']}: signing certificate had expired at signing.",
                doc,
            )
        if doc["manual_task"]:
            read = doc.get("read") or {}
            add(
                "pending_source",
                "source_unavailable_task",
                f"{doc['title']}: {read['why']} Manual task open."
                if read.get("reason_code") and read.get("why")
                else f"{doc['title']}: no source for this document. Manual verification task open.",
                doc,
            )
    return out
