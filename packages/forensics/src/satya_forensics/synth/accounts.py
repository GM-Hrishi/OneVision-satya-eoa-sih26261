"""Synthetic audited statement of accounts (Annexure-2.1(vii)) for the P-18 UDIN check.

One text-layer page: the Trust's income and expenditure account for the previous financial year
and the auditor's block (firm, FRN, partner, membership no., UDIN, place, date), the fields of
design B1 row 7. Every value is invented and the page says SYNTHETIC. A UDIN here follows the
structure YY + 6-digit membership no. + 6 letters + 4 digits (design B1 row 7 [VERIFY]); none is
a real UDIN and the membership numbers sit in a demo range (99xxxx).
"""

import io
from dataclasses import dataclass
from datetime import date

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen.canvas import Canvas

PAGE_W, PAGE_H = A4
FONT, BOLD = "Helvetica", "Helvetica-Bold"


@dataclass(frozen=True)
class AuditedAccounts:
    application_id: str
    trust_name: str
    institution_name: str
    town: str
    fy: str  # e.g. "2025-26"
    income_rupees: int
    expenditure_rupees: int
    firm: str
    frn: str  # as printed: 6+1 or 7+1 with a leading zero
    partner: str
    membership_no: str  # as printed beside the partner's name
    udin: str | None  # as printed (may carry spaces); None = no UDIN printed
    report_date: date


def fy_end(fy: str) -> date:
    return date(int(fy[:4]) + 1, 3, 31)


def render_accounts(acc: AuditedAccounts) -> bytes:
    buf = io.BytesIO()
    c = Canvas(buf, pagesize=A4, invariant=True, pageCompression=0)
    c.setTitle(f"SYNTHETIC audited statement of accounts {acc.application_id}")
    c.setAuthor("SATYA-EoA synthetic generator (Team OneVision)")
    c.setSubject("Synthetic test document. Not a real audit report.")
    c.setCreator("satya_forensics.synth")
    y = PAGE_H - 64

    def line(text: str, x: float = 56, font: str = FONT, size: float = 10.5) -> None:
        nonlocal y
        c.setFont(font, size)
        c.drawString(x, y, text)
        y -= size * 1.45

    end = fy_end(acc.fy)
    line("SYNTHETIC AUDITED STATEMENT OF ACCOUNTS (MOCK)", font=BOLD, size=12)
    line("For tests only. Not a real audit report and not valid for any purpose.")
    y -= 6
    line(acc.trust_name, font=BOLD)
    line(f"(running {acc.institution_name}, {acc.town})")
    line(f"Income and Expenditure Account for the year ended {end:%d %B %Y} (FY {acc.fy})")
    y -= 4
    rows = [
        ("Fees and other academic receipts", f"{acc.income_rupees:,}"),
        ("Total income", f"{acc.income_rupees:,}"),
        ("Salaries, maintenance and other expenditure", f"{acc.expenditure_rupees:,}"),
        ("Total expenditure", f"{acc.expenditure_rupees:,}"),
        ("Excess of income over expenditure", f"{acc.income_rupees - acc.expenditure_rupees:,}"),
    ]
    c.setLineWidth(0.6)
    top = y + 12
    for label, value in rows:
        line(label, x=62)
        c.drawRightString(PAGE_W - 62, y + 10.5 * 1.45, f"Rs. {value}")
    c.rect(56, y + 6, PAGE_W - 112, top - y - 6, stroke=1, fill=0)
    y -= 14
    line("AUDITOR'S REPORT (extract)", font=BOLD)
    line("In our opinion the account gives a true and fair view of the excess of income over")
    line(f"expenditure of the Trust for the year ended {end:%d %B %Y}.")
    y -= 10
    line(f"For {acc.firm}", font=BOLD)
    line("Chartered Accountants")
    line(f"Firm Registration No.: {acc.frn}")
    y -= 8
    line(f"{acc.partner}, Partner")
    line(f"Membership No.: {acc.membership_no}")
    if acc.udin is not None:
        line(f"UDIN: {acc.udin}")
    line(f"Place: {acc.town}")
    line(f"Date: {acc.report_date:%d-%b-%Y}")
    line("(Signature and seal not reproduced: synthetic test document.)")
    c.setFont(FONT, 7.5)
    c.drawString(
        56,
        30,
        f"Application Number: {acc.application_id} · Approval Portal (Mock, for demo) · "
        "SYNTHETIC TEST DOCUMENT",
    )
    c.drawRightString(PAGE_W - 56, 30, "Page 1 of 1")
    c.showPage()
    c.save()
    return buf.getvalue()
