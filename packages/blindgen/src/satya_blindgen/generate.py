"""Blind generator: applications with random layouts, values and combinations of anomalies.

Independent of the project's own synthetic generators: it imports none of their case definitions or
expected-result tables. It reads only what a portal would hand any tool (the affidavit template
file and the test trust material) and the low-level PDF signing helpers. Document text, layout,
dates, ids and every planted anomaly are decided here, from the seed. The ground truth (which rule
should fire on which document, and the expected document label) is written to a sealed
`manifest.json` before any evaluation; the evaluator reads it only after the engine has run.

Anomalies this generator can plant (rule ids are those of packages/rules): see ANOMALIES.
"""

import hashlib
import io
import json
import math
import random
import re
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import yaml
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen.canvas import Canvas

import satya_forensics.pki as pki
import satya_forensics.synth.signing as signing
from satya_affidavit.paths import templates_dir

IST = timezone(timedelta(hours=5, minutes=30))
STAMP_FILE, AFF_FILE, ACC_FILE = (
    "affidavit-sworn.pdf",
    "affidavit-sworn.pdf",
    "audited-accounts.pdf",
)
AFF_SLOT, ACC_SLOT = "annex2.1(i) affidavit", "annex2.1(vii) audited accounts"
FONTS = (
    ("Helvetica", "Helvetica-Bold"),
    ("Times-Roman", "Times-Bold"),
    ("Courier", "Courier-Bold"),
)
# anomaly -> (rule ids that should fire, document it lives on)
ANOMALIES: dict[str, tuple[tuple[str, ...], str]] = {
    "decl_missing": (("AFF-DECL-MISSING",), "affidavit"),
    "decl_changed": (("AFF-DECL-CHANGED",), "affidavit"),
    "decl_added": (("AFF-DECL-ADDED",), "affidavit"),
    "header_aid": (("AFF-HEADER",), "affidavit"),
    "stamp_duty": (("STAMP-DUTY",), "affidavit"),
    "stamp_party": (("STAMP-PARTY",), "affidavit"),
    "chrono": (("STAMP-CHRONO",), "affidavit"),
    "notary_expired": (("NOTARY-EXPIRY",), "affidavit"),
    "sig_image": (("SIG-IMAGE",), "affidavit"),
    "sig_untrusted": (("SIG-UNTRUSTED",), "affidavit"),
    "sig_modified": (("SIG-MODIFIED",), "affidavit"),
    "sig_signer": (("SIG-SIGNER",), "affidavit"),
    "udin_struct": (("UDIN-STRUCT",), "accounts"),
    "udin_member": (("UDIN-MEMBER",), "accounts"),
}
WORDS = ("approved", "regular", "valid", "prescribed", "uploaded", "true", "digital", "campus")
STATES = (("Tamil Nadu", "Southern"), ("Karnataka", "Southern"), ("Maharashtra", "Western"))
SURNAMES = ("Rao", "Iyer", "Menon", "Patil", "Kulkarni", "Naidu", "Shetty", "Bose")


@dataclass
class App:
    index: int
    seed: int
    rng: random.Random
    anomalies: list[str] = field(default_factory=list)

    @property
    def slug(self) -> str:
        return f"b{self.seed}-{self.index:04d}"


def _ulid_like(rng: random.Random, prefix: str) -> str:
    alphabet = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
    return prefix + "".join(rng.choice(alphabet) for _ in range(26))


def _pick_anomalies(rng: random.Random, clean_share: float) -> list[str]:
    if rng.random() < clean_share:
        return []
    count = rng.choices([1, 2, 3], weights=[6, 3, 1])[0]
    chosen: list[str] = []
    for name in rng.sample(list(ANOMALIES), len(ANOMALIES)):
        # one signature problem per file; one UDIN problem per statement
        if name.startswith("sig_") and any(c.startswith("sig_") for c in chosen):
            continue
        if name.startswith("udin_") and any(c.startswith("udin_") for c in chosen):
            continue
        chosen.append(name)
        if len(chosen) == count:
            break
    return chosen


def _template() -> dict[str, Any]:
    path = templates_dir() / "affidavit-2" / "aff2-portal-2024-27.yaml"
    return yaml.safe_load(path.read_text("utf-8"))  # type: ignore[no-any-return]


def _ay_long(ay: str) -> str:
    start = int(ay[:4])
    return f"{start}-{start + 1}"


def _declaration_lines(
    template: dict[str, Any], values: dict[str, str], rng: random.Random
) -> list[dict[str, Any]]:
    """Declarations as printed: text with option groups kept as (choices, chosen)."""
    out = []
    for decl in template["declarations"]:
        text = " ".join(str(decl["text"]).split())
        text = text.replace("{ay_long}", values["ay_long"]).replace("{trust_name}", values["trust"])
        text = text.replace("{institution_name}", values["institution"])
        out.append(
            {
                "block": decl["block"],
                "number": decl["number"],
                "text": text,
                "bullets": list(decl.get("bullets", [])),
            }
        )
    return out


GROUP = re.compile(r"\[\[(\w+):\s*([^\]]+)\]\]")


class _Page:
    """Minimal flowing text writer with its own random look."""

    def __init__(self, rng: random.Random) -> None:
        self.rng = rng
        self.font, self.bold = rng.choice(FONTS)
        self.size = rng.choice((9.5, 10, 10.5, 11))
        self.lead = self.size * rng.choice((1.3, 1.4, 1.55))
        self.left = rng.choice((54.0, 62.0, 72.0))
        self.right = A4[0] - rng.choice((54.0, 62.0, 72.0))
        self.top = A4[1] - rng.choice((56.0, 66.0))
        self.bottom = 60.0
        self.pages: list[list[tuple[Any, ...]]] = [[]]
        self.y = self.top

    @property
    def ops(self) -> list[tuple[Any, ...]]:
        return self.pages[-1]

    def ensure(self, height: float) -> None:
        if self.y - height < self.bottom:
            self.pages.append([])
            self.y = self.top

    def text(self, x: float, s: str, bold: bool = False, size: float | None = None) -> None:
        self.ops.append(("text", x, self.y, s, self.bold if bold else self.font, size or self.size))

    def line(self, s: str, bold: bool = False, x: float | None = None) -> None:
        self.ensure(self.lead)
        self.y -= self.lead
        self.text(x if x is not None else self.left, s, bold)

    def wrapped(self, s: str, indent: float = 0.0, label: str | None = None) -> None:
        """Wrap `s`; option groups [[g: a|b]] print as 'a / b' with the unchosen struck out."""
        tokens: list[tuple[str, bool]] = []
        pos = 0
        for m in GROUP.finditer(s):
            tokens += [(w, False) for w in s[pos : m.start()].split()]
            choices = [c.strip() for c in m.group(2).split("|")]
            keep = self.rng.randrange(len(choices))
            for i, c in enumerate(choices):
                tokens.append((c, i != keep))
                if i < len(choices) - 1:
                    tokens.append(("/", True))
            pos = m.end()
        tokens += [(w, False) for w in s[pos:].split()]
        x0 = self.left + indent
        width = self.right - x0
        cur: list[tuple[str, bool]] = []
        used = 0.0
        first = True
        space = stringWidth(" ", self.font, self.size)

        def flush() -> None:
            nonlocal first
            self.ensure(self.lead)
            self.y -= self.lead
            x = x0
            if first and label:
                self.text(self.left, label)
            first = False
            for word, struck in cur:
                w = stringWidth(word, self.font, self.size)
                self.text(x, word)
                if struck:
                    self.ops.append(("strike", x, self.y + self.size * 0.32, x + w))
                x += w + space

        for word, struck in tokens:
            w = stringWidth(word, self.font, self.size)
            if cur and used + w > width:
                flush()
                cur, used = [], 0.0
            cur.append((word, struck))
            used += w + space
        if cur:
            flush()

    def gap(self, factor: float = 0.6) -> None:
        self.y -= self.lead * factor

    def footer_pages(self) -> int:
        return len(self.pages)

    def render(self, title: str) -> bytes:
        buf = io.BytesIO()
        c = Canvas(buf, pagesize=A4, invariant=True, pageCompression=0)
        c.setTitle(title)
        c.setAuthor("SATYA-EoA blind generator (synthetic)")
        c.setCreator("satya_blindgen")
        for number, ops in enumerate(self.pages, start=1):
            for op in ops:
                if op[0] == "text":
                    c.setFont(op[4], op[5])
                    c.drawString(op[1], op[2], op[3])
                elif op[0] == "strike":
                    c.setLineWidth(0.7)
                    c.line(op[1], op[2], op[3], op[2])
                elif op[0] == "rect":
                    c.setLineWidth(0.6)
                    c.rect(op[1], op[2], op[3], op[4], stroke=1, fill=0)
            c.setFont(self.font, 7.5)
            c.drawString(self.left, 28, "SYNTHETIC BLIND-SET DOCUMENT. Not a real affidavit.")
            c.drawRightString(self.right, 28, f"Page {number} of {len(self.pages)}")
            c.showPage()
        c.save()
        return buf.getvalue()


def _mutate(text: str, rng: random.Random) -> str:
    """Change the meaning of a declaration: swap one content word for a different one."""
    words = text.split()
    candidates = [i for i, w in enumerate(words) if len(w) > 4 and w.isalpha()]
    i = rng.choice(candidates)
    words[i] = rng.choice([w for w in WORDS if w != words[i].lower()])
    if rng.random() < 0.5:
        words.insert(i, "not")
    return " ".join(words)


def _snapshot(app: App, v: dict[str, Any]) -> dict[str, Any]:
    rng = app.rng
    deeds = []
    remaining = v["land_acre"]
    for k in range(v["deed_count"]):
        area = (
            round(remaining / (v["deed_count"] - k), 2)
            if k < v["deed_count"] - 1
            else round(remaining, 2)
        )
        remaining = round(remaining - area, 2)
        deeds.append(
            {
                "holder": v["trust"],
                "document_no": f"BL-DEED-{rng.randint(1000, 9999)}",
                "registration_date": (
                    date(2012, 1, 1) + timedelta(days=rng.randint(0, 3000))
                ).isoformat(),
                "plot_no": f"{rng.randint(1, 400)}/{rng.randint(1, 9)}",
                "village_district": f"Blind Village {rng.randint(1, 99)}, Blind District {rng.randint(1, 30)}",
                "area_acre": area,
            }
        )
    room_types = {
        "administrative": ["Principal Office", "Board Room", "Staff Room", "Accounts Office"],
        "amenities": ["Boys Common Room", "Girls Common Room", "Canteen"],
        "instructional": ["Class Room", "Tutorial Room", "Laboratory", "Workshop", "Drawing Hall"],
        "instructional_common": ["Library and Reading Room", "Seminar Hall", "Computer Centre"],
    }
    rooms: dict[str, list[dict[str, Any]]] = {}
    for block, kinds in room_types.items():
        n = rng.randint(2, len(kinds))
        prefix = {
            "administrative": "A",
            "amenities": "M",
            "instructional": "I",
            "instructional_common": "C",
        }[block]
        rooms[block] = [
            {
                "room_id": f"{prefix}-{rng.randint(1, 4)}{k:02d}",
                "room_type": kinds[k % len(kinds)],
                "carpet_area_m2": float(rng.choice((24, 30, 33, 40, 66, 75, 132, 200))),
                "flooring": "Ready",
                "walls_painting": "Ready",
                "electrification": "Ready",
            }
            for k in range(n)
        ]
    return {
        "ay": v["ay"],
        "captured_at": f"{v['app_date'].isoformat()}T11:05:00+05:30",
        "basic": {
            "application_id": v["aid"],
            "permanent_id": v["pid"],
            "institution_type": "Private-Self Financing",
            "status": "Submitted",
            "application_date": v["app_date"].isoformat(),
            "submission_date": (v["app_date"] + timedelta(days=4)).isoformat(),
            "regional_office": v["region"],
            "overall_deficiency": "no",
        },
        "trust": {"name": v["trust"], "registration_ref": f"BLIND-TRUST-{rng.randint(1000, 9999)}"},
        "authorised_signatory": {"name": v["signatory"], "designation": "chairman"},
        "courses": [
            {
                "programme": "Engineering and Technology",
                "level": "UG",
                "course": "Mechanical Engineering",
                "intake_approved": [
                    {"ay": "2024-25", "intake": 60},
                    {"ay": "2025-26", "intake": 60},
                ],
                "intake_applied": 60,
            }
        ],
        "land": {
            "total_area": v["land_acre"],
            "unit": "acre",
            "pieces": v["deed_count"],
            "max_distance_km": 0.5,
            "coordinates": {
                "lat": {"deg": 12, "min": 30, "sec": 0, "hemisphere": "N"},
                "lon": {"deg": 80, "min": 10, "sec": 0, "hemisphere": "E"},
            },
            "deeds": deeds,
        },
        "buildings": [
            {
                "block": "Block A",
                "sanctioned_area_m2": 8000,
                "constructed_area_m2": 8000,
                "approving_authority": "Blind Local Planning Authority",
                "approval_date": "2011-02-01",
            }
        ],
        "rooms": rooms,
        "declaration": {
            "items": {k: True for k in "abcdef"},
            "category_list": ["EoA Only"],
        },
        "deficiency_report": {
            "template_year": v["ay"],
            "sections": [{"section": "Principal eligibility", "deficiency": "no"}],
            "overall": "no",
            "principal_eligibility": "yes",
        },
    }


def _mdy(d: date) -> str:
    return f"{d.month:02d}/{d.day:02d}/{d.year}"


def _wrap_cell(text: str, width: float, font: str, size: float) -> list[str]:
    lines: list[str] = []
    cur = ""
    for word in text.split():
        trial = f"{cur} {word}".strip()
        if cur and stringWidth(trial, font, size) > width - 4:
            lines.append(cur)
            cur = word
        else:
            cur = trial
    return [*lines, cur] if cur else lines or [""]


def _table(
    p: _Page, caption: str, columns: list[str], rows: list[list[str]], total: str | None
) -> None:
    """A bordered grid table with wrapped cells, as portal affidavits print them."""
    p.gap(0.8)
    p.line(caption, bold=True)
    span = (p.right - p.left) / len(columns)
    small = p.size - 1.5
    for r, row in enumerate([columns, *rows]):
        face = p.bold if r == 0 else p.font
        cells = [_wrap_cell(c, span, face, small) for c in row]
        height = max(len(c) for c in cells) * (small + 2) + 4
        p.ensure(height + p.lead)
        top = p.y
        for i, cell in enumerate(cells):
            for k, text in enumerate(cell):
                p.ops.append(
                    (
                        "text",
                        p.left + i * span + 2,
                        top - 2 - small - k * (small + 2),
                        text,
                        face,
                        small,
                    )
                )
            p.ops.append(("rect", p.left + i * span, top - height, span, height))
        p.y = top - height
    if total:
        p.line(total)


def render_affidavit(
    app: App, v: dict[str, Any], snapshot: dict[str, Any], template: dict[str, Any]
) -> tuple[bytes, dict[str, Any]]:
    rng = app.rng
    p = _Page(rng)
    # Stamp page first (own page), as portal-uploaded sworn copies carry the e-stamp certificate.
    stamp = v["stamp"]
    p.line("SYNTHETIC E-STAMP CERTIFICATE (BLIND SET)", bold=True)
    p.line("For tests only. Not a real stamp instrument.")
    fields = [
        ("Certificate No.", stamp["no"]),
        ("Certificate Issued Date", stamp["issued"].strftime("%d-%b-%Y %I:%M %p")),
        ("Description of Document", "Article 4 Affidavit"),
        ("Consideration Price (Rs.)", "0 (Zero)"),
        ("First Party", v["trust"]),
        ("Second Party", stamp["party"]),
        (
            "Stamp Duty Amount (Rs.)",
            f"{stamp['duty']} ({'One Hundred only' if stamp['duty'] == 100 else 'amount'})",
        ),
    ]
    order = fields[:]
    for k, val in order:
        p.line(f"{k} : {val}")
    p.pages.append([])
    p.y = p.top
    p.line(str(template["heading"]), bold=True)
    p.line(f"ACADEMIC YEAR – {_ay_long(v['ay'])}")
    header = [
        ("Permanent ID", v["pid"]),
        ("Application ID", v["aid_printed"]),
        ("Name of the Institute", v["institution"]),
        ("Address of the Institute", f"{v['town']}, Blind District, {v['state']}"),
        ("Type of Institute", "Private-Self Financing"),
        ("Region", v["region"]),
        ("Date of Application", _mdy(v["app_date"])),
    ]
    for k, val in header:
        p.line(f"{k} : {val}")
    p.line("Application for :")
    p.line("1. EoA Only")
    p.gap(0.4)
    p.wrapped(
        f"I, the deponent, being the Chairman of {v['trust']}, which runs {v['institution']}, "
        "do hereby solemnly affirm and declare as under:"
    )
    decls = _declaration_lines(template, v, rng)
    truth: dict[str, Any] = {"declarations": len(decls)}
    drop = set()
    if "decl_missing" in app.anomalies:
        drop = set(rng.sample(range(len(decls)), rng.choice((1, 2))))
        truth["dropped"] = len(drop)
    changed = rng.randrange(len(decls)) if "decl_changed" in app.anomalies else -1
    while changed in drop:
        changed = rng.randrange(len(decls))
    printed = [d for i, d in enumerate(decls) if i not in drop]
    if "decl_added" in app.anomalies:
        printed.insert(
            rng.randrange(1, len(printed)),
            {
                "block": "core",
                "number": 0,
                "text": "The institution shall also admit students on the strength of recommendation letters.",
                "bullets": [],
            },
        )
    core_n = ex_n = 0
    in_existing = False
    for d in printed:
        text = d["text"]
        if d is decls[changed] if changed >= 0 else False:
            text = _mutate(text, rng)
        if d["block"] == "existing_institute" and not in_existing:
            in_existing = True
            p.gap(0.5)
            p.line(str(template["existing_institute_heading"]), bold=True)
        if in_existing:
            ex_n += 1
            label = f"{ex_n}."
        else:
            core_n += 1
            label = f"{core_n}."
        p.wrapped(text, indent=18.0, label=label)
        for b in d["bullets"]:
            p.wrapped(b, indent=36.0, label="•")
    land = snapshot["land"]
    _table(
        p,
        "LAND DETAILS",
        [
            "Name of the deed Holder",
            "Document No.",
            "Date of Registration",
            "Plot No.",
            "Address (Village) District",
            "Area in Acre",
        ],
        [
            [
                d["holder"],
                d["document_no"],
                _mdy(date.fromisoformat(d["registration_date"])),
                d["plot_no"],
                d["village_district"],
                f"{d['area_acre']:.2f}",
            ]
            for d in land["deeds"]
        ],
        f"Total area in Acre {land['total_area']:.2f}",
    )
    p.gap(0.8)
    p.line("BUILT-UP AREA DETAILS", bold=True)
    captions = {
        "administrative": "ADMINISTRATIVE AREA",
        "amenities": "AMENITIES AREA",
        "instructional": "INSTRUCTIONAL AREA",
        "instructional_common": "INSTRUCTIONAL AREA – COMMON FACILITIES",
    }
    for block, caption in captions.items():
        _table(
            p,
            caption,
            ["Room No.", "Room type", "Carpet area (m²)", "Flooring", "Walls", "Electrification"],
            [
                [
                    r["room_id"],
                    r["room_type"],
                    f"{r['carpet_area_m2']:.1f}",
                    r["flooring"],
                    r["walls_painting"],
                    r["electrification"],
                ]
                for r in snapshot["rooms"][block]
            ],
            None,
        )
    p.gap(0.8)
    p.wrapped(
        f"VERIFICATION: Verified at {v['town']} on {_mdy(v['notarised'])} that the contents of the "
        "above affidavit are true and correct to the best of my knowledge and belief, and nothing "
        "material has been concealed."
    )
    p.line("DEPONENT")
    p.line(f"Sworn and signed before me on {_mdy(v['notarised'])}.")
    p.line(
        f"Notary (synthetic) · Reg. No. {v['notary_reg']} · Seal valid till {_mdy(v['seal_till'])}"
    )
    mark_box = None
    if "sig_image" in app.anomalies:
        p.gap(0.5)
        p.ensure(p.lead * 4)
        top = p.y
        lines = [
            f"Digitally signed by {v['signatory'].upper()}",
            f"Date: {v['issuer_dsc'].strftime('%Y.%m.%d %H:%M:%S')} +05'30'",
        ]
        for i, s in enumerate(lines):
            p.ops.append(("text", p.right - 224, top - 12 - i * p.lead, s, p.font, p.size - 1))
        p.ops.append(("rect", p.right - 230, top - p.lead * 3, 230.0, p.lead * 2.6))
        mark_box = (len(p.pages) - 1, p.right - 230, top - p.lead * 3, p.right, top)
        p.y = top - p.lead * 3
    pdf = p.render(f"SYNTHETIC Affidavit 2 blind-set document {v['aid']}")
    truth["mark_box"] = mark_box
    return pdf, truth


def render_accounts(app: App, v: dict[str, Any]) -> bytes:
    rng = app.rng
    p = _Page(rng)
    p.line("SYNTHETIC AUDITED STATEMENT OF ACCOUNTS (BLIND SET)", bold=True)
    p.line(v["trust"], bold=True)
    p.line(f"(running {v['institution']}, {v['town']})")
    end = date(int(v["fy"][:4]) + 1, 3, 31)
    month = end.strftime("%B")
    p.line(f"Income and Expenditure Account for the year ended {end.day} {month} {end.year}")
    income = rng.randint(40, 90) * 100000
    for label, val in (
        ("Total income", income),
        ("Total expenditure", income - rng.randint(1, 9) * 100000),
    ):
        p.line(f"{label}   Rs. {val:,}")
    p.gap(1.0)
    p.line("AUDITOR'S REPORT (extract)", bold=True)
    p.line("In our opinion the account gives a true and fair view.")
    p.line(f"For {v['firm']}", bold=True)
    p.line("Chartered Accountants")
    p.line(f"Firm Registration No.: {v['frn']}")
    p.line(f"{v['partner']}, Partner")
    p.line(rng.choice(("Membership No.: ", "M. No. ")) + v["member_printed"])
    if v["udin_printed"]:
        udin = v["udin_printed"]
        if rng.random() < 0.4:
            udin = f"{udin[:2]} {udin[2:8]} {udin[8:14]} {udin[14:]}"
        p.line(f"UDIN: {udin}")
    p.line(f"Place: {v['town']}")
    return p.render(f"SYNTHETIC accounts blind-set document {v['aid']}")


LABEL_ORDER = (
    "mismatch_detected",
    "expired",
    "manual_review_required",
    "source_unavailable",
    "verification_pending",
    "verified",
)


def _rule_labels() -> dict[str, str]:
    """Label each rule gives its document (from the versioned rule files: the spec, not code)."""
    from satya_affidavit.paths import rules_dir

    out: dict[str, str] = {}
    for name in ("m5-affidavit.yaml", "m6-signatures.yaml"):
        raw = yaml.safe_load((rules_dir() / name).read_text("utf-8"))
        out.update({r["rule_id"]: r["label"] for r in raw["rules"]})
    return out


def _letters(rng: random.Random, n: int) -> str:
    return "".join(rng.choice("ABCDEFGHJKLMNPQRSTUVWXYZ") for _ in range(n))


def build_application(
    app: App, root: Path, labels: dict[str, str], template: dict[str, Any]
) -> dict[str, Any]:
    rng = app.rng
    ay = rng.choice(("2024-25", "2025-26", "2026-27"))
    start = int(ay[:4])
    state, region = rng.choice(STATES)
    n = rng.randint(100, 999)
    app_date = date(start, rng.randint(9, 12), rng.randint(1, 20))
    stamp_issued = datetime.combine(
        app_date + timedelta(days=rng.randint(1, 3)), datetime.min.time()
    ) + timedelta(hours=rng.randint(9, 17), minutes=rng.randint(0, 59))
    notarised = stamp_issued.date() + timedelta(days=rng.randint(0, 2))
    if "chrono" in app.anomalies:
        notarised = stamp_issued.date() - timedelta(days=rng.randint(1, 3))
    seal_till = notarised + timedelta(days=rng.randint(400, 900))
    if "notary_expired" in app.anomalies:
        seal_till = notarised - timedelta(days=rng.randint(1, 30))
    issuer_dsc = datetime.combine(
        max(notarised, stamp_issued.date()) + timedelta(days=1), datetime.min.time(), IST
    ) + timedelta(hours=11)
    uploader_dsc = issuer_dsc + timedelta(days=1, hours=5, minutes=30)
    uploaded_at = uploader_dsc + timedelta(minutes=10)
    signatory = f"Blind Trustee {rng.choice(SURNAMES)} {n}"
    fy = f"{start - 1}-{str(start)[2:]}"
    yy = f"{start:04d}"[2:]
    member = f"{rng.randint(100000, 999999)}"
    udin = f"{yy}{member}{_letters(rng, 6)}{rng.randint(1000, 9999)}"
    udin_printed, member_printed = udin, member
    if "udin_struct" in app.anomalies:
        udin_printed = udin[:-1]
    if "udin_member" in app.anomalies:
        other = f"{(int(member) % 900000) + 100000 + 7}"[:6]
        udin_printed = f"{yy}{other if other != member else '123456'}{udin[8:]}"
    aid = f"1-9{rng.randint(10**9, 10**10 - 1)}"[:12]
    aid_printed = (
        f"1-9{rng.randint(10**9, 10**10 - 1)}"[:12] if "header_aid" in app.anomalies else aid
    )
    pid = f"1-9{rng.randint(100000, 999999)}"
    v: dict[str, Any] = {
        "ay": ay,
        "ay_long": _ay_long(ay),
        "aid": aid,
        "aid_printed": aid_printed,
        "pid": pid,
        "state": state,
        "region": region,
        "town": f"Blind Town {rng.randint(1, 99)}",
        "trust": f"Blind Educational Trust {n}",
        "institution": f"Blind Institute of Technology {n}",
        "signatory": signatory,
        "app_date": app_date,
        "land_acre": round(rng.uniform(4, 25), 2),
        "deed_count": rng.randint(1, 3),
        "stamp": {
            "no": f"IN-{state[:2].upper()}{rng.randint(10**13, 10**14 - 1)}{_letters(rng, 1)}",
            "issued": stamp_issued,
            "duty": rng.choice((20, 50))
            if "stamp_duty" in app.anomalies
            else rng.choice((100, 200)),
            "party": "BLIND OTHER BODY" if "stamp_party" in app.anomalies else "AICTE NEW DELHI",
        },
        "notarised": notarised,
        "seal_till": seal_till,
        "notary_reg": f"BLIND-NOT-{rng.randint(1000, 9999)}",
        "issuer_dsc": issuer_dsc,
        "fy": fy,
        "firm": f"Blind & Associates {n}",
        "frn": f"{rng.randint(100000, 999999)}{rng.choice('NSW')}",
        "partner": f"CA Blind Partner {rng.choice(SURNAMES)}",
        "member_printed": member_printed,
        "udin_printed": udin_printed,
    }
    snapshot = _snapshot(app, v)
    pdf, truth = render_affidavit(app, v, snapshot, template)
    # --- signatures (own plan per anomaly) ---
    kinds = {"issuer": "chairman", "uploader": "chairman"}
    if "sig_untrusted" in app.anomalies:
        kinds = {"issuer": "untrusted", "uploader": "untrusted"}
    if "sig_signer" in app.anomalies:
        kinds = {"issuer": "wrong-signer", "uploader": "wrong-signer"}
    specs: list[pki.SignerSpec] = []

    def identity(kind: str, when: datetime) -> pki.Identity:
        spec = pki.signer_spec(kind, n % 90 + 1, signatory, when)
        specs.append(spec)
        return pki.signer(spec)

    if "sig_image" not in app.anomalies:
        pdf = signing.sign(pdf, identity(kinds["issuer"], issuer_dsc), "Signature1", issuer_dsc)
    pdf = signing.sign(pdf, identity(kinds["uploader"], uploader_dsc), "Signature2", uploader_dsc)
    if "sig_modified" in app.anomalies:
        pdf = signing.add_page_content(pdf, len(truth) and 1, "ADDED AFTER SIGNING")
    accounts = render_accounts(app, v)
    accounts = signing.sign(
        accounts, identity("chairman", uploader_dsc), "Signature1", uploader_dsc
    )

    case_id = _ulid_like(rng, "cas_")
    docs = [
        (AFF_SLOT, "affidavit-2", "Affidavit 2 (sworn copy)", "T", AFF_FILE, pdf),
        (
            ACC_SLOT,
            "audited-accounts",
            f"Audited statement of accounts FY {fy}",
            "E",
            ACC_FILE,
            accounts,
        ),
    ]
    case = {
        "case_id": case_id,
        "application_id": aid,
        "permanent_id": pid,
        "ay": ay,
        "regional_office": region,
        "state": state,
        "route": "self_disclosure",
        "stage": "2",
        "category_set": ["EoA Only"],
        "institution_name": v["institution"],
        "affidavit_draft": {
            "template_id": template["template_id"],
            "ay": ay,
            "category_set": ["EoA Only"],
            "header": {
                "institution_name": v["institution"],
                "address": f"{v['town']}, Blind District, {state}",
                "town": v["town"],
            },
        },
        "documents": [],
    }
    manifest_docs: dict[str, Any] = {}
    out = root / app.slug
    out.mkdir(parents=True, exist_ok=True)
    for slot, declared, title, fmt, name, data in docs:
        doc_id = _ulid_like(rng, "doc_")
        (out / name).write_bytes(data)
        case["documents"].append(
            {
                "doc_id": doc_id,
                "slot": slot,
                "declared_type": declared,
                "title": title,
                "format_type": fmt,
                "file": name,
                "sha256": hashlib.sha256(data).hexdigest(),
                "bytes": len(data),
                "uploaded_at": uploaded_at.isoformat(),
            }
        )
        which = "affidavit" if slot == AFF_SLOT else "accounts"
        rules = sorted(
            r for a in app.anomalies if ANOMALIES[a][1] == which for r in ANOMALIES[a][0]
        )
        base = "verified" if which == "affidavit" else "source_unavailable"
        worst = [labels[r] for r in rules] + [base]
        manifest_docs[doc_id] = {
            "slot": slot,
            "expected_rules": rules,
            "expected_label": min(worst, key=LABEL_ORDER.index),
        }
    (out / "case.json").write_text(json.dumps(case, indent=1), "utf-8")
    (out / "snapshot.json").write_text(json.dumps(snapshot, indent=1), "utf-8")
    printed = {
        "stamp.certificate_no": v["stamp"]["no"],
        "stamp.duty": v["stamp"]["duty"],
        "notary.date": notarised.isoformat(),
        "notary.valid_till": seal_till.isoformat(),
        "udin": udin_printed.replace(" ", ""),
        "udin.membership_no": member_printed,
    }
    return {
        "app": app.slug,
        "seed": app.seed,
        "case_id": case_id,
        "anomalies": app.anomalies,
        "clean": not app.anomalies,
        "documents": manifest_docs,
        "printed": printed,
        "crl_signers": [s.kind for s in specs],
        "file_sha256": {d["file"]: d["sha256"] for d in case["documents"]},
    }


def generate(
    root: Path, seeds: tuple[int, ...], total: int, clean_min: float = 0.4, clean_share: float = 0.5
) -> Path:
    """Write the set and a sealed manifest.json; returns the manifest path."""
    root.mkdir(parents=True, exist_ok=True)
    labels = _rule_labels()
    template = _template()
    per_seed = [
        total // len(seeds) + (1 if i < total % len(seeds) else 0) for i in range(len(seeds))
    ]
    apps: list[App] = []
    for seed, count in zip(seeds, per_seed, strict=True):
        for i in range(count):
            rng = random.Random(f"blind:{seed}:{i}")
            app = App(i, seed, rng)
            app.anomalies = _pick_anomalies(rng, clean_share)
            apps.append(app)
    need = math.ceil(clean_min * total)
    fixer = random.Random(f"blind-clean:{seeds}")
    dirty = [a for a in apps if a.anomalies]
    fixer.shuffle(dirty)
    while len(apps) - len(dirty) < need and dirty:
        dirty.pop().anomalies = []
    entries = [build_application(app, root, labels, template) for app in apps]
    manifest = {
        "synthetic": "Synthetic data generated for this repository. Not real AICTE data.",
        "seeds": list(seeds),
        "applications": entries,
    }
    path = root / "manifest.json"
    path.write_text(json.dumps(manifest, indent=1, sort_keys=True), "utf-8")
    return path
