"""Stamp page, notary block and signing order of a sworn Affidavit 2 (design B1 row 1, D1).

Rules (packages/rules/m6-signatures.yaml):
- STAMP-INSTRUMENT: the affidavit is on an e-stamp certificate (Annex-2.1(i)); physical paper or no
  stamp page cannot be checked online → manual review.
- STAMP-PARTY: the e-stamp's Second Party is the Council (executed copies print "AICTE NEW DELHI").
- STAMP-DUTY: stamp duty is at least Rs 100 (2.3.4b, Annex-2.1(i)).
- STAMP-REUSE: the certificate number is not already on another application or year in the
  register (within the synthetic corpus).
- NOTARY-EXPIRY: the notary's seal is valid on the notarisation date.
- STAMP-CHRONO: application ≤ stamp issue ≤ notarisation ≤ DSC ≤ upload, and no printed signature
  mark on the sworn copy is dated after the notarisation (design D1 review case).

Dates on the stamp certificate are SHCIL style ("21-Nov-2026 11:05 AM"); dates in the affidavit
body follow the template year (portal affidavit = MM/DD/YYYY, design D4), with the impossible-month
fallback of M5.
"""

import re
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from itertools import pairwise
from typing import Any

from satya_affidavit.ids import mask
from satya_affidavit.normalise import parse_date
from satya_forensics.registry import Registry
from satya_forensics.signatures import SigResult
from satya_forensics.textlayer import Box, Page

IST = timezone(timedelta(hours=5, minutes=30))
COUNCIL = re.compile(r"\bAICTE\b|ALL\s+INDIA\s+COUNCIL\s+FOR\s+TECHNICAL\s+EDUCATION", re.I)
MIN_DUTY_RUPEES = 100
FIELD = r"\s*:\s*(.+?)\s*$"
E_STAMP_FIELDS = {
    "certificate_no": re.compile(r"^Certificate\s+No\.?" + FIELD, re.I),
    "issued": re.compile(r"^Certificate\s+Issued\s+Date" + FIELD, re.I),
    "article": re.compile(r"^Description\s+of\s+Document" + FIELD, re.I),
    "second_party": re.compile(r"^Second\s+Party" + FIELD, re.I),
    "duty": re.compile(r"^Stamp\s+Duty\s+Amount\s*\(Rs\.?\)" + FIELD, re.I),
}
PHYSICAL_FIELDS = {
    "certificate_no": re.compile(r"^Serial\s+No\.?" + FIELD, re.I),
    "issued": re.compile(r"^Date\s+of\s+Sale" + FIELD, re.I),
    "article": re.compile(r"^Purpose" + FIELD, re.I),
    "duty": re.compile(r"^Denomination" + FIELD, re.I),
}
NOTARY_DATE = re.compile(r"before\s+me\s+on\s+([0-9]{1,2}[/.-][0-9]{1,2}[/.-][0-9]{4})", re.I)
NOTARY_EXPIRY = re.compile(
    r"(?:seal\s+)?valid\s+(?:till|upto|up\s+to)\s+([0-9]{1,2}[/.-][0-9]{1,2}[/.-][0-9]{4})", re.I
)
NOTARY_REG = re.compile(r"Reg(?:istration)?\.?\s*No\.?\s*([A-Z0-9][A-Z0-9/-]*)", re.I)


@dataclass
class StampInfo:
    page: int
    instrument: str  # e-stamp | physical
    certificate_no: str | None = None
    issued: date | None = None
    article: str | None = None
    second_party: str | None = None
    duty_rupees: int | None = None
    boxes: dict[str, Box] = field(default_factory=dict)


@dataclass
class NotaryInfo:
    page: int
    notarised: date | None
    seal_valid_till: date | None
    reg_no: str | None
    boxes: dict[str, Box] = field(default_factory=dict)


def _shcil_date(text: str) -> date | None:
    text = " ".join(text.split())
    for fmt in ("%d-%b-%Y %I:%M %p", "%d-%b-%Y"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


def _rupees(text: str) -> int | None:
    m = re.search(r"(\d[\d,]*)", text)
    return int(m.group(1).replace(",", "")) if m else None


def read_stamp(pages: list[Page]) -> StampInfo | None:
    """The stamp page in front of the affidavit (first two pages are searched)."""
    for page in pages[:2]:
        upper = page.text.upper()
        if "E-STAMP" in upper or "ESTAMP" in upper:
            instrument, patterns = "e-stamp", E_STAMP_FIELDS
        elif "NON-JUDICIAL" in upper or "NON JUDICIAL" in upper:
            instrument, patterns = "physical", PHYSICAL_FIELDS
        else:
            continue
        info = StampInfo(page=page.number, instrument=instrument)
        for name, pattern in patterns.items():
            for match, box in page.find(pattern):
                value = match.group(1)
                info.boxes[name] = box
                if name == "certificate_no":
                    info.certificate_no = (
                        "".join(value.split()) if instrument == "e-stamp" else value
                    )
                elif name == "issued":
                    info.issued = _shcil_date(value)
                elif name == "duty":
                    info.duty_rupees = _rupees(value)
                elif name == "article":
                    info.article = value
                elif name == "second_party":
                    info.second_party = value
                break
        return info
    return None


def read_notary(pages: list[Page], order: str) -> NotaryInfo | None:
    """The notary block (searched from the last page backwards)."""
    for page in reversed(pages):
        dates = page.find(NOTARY_DATE)
        if not dates:
            continue
        match, box = dates[-1]
        info = NotaryInfo(page.number, parse_date(match.group(1), order)[0], None, None)
        info.boxes["date"] = box
        expiry = page.find(NOTARY_EXPIRY)
        if expiry:
            info.seal_valid_till = parse_date(expiry[-1][0].group(1), order)[0]
            info.boxes["expiry"] = expiry[-1][1]
        reg = page.find(NOTARY_REG)
        if reg:
            info.reg_no = reg[-1][0].group(1)
        return info
    return None


def _ist_date(when: datetime | None) -> date | None:
    return None if when is None else when.astimezone(IST).date()


@dataclass
class Finding:
    """A rule outcome for the engine to turn into a check (and a flag when it fails)."""

    rule_id: str
    key: str
    kind: str
    failed: bool
    page: int | None
    box: Box | None
    extracted: Any
    expected: Any
    confidence: float = 0.95
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class AffidavitStampResult:
    findings: list[Finding]
    stamp: dict[str, Any] | None
    chronology: dict[str, Any]
    ocr_match: Finding | None = None  # OCR-read number found on another filing (O-23)


def evaluate(
    pages: list[Page],
    order: str,
    issuer: SigResult,
    application_date: date | None,
    uploaded_at: datetime | None,
    application_id: str,
    ay: str,
    registry: Registry,
) -> AffidavitStampResult:
    stamp = read_stamp(pages)
    notary = read_notary(pages, order)
    findings: list[Finding] = []

    def box(info: StampInfo | NotaryInfo | None, name: str) -> Box | None:
        return None if info is None else info.boxes.get(name)

    # STAMP-INSTRUMENT
    findings.append(
        Finding(
            "STAMP-INSTRUMENT",
            "stamp:instrument",
            "format",
            stamp is None or stamp.instrument != "e-stamp",
            stamp.page if stamp else None,
            box(stamp, "certificate_no"),
            stamp.instrument if stamp else None,
            "e-stamp certificate (Annex-2.1(i))",
        )
    )
    if stamp is not None and stamp.instrument == "e-stamp":
        party = stamp.second_party
        findings.append(
            Finding(
                "STAMP-PARTY",
                "stamp:second_party",
                "format",
                not (party and COUNCIL.search(party)),
                stamp.page,
                box(stamp, "second_party"),
                party,
                "AICTE NEW DELHI (the Council)",
            )
        )
    if stamp is not None and stamp.duty_rupees is not None:
        findings.append(
            Finding(
                "STAMP-DUTY",
                "stamp:duty",
                "format",
                stamp.duty_rupees < MIN_DUTY_RUPEES,
                stamp.page,
                box(stamp, "duty"),
                stamp.duty_rupees,
                MIN_DUTY_RUPEES,
            )
        )
    ocr_match: Finding | None = None
    if stamp is not None and stamp.certificate_no:
        others = registry.stamp_reused(stamp.certificate_no, application_id, ay)
        where = sorted({f"{o.application_id or 'another filing'} ({o.year})" for o in others})
        if pages[stamp.page - 1].from_ocr:
            # O-23: a number read by OCR is never a reuse finding, only a low-trust note.
            if others:
                ocr_match = Finding(
                    "STAMP-OCR-MATCH",
                    "stamp:certificate_no_ocr",
                    "format",
                    True,
                    stamp.page,
                    box(stamp, "certificate_no"),
                    mask(stamp.certificate_no),
                    "number read by OCR; confirm against the document",
                    confidence=0.5,
                    extra={"seen_on": where},
                )
        else:
            findings.append(
                Finding(
                    "STAMP-REUSE",
                    "stamp:certificate_no",
                    "format",
                    bool(others),
                    stamp.page,
                    box(stamp, "certificate_no"),
                    mask(stamp.certificate_no),
                    "certificate number not used on any other filing",
                    extra={"seen_on": where},
                )
            )
    # NOTARY-EXPIRY
    if notary is not None and notary.notarised and notary.seal_valid_till:
        findings.append(
            Finding(
                "NOTARY-EXPIRY",
                "notary:seal_expiry",
                "expiry",
                notary.seal_valid_till < notary.notarised,
                notary.page,
                box(notary, "expiry"),
                notary.seal_valid_till.isoformat(),
                f"on or after {notary.notarised.isoformat()}",
                extra={"valid_to": notary.seal_valid_till.isoformat(), "basis": "printed"},
            )
        )
    # STAMP-CHRONO: order and printed mark after notarisation
    image_mark = not issuer.has_byte_range and issuer.reason_code == "SIG_IMAGE_ONLY"
    dsc_date = _ist_date(issuer.signed_at) if issuer.reason_code != "SIG_NOT_DIGITAL" else None
    dsc_kind = None if dsc_date is None else ("image_mark" if image_mark else "signature")
    upload_date = _ist_date(uploaded_at)
    sequence = [
        ("application", application_date),
        ("stamp", stamp.issued if stamp else None),
        ("notarisation", notary.notarised if notary else None),
        ("DSC", dsc_date),
        ("upload", upload_date),
    ]
    known = [(name, d) for name, d in sequence if d is not None]
    broken = [
        f"{a} {da.isoformat()} > {b} {db.isoformat()}"
        for (a, da), (b, db) in pairwise(known)
        if da > db
    ]
    order_ok = None if len(known) < 2 else not broken
    findings.append(
        Finding(
            "STAMP-CHRONO",
            "chronology:order",
            "chronology",
            bool(broken),
            notary.page if notary else None,
            box(notary, "date"),
            "; ".join(broken) if broken else " ≤ ".join(f"{n} {d.isoformat()}" for n, d in known),
            "application ≤ stamp ≤ notarisation ≤ DSC ≤ upload",
            confidence=0.95,
        )
    )
    mark_after = None
    if image_mark and notary is not None and notary.notarised and dsc_date is not None:
        mark_after = dsc_date > notary.notarised
        findings.append(
            Finding(
                "STAMP-CHRONO",
                "chronology:mark_after_notary",
                "chronology",
                mark_after,
                issuer.page,
                None,
                f"printed mark dated {dsc_date.isoformat()}",
                f"no printed mark dated after notarisation {notary.notarised.isoformat()}",
                confidence=0.9,
                extra={"regions": issuer.regions},
            )
        )
    notary_ok = None
    if notary is not None and notary.notarised and notary.seal_valid_till:
        notary_ok = notary.seal_valid_till >= notary.notarised
    chronology = {
        "application_date": application_date.isoformat() if application_date else None,
        "stamp_date": stamp.issued.isoformat() if stamp and stamp.issued else None,
        "notary_date": notary.notarised.isoformat() if notary and notary.notarised else None,
        "dsc_date": dsc_date.isoformat() if dsc_date else None,
        "upload_date": upload_date.isoformat() if upload_date else None,
        "order_ok": order_ok,
        "notary_expiry": (
            notary.seal_valid_till.isoformat() if notary and notary.seal_valid_till else None
        ),
        "dsc_kind": dsc_kind,
        "mark_after_notary": mark_after,
        "notary_expiry_ok": notary_ok,
    }
    stamp_section = None
    if stamp is not None:
        stamp_section = {
            "instrument": stamp.instrument,
            "certificate_no": mask(stamp.certificate_no),
            "second_party": stamp.second_party,
            "duty": None if stamp.duty_rupees is None else stamp.duty_rupees * 100,
            "state": "verification_pending",  # set by the engine from the stamp findings
            "article": stamp.article,
            "issue_date": stamp.issued.isoformat() if stamp.issued else None,
            "page": stamp.page,
        }
    return AffidavitStampResult(findings, stamp_section, chronology, ocr_match)


def certificate_number(pages: list[Page]) -> str | None:
    """Only the stamp certificate number (to build the register of current cases)."""
    info = read_stamp(pages)
    return info.certificate_no if info else None
