"""P-18 UDIN structure check on an audited statement of accounts (design B1 row 7, D4).

UDIN = 18 characters: YY + 6-digit ICAI membership no. + 6 letters + 4 digits [VERIFY: structure
from one non-AICTE audit; UDIN is not named in the APH]. Checks:
- UDIN-STRUCT: the structure, and YY ≥ the year the audited FY ended (a UDIN cannot predate the
  audit) and not more than `max_year_gap` years later;
- UDIN-MEMBER: characters 3-8 equal the membership number printed beside the auditor's name;
- UDIN-REUSE: one UDIN per FY: not already on another filing in the register.
There is no automated ICAI channel in the prototype, so the statement also gets a source_lookup
check that ends `source_unavailable` (P-18 acceptance; creates a manual task, RB-09). Without a
printed UDIN nothing is structure-checked: the lookup has no identifier and the label is the same.
"""

import re
from dataclasses import dataclass
from datetime import date

from satya_forensics.registry import Registry
from satya_forensics.stamp import Finding
from satya_forensics.textlayer import Box, Page

UDIN_LINE = re.compile(r"\bUDIN\s*[:.-]?\s*([0-9A-Z][0-9A-Z ]{8,30})", re.I)
UDIN_SHAPE = re.compile(r"^(\d{2})(\d{6})([A-Z]{6})(\d{4})$")
MEMBERSHIP = re.compile(r"\b(?:Membership\s+No|M\.\s*No)\.?\s*[:.-]?\s*(\d{4,7})\b", re.I)
YEAR_ENDED = re.compile(r"year\s+ended\s+(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})", re.I)
ICAI_SOURCE = {
    "adapter_id": "icai-udin",
    "mode": "none",
    "name": "ICAI UDIN (no automated channel)",
}


@dataclass
class AccountsText:
    page: int
    udin: str | None
    udin_box: Box | None
    membership_no: str | None
    membership_box: Box | None
    fy_end: date | None


def read_accounts(pages: list[Page]) -> AccountsText | None:
    for page in pages:
        udin_hits = page.find(UDIN_LINE)
        member_hits = page.find(MEMBERSHIP)
        year_hits = page.find(YEAR_ENDED)
        if not (udin_hits or member_hits):
            continue
        fy_end = None
        if year_hits:
            d, month, y = year_hits[0][0].groups()
            try:
                fy_end = date(int(y), _MONTHS[month[:3].lower()], int(d))
            except (KeyError, ValueError):
                fy_end = None
        return AccountsText(
            page=page.number,
            udin="".join(udin_hits[0][0].group(1).split()).upper() if udin_hits else None,
            udin_box=udin_hits[0][1] if udin_hits else None,
            membership_no=member_hits[0][0].group(1) if member_hits else None,
            membership_box=member_hits[0][1] if member_hits else None,
            fy_end=fy_end,
        )
    return None


_MONTHS = {
    m: i
    for i, m in enumerate(
        ("jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"),
        start=1,
    )
}


def fy_label(fy_end: date) -> str:
    return f"{fy_end.year - 1}-{str(fy_end.year)[2:]}"


def evaluate(
    acc: AccountsText | None, permanent_id: str, registry: Registry, max_year_gap: int
) -> list[Finding]:
    if acc is None or acc.udin is None:
        return []
    findings: list[Finding] = []
    shape = UDIN_SHAPE.match(acc.udin)
    findings.append(
        Finding(
            "UDIN-STRUCT",
            "udin:format",
            "format",
            shape is None,
            acc.page,
            acc.udin_box,
            f"{len(acc.udin)} characters",
            "18 characters: YY + 6-digit membership no. + 6 letters + 4 digits",
        )
    )
    if shape is None:
        return findings
    yy = int(shape.group(1))
    if acc.fy_end is not None:
        end = acc.fy_end.year % 100
        findings.append(
            Finding(
                "UDIN-STRUCT",
                "udin:year",
                "format",
                not (end <= yy <= end + max_year_gap),
                acc.page,
                acc.udin_box,
                f"UDIN year 20{yy:02d}",
                f"20{end:02d} to 20{end + max_year_gap:02d} (FY {fy_label(acc.fy_end)} ended "
                f"{acc.fy_end.isoformat()})",
            )
        )
    if acc.membership_no is not None:
        printed = acc.membership_no.zfill(6)
        findings.append(
            Finding(
                "UDIN-MEMBER",
                "udin:membership_no",
                "format",
                shape.group(2) != printed,
                acc.page,
                acc.udin_box,
                "membership no. inside the UDIN differs",
                "membership no. printed beside the auditor's name",
            )
        )
    fy = fy_label(acc.fy_end) if acc.fy_end else ""
    others = registry.udin_reused(acc.udin, permanent_id, fy)
    findings.append(
        Finding(
            "UDIN-REUSE",
            "udin:reuse",
            "format",
            bool(others),
            acc.page,
            acc.udin_box,
            "UDIN already on " + ", ".join(sorted({f"FY {o.year}" for o in others}))
            if others
            else "UDIN not seen on another filing",
            "one UDIN per FY, not reused",
        )
    )
    return findings


def source_check(acc: AccountsText | None, checked_at: str) -> dict[str, object]:
    return {
        "kind": "source_lookup",
        "outcome": "source_unavailable",
        "reason_code": "SRC_NO_CHANNEL" if acc and acc.udin else "SRC_NO_IDENTIFIER",
        "source": dict(ICAI_SOURCE),
        "checked_at": checked_at,
        "attempts": 0,
    }
