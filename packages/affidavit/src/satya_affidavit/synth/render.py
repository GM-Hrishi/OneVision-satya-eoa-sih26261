"""Render a synthetic Affidavit 2 as a text-layer PDF (tests and demo only; never in a runtime
image).

A tiny layout engine on the reportlab canvas, so the generator controls exactly what the M5
extractor has to cope with: re-typeset line breaks, hyphen-wrapped words, struck-through option
choices, ruled tables that break across pages with a repeated header, a stamp page in front and a
running footer.
Every page says SYNTHETIC; nothing here imitates a real portal, logo or signature.
"""

import io
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any

from reportlab.lib.pagesizes import A4
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen.canvas import Canvas

from satya_affidavit.normalise import OPTION_MARKUP, format_date
from satya_affidavit.template import ROOM_FIELDS, Draft

PAGE_W, PAGE_H = A4
TOP = PAGE_H - 56
BOTTOM = 64
FONT = "Helvetica"
BOLD = "Helvetica-Bold"
FOOTER_SIZE = 7.5
LAND_WIDTHS = (92.0, 86.0, 66.0, 82.0, 113.0, 56.0)
ROOM_WIDTHS = (58.0, 142.0, 66.0, 76.0, 76.0, 78.0)


@dataclass(frozen=True)
class Style:
    """How the sworn copy is re-typeset. None of these is a change to the affidavit."""

    name: str = "plain"
    font_size: float = 10.5
    margin_left: float = 56.0
    margin_right: float = 56.0
    hyphenate: bool = False
    upper_names: bool = False
    impossible_month_dates: bool = False
    alt_options: bool = False
    compact_numbers: bool = False


@dataclass
class Seg:
    text: str
    struck: bool = False


@dataclass
class PrintDecl:
    key: str  # "decl:<canonical no>" or "decl:added"
    printed_no: int
    block: str
    segments: list[Seg]
    bullets: list[str] = field(default_factory=list)

    def kept_text(self) -> str:
        words = [s.text for s in self.segments if not s.struck]
        return " ".join(" ".join(words + self.bullets).split())


@dataclass
class PrintModel:
    """Everything the sworn copy prints, after any planted change. Also the ground truth."""

    aid: str
    heading: str
    ay_line: str
    header: list[tuple[str, str, str]]  # (key, label, value)
    category_label: str
    categories: list[str]
    affirmation: str
    core: list[PrintDecl]
    existing_heading: str
    existing: list[PrintDecl]
    extra_blocks: list[tuple[str, list[PrintDecl]]]
    land_caption: str
    land_labels: list[str]
    land_rows: list[tuple[str, list[str]]]  # (row key, cells)
    land_total_label: str
    rooms_heading: str
    room_labels: list[str]
    room_tables: list[tuple[str, str, list[tuple[str, list[str]]]]]  # (table, caption, rows)
    verification: str
    stamp: dict[str, str] | None
    notary: list[str]
    stamp_title: str = "SYNTHETIC E-STAMP CERTIFICATE (MOCK)"
    # Printed "Digitally signed by …" mark (no /ByteRange): lines drawn in a box after the notary
    # block (M6 SIG-IMAGE). `mark_box` is filled by render(): (page, x0, y0, x1, y1) in points.
    dsc_mark: list[str] = field(default_factory=list)
    mark_box: tuple[int, float, float, float, float] | None = None

    def renumber(self) -> None:
        for i, d in enumerate(self.core, start=1):
            d.printed_no = i
        for i, d in enumerate(self.existing, start=1):
            d.printed_no = i


def _segments(markup: str, alt: bool) -> list[Seg]:
    segs: list[Seg] = []
    pos = 0
    for match in OPTION_MARKUP.finditer(markup):
        segs.extend(Seg(w) for w in markup[pos : match.start()].split())
        choices = [c.strip() for c in match[2].split("|")]
        chosen = len(choices) - 1 if alt else 0
        tokens = [Seg(choices[0])]
        for choice in choices[1:]:
            tokens += [Seg("/"), Seg(choice)]
        for i in range(len(choices)):
            if i == chosen:
                continue
            tokens[2 * i].struck = True
            tokens[2 * i - 1 if i > chosen else 2 * i + 1].struck = True
        for token in tokens:  # a choice may hold several words
            segs.extend(Seg(w, token.struck) for w in token.text.split())
        pos = match.end()
    segs.extend(Seg(w) for w in markup[pos:].split())
    return segs


def _date_cell(value: date, order: str, style: Style) -> str:
    if style.impossible_month_dates and value.day > 12:
        other = "DD/MM/YYYY" if order == "MM/DD/YYYY" else "MM/DD/YYYY"
        return format_date(value, other)
    return format_date(value, order)


def _num(value: float, style: Style, places: int) -> str:
    return f"{value:g}" if style.compact_numbers else f"{value:.{places}f}"


def build_print_model(draft: Draft, case: dict[str, Any], style: Style) -> PrintModel:
    t = draft.template
    order = t.date_order
    name = draft.header.institution_name
    shown_name = name.upper() if style.upper_names else name
    header = []
    for key, label in t.header_fields:
        value = draft.header_value(key)
        if key == "institution_name":
            value = shown_name
        header.append((key, label, value))
    core: list[PrintDecl] = []
    existing: list[PrintDecl] = []
    for d in draft.declarations:
        pd = PrintDecl(
            f"decl:{d.no}",
            d.printed_no,
            d.block,
            _segments(d.markup, style.alt_options),
            list(d.bullets),
        )
        (core if d.block == "core" else existing).append(pd)
    land_rows = [
        (
            str(i),
            [
                r.holder,
                r.document_no,
                _date_cell(r.registration_date, order, style),
                r.plot_no,
                r.village_district,
                _num(r.area_acre, style, 2),
            ],
        )
        for i, r in enumerate(draft.land_rows, start=1)
    ]
    room_tables = []
    for table, _, caption in t.room_tables:
        rows = []
        for r in draft.rooms.get(table, ()):
            cells = [str(getattr(r, f)) for f in ROOM_FIELDS]
            cells[2] = _num(r.carpet_area_m2, style, 1)
            if style.upper_names:
                cells[3:] = [c.upper() for c in cells[3:]]
            rows.append((r.room_id, cells))
        room_tables.append((table, caption, rows))
    stamp_meta = case.get("stamp", {})
    sworn_on = (
        date.fromisoformat(stamp_meta["notarised"]) if stamp_meta else draft.header.application_date
    )
    stamp, stamp_title = _stamp_fields(stamp_meta, draft) if stamp_meta else (None, "")
    notary = []
    if stamp_meta:
        notary = [
            f"Sworn and signed before me on {format_date(sworn_on, order)}.",
            f"Notary (synthetic) · Reg. No. {stamp_meta['notary_reg_no']} · Seal valid till "
            f"{format_date(date.fromisoformat(stamp_meta['notary_valid_till']), order)}",
            "Seal and signatures are not reproduced: synthetic test document.",
        ]
    verification = t.verification.format(
        town=draft.header.town, sworn_date=format_date(sworn_on, order)
    )
    affirmation = draft.affirmation.replace(name, shown_name)
    return PrintModel(
        aid=draft.header.aid,
        heading=t.heading,
        ay_line=draft.ay_line,
        header=header,
        category_label=t.category_label,
        categories=list(draft.category_list),
        affirmation=affirmation,
        core=core,
        existing_heading=t.existing_heading,
        existing=existing,
        extra_blocks=[],
        land_caption=t.land_caption,
        land_labels=[label for _, label in t.land_columns],
        land_rows=land_rows,
        land_total_label=t.land_total_label,
        rooms_heading=t.rooms_heading,
        room_labels=[label for _, label in t.room_columns],
        room_tables=room_tables,
        verification=verification,
        stamp=stamp,
        notary=notary,
        stamp_title=stamp_title or "SYNTHETIC E-STAMP CERTIFICATE (MOCK)",
    )


def shcil_datetime(value: str) -> str:
    """SHCIL-style certificate date: ISO date or date-time -> '22-Nov-2026 11:05 AM'."""
    when = datetime.fromisoformat(value if "T" in value else f"{value}T11:05:00")
    return when.strftime("%d-%b-%Y %I:%M %p")


def _stamp_fields(meta: dict[str, Any], draft: Draft) -> tuple[dict[str, str], str]:
    """The stamp page fields (design B1 row 1). Physical paper carries no certificate number."""
    trust = draft.header.trust_name
    duty = int(meta.get("duty", 100))
    words = {100: "One Hundred", 50: "Fifty", 20: "Twenty", 500: "Five Hundred"}.get(duty, "")
    if meta.get("instrument", "e-stamp") == "physical":
        fields = {
            "Serial No.": meta["certificate_no"],
            "Denomination": f"Rs. {duty} ({words} only)",
            "Date of Sale": shcil_datetime(meta["issued"]),
            "Sold to": trust,
            "Purpose": meta.get("article", "Article 4 Affidavit"),
            "Stamp Vendor": f"Demo Stamp Vendor (licence {meta['notary_reg_no']}-SV)",
        }
        return fields, "SYNTHETIC NON-JUDICIAL STAMP PAPER (MOCK)"
    fields = {
        "Certificate No.": meta["certificate_no"],
        "Certificate Issued Date": shcil_datetime(meta["issued"]),
        "Account Reference": "DEMOACC (SYNTHETIC)",
        "Unique Doc. Reference": f"SUBIN-DEMO-{meta['certificate_no'][-6:]}",
        "Purchased by": trust,
        "Description of Document": meta.get("article", "Article 4 Affidavit"),
        "Consideration Price (Rs.)": "0 (Zero)",
        "First Party": trust,
        "Second Party": meta.get("second_party", "AICTE NEW DELHI"),
        "Stamp Duty Paid By": trust,
        "Stamp Duty Amount (Rs.)": f"{duty} ({words} only)",
    }
    return fields, "SYNTHETIC E-STAMP CERTIFICATE (MOCK)"


# ---- layout -----------------------------------------------------------------------------------
Op = tuple[Any, ...]


class _Writer:
    def __init__(self, style: Style) -> None:
        self.style = style
        self.size = style.font_size
        self.lead = style.font_size * 1.38
        self.left = style.margin_left
        self.right = PAGE_W - style.margin_right
        self.pages: list[list[Op]] = []
        self.positions: dict[str, int] = {}
        self.y = 0.0
        self.new_page()

    @property
    def page(self) -> int:
        return len(self.pages)

    def new_page(self) -> None:
        self.pages.append([])
        self.y = TOP

    def ensure(self, height: float) -> None:
        if self.y - height < BOTTOM:
            self.new_page()

    def mark(self, key: str) -> None:
        self.positions.setdefault(key, self.page)

    def text(self, x: float, text: str, font: str = FONT, size: float | None = None) -> None:
        self.pages[-1].append(("text", x, self.y, text, font, size or self.size, False))

    def gap(self, lines: float = 0.5) -> None:
        self.y -= self.lead * lines

    def line_text(
        self, text: str, x: float | None = None, font: str = FONT, center: bool = False
    ) -> None:
        self.ensure(self.lead)
        width = stringWidth(text, font, self.size)
        start = (PAGE_W - width) / 2 if center else (x if x is not None else self.left)
        self.text(start, text, font)
        self.y -= self.lead

    def paragraph(
        self, words: list[Seg], indent: float, prefix: str | None = None, font: str = FONT
    ) -> None:
        space = stringWidth(" ", font, self.size)
        queue = list(words)
        first = True
        while queue:
            self.ensure(self.lead)
            if first and prefix:
                self.text(self.left, prefix, font)
            first = False
            x = self.left + indent
            placed = 0
            while queue:
                seg = queue[0]
                width = stringWidth(seg.text, font, self.size)
                if x + width <= self.right:
                    self._word(x, seg, width, font)
                    x += width + space
                    placed += 1
                    queue.pop(0)
                    continue
                split = self._hyphen_split(seg, x)
                if split:
                    head, tail = split
                    self._word(x, Seg(head + "-"), stringWidth(head + "-", font, self.size), font)
                    queue[0] = Seg(tail)
                    placed += 1
                elif placed == 0:  # a single over-long word: place it anyway
                    self._word(x, seg, width, font)
                    queue.pop(0)
                break
            self.y -= self.lead

    def _hyphen_split(self, seg: Seg, x: float) -> tuple[str, str] | None:
        word = seg.text
        if not self.style.hyphenate or seg.struck or len(word) < 7 or not word.isalpha():
            return None
        for k in range(len(word) - 3, 2, -1):
            if x + stringWidth(word[:k] + "-", FONT, self.size) <= self.right:
                return word[:k], word[k:]
        return None

    def _word(self, x: float, seg: Seg, width: float, font: str) -> None:
        self.pages[-1].append(("text", x, self.y, seg.text, font, self.size, seg.struck))
        if seg.struck:
            y = self.y + self.size * 0.3
            self.pages[-1].append(("line", x - 0.5, y, x + width + 0.5, y, 0.8))

    def table(
        self,
        labels: list[str],
        widths: tuple[float, ...],
        rows: list[tuple[str, list[str]]],
        key_prefix: str,
        tail_row: list[str] | None = None,
    ) -> None:
        size = self.size - 1.5
        lead = size * 1.3
        pad = 3.0

        def wrap(text: str, width: float, font: str) -> list[str]:
            lines: list[str] = []
            current = ""
            words: list[str] = []
            for word in text.split():  # break a word that cannot fit a cell on its own
                while stringWidth(word, font, size) > width - 2 * pad and len(word) > 1:
                    cut = len(word) - 1
                    while cut > 1 and stringWidth(word[:cut], font, size) > width - 2 * pad:
                        cut -= 1
                    words.append(word[:cut])
                    word = word[cut:]
                words.append(word)
            for word in words:
                trial = f"{current} {word}".strip()
                if stringWidth(trial, font, size) <= width - 2 * pad or not current:
                    current = trial
                else:
                    lines.append(current)
                    current = word
            return [*lines, current] if current else lines or [""]

        def draw_row(cells: list[str], font: str) -> None:
            wrapped = [wrap(c, w, font) for c, w in zip(cells, widths, strict=True)]
            height = max(len(w) for w in wrapped) * lead + 2 * pad
            top = self.y
            x = self.left
            ops = self.pages[-1]
            for lines, width in zip(wrapped, widths, strict=True):
                for i, line in enumerate(lines):
                    ops.append(
                        (
                            "text",
                            x + pad,
                            top - pad - size * 0.85 - i * lead,
                            line,
                            font,
                            size,
                            False,
                        )
                    )
                x += width
            total = sum(widths)
            ops.append(("rect", self.left, top - height, total, height, 0.6))
            x = self.left
            for width in widths[:-1]:
                x += width
                ops.append(("line", x, top, x, top - height, 0.6))
            self.y = top - height

        def row_height(cells: list[str], font: str) -> float:
            return (
                max(len(wrap(c, w, font)) for c, w in zip(cells, widths, strict=True)) * lead
                + 2 * pad
            )

        header_h = row_height(labels, BOLD)
        self.ensure(header_h + row_height(rows[0][1], FONT) if rows else header_h)
        draw_row(labels, BOLD)
        for key, cells in rows:
            h = row_height(cells, FONT)
            if self.y - h < BOTTOM:
                self.new_page()
                draw_row(labels, BOLD)
            self.mark(f"{key_prefix}:{key}")
            draw_row(cells, FONT)
        if tail_row is not None:
            if self.y - row_height(tail_row, FONT) < BOTTOM:
                self.new_page()
                draw_row(labels, BOLD)
            draw_row(tail_row, FONT)
        self.y -= self.lead * 0.8


def _stamp_page(w: _Writer, stamp: dict[str, str], title: str) -> None:
    w.line_text(title, font=BOLD, center=True)
    w.line_text(
        "For tests only. Not a real stamp instrument and not valid for any purpose.", center=True
    )
    w.gap(1)
    for label, value in stamp.items():
        w.ensure(w.lead)
        w.text(w.left + 20, label, BOLD)
        w.text(w.left + 200, f": {value}")
        w.y -= w.lead
    w.gap(0.5)
    w.pages[-1].append(("rect", w.left, w.y, w.right - w.left, TOP - w.y + w.lead, 1.0))
    w.new_page()


def render(model: PrintModel, style: Style) -> tuple[bytes, dict[str, int]]:
    """PDF bytes + the page of every keyed element (decl:<n>, land:<row>, <table>:<room>, …)."""
    w = _Writer(style)
    if model.stamp:
        _stamp_page(w, model.stamp, model.stamp_title)
    w.mark("heading")
    w.line_text(model.heading, font=BOLD, center=True)
    w.mark("header:ay")
    w.line_text(model.ay_line, font=BOLD, center=True)
    w.line_text("(Synthetic test document · mock approval portal draft)", center=True)
    w.gap(0.5)
    for key, label, value in model.header:
        w.mark(f"header:{key}")
        w.ensure(w.lead)
        w.text(w.left, label)
        w.text(w.left + 150, f": {value}")
        w.y -= w.lead
    w.mark("category_line")
    w.line_text(f"{model.category_label} :")
    for i, category in enumerate(model.categories, start=1):
        w.line_text(f"{i}. {category}", x=w.left + 22)
    w.gap(0.5)
    w.paragraph([Seg(x) for x in model.affirmation.split()], indent=0)
    w.gap(0.4)

    def decls(items: list[PrintDecl]) -> None:
        for d in items:
            w.mark(d.key)
            w.paragraph(d.segments, indent=22, prefix=f"{d.printed_no}.")
            for bullet in d.bullets:
                w.ensure(w.lead)
                w.text(w.left + 28, "•")
                w.paragraph([Seg(x) for x in bullet.split()], indent=40)
            w.gap(0.25)

    decls(model.core)
    w.gap(0.3)
    w.line_text(model.existing_heading, font=BOLD)
    decls(model.existing)
    for heading, items in model.extra_blocks:
        w.gap(0.3)
        w.line_text(heading, font=BOLD)
        decls(items)
    w.gap(0.5)
    w.ensure(w.lead * 4)
    w.mark("table:land")
    w.line_text(model.land_caption, font=BOLD)
    w.table(
        model.land_labels,
        LAND_WIDTHS,
        model.land_rows,
        "land",
        [model.land_total_label, "", "", "", "", ""],
    )
    w.ensure(w.lead * 4)
    w.line_text(model.rooms_heading, font=BOLD)
    for table, caption, rows in model.room_tables:
        w.ensure(w.lead * 4)
        w.mark(f"table:{table}")
        w.line_text(caption, font=BOLD)
        w.table(model.room_labels, ROOM_WIDTHS, rows, table)
    w.gap(0.5)
    w.mark("verification")
    w.paragraph([Seg(x) for x in model.verification.split()], indent=0)
    w.gap(1)
    w.line_text("DEPONENT", font=BOLD)
    w.line_text("(Signature not reproduced: synthetic test document.)")
    for line in model.notary:
        w.line_text(line)
    if model.dsc_mark:
        _dsc_mark(w, model)
    return _emit(w, model.aid), w.positions


def _dsc_mark(w: _Writer, model: PrintModel) -> None:
    """A printed signature mark: text in a ruled box, as a flattened stamp image would carry."""
    size = w.size - 1.5
    lead = size * 1.35
    height = lead * len(model.dsc_mark) + 8
    w.gap(0.5)
    w.ensure(height + w.lead)
    x0 = w.right - 230.0
    top = w.y
    ops = w.pages[-1]
    for i, line in enumerate(model.dsc_mark):
        ops.append(("text", x0 + 6, top - 4 - size * 0.85 - i * lead, line, FONT, size, False))
    ops.append(("rect", x0, top - height, 230.0, height, 0.8))
    w.mark("dsc_mark")
    model.mark_box = (w.page, x0, top - height, x0 + 230.0, top)
    w.y = top - height - w.lead


def _emit(w: _Writer, aid: str) -> bytes:
    buf = io.BytesIO()
    canvas = Canvas(buf, pagesize=A4, invariant=True, pageCompression=0)
    canvas.setTitle(f"SYNTHETIC Affidavit 2 test document {aid}")
    canvas.setAuthor("SATYA-EoA synthetic generator (Team OneVision)")
    canvas.setSubject("Synthetic test document. Not a real affidavit.")
    canvas.setCreator("satya_affidavit.synth")
    total = len(w.pages)
    for number, ops in enumerate(w.pages, start=1):
        for op in ops:
            kind = op[0]
            if kind == "text":
                _, x, y, text, font, size, _struck = op
                canvas.setFont(font, size)
                canvas.drawString(x, y, text)
            elif kind == "line":
                _, x0, y0, x1, y1, width = op
                canvas.setLineWidth(width)
                canvas.line(x0, y0, x1, y1)
            elif kind == "rect":
                _, x, y, rw, rh, width = op
                canvas.setLineWidth(width)
                canvas.rect(x, y, rw, rh, stroke=1, fill=0)
        canvas.setFont(FONT, FOOTER_SIZE)
        canvas.drawString(
            w.left,
            30,
            f"Application Number: {aid} · Approval Portal (Mock, for demo) · "
            "SYNTHETIC TEST DOCUMENT",
        )
        canvas.drawRightString(w.right, 30, f"Page {number} of {total}")
        canvas.showPage()
    canvas.save()
    return buf.getvalue()
