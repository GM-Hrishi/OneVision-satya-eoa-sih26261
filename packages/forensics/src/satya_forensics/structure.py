"""Heuristic PDF structure indicators (T6). Commodity checks, labelled `check_kind: "heuristic"`.

Four indicators look at a key value (a date, an area, a stamp or application number, an amount) on
a page of the affidavit or of a time-bound certificate:

1. `annotation_over_value`  a FreeText, Square, Highlight or Stamp annotation covers the value;
2. `font_differs`           the value is set in another font family or size than its line;
3. `cover_over_text`        an opaque white (page-colour) box is drawn after the value's text, which
                           is still in the text layer;
4. `glyph_overlap`          characters of the value are drawn on top of each other.

Each one is a low or medium severity indicator that asks for a person to look
(`manual_review_required` at most; never `mismatch_detected`). Each has an evidence region. None
proves anything: the limitation texts name the ordinary causes. Text layer only; geometry comes from
pdfminer in page space.
"""

import io
import re
from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import Any

import pdfplumber
from pdfminer.layout import LTChar, LTContainer, LTRect
from pdfminer.psparser import PSException
from pdfplumber.utils.exceptions import PdfminerException

from satya_forensics.textlayer import Box

CHECK_KIND = "heuristic"
ANNOTATION_SUBTYPES = frozenset({"FreeText", "Square", "Highlight", "Stamp"})
MONTHS = "Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec"
KEY_VALUE = re.compile(
    rf"""
    \b\d{{1,2}}[./-]\d{{1,2}}[./-]\d{{2,4}}\b
    | \b\d{{4}}-\d{{2}}-\d{{2}}\b
    | \b\d{{1,2}}\s+(?:{MONTHS})[a-z]*\.?\s+\d{{4}}\b
    | \b\d+(?:\.\d+)?\s*(?:acres?|hectares?|sq\.?\s?m|m2)\b
    | \bIN-[A-Z]{{2}}\d{{8,}}[A-Z0-9]*\b
    | \b1-\d{{7,11}}\b
    | \b\d{{8}}[A-Z0-9]{{10}}\b
    | (?:Rs\.?|INR)\s?\d[\d,]*(?:\.\d+)?
    """,
    re.VERBOSE | re.IGNORECASE,
)
OVERLAP_SHARE = 0.6  # of the smaller glyph box; normal kerning stays far below this
COVER_SHARE = 0.5  # of the value box
MIN_COVER_AREA = 20.0
SIZE_TOLERANCE = 0.5
LINE_WINDOW = 6
STYLE_SUFFIX = re.compile(
    r"[-,]?(Bold|Italic|Oblique|BoldItalic|BoldOblique|Regular|Roman)+$", re.I
)


@dataclass
class Indicator:
    kind: str
    rule_id: str
    page: int
    box: Box
    page_width: float
    page_height: float
    value: str
    detail: dict[str, Any] = field(default_factory=dict)

    def region(self) -> dict[str, float]:
        def clamp(v: float) -> float:
            return round(min(max(v, 0.0), 1.0), 4)

        return {
            "x": clamp(self.box.x0 / self.page_width),
            "y": clamp(self.box.top / self.page_height),
            "w": clamp((self.box.x1 - self.box.x0) / self.page_width),
            "h": clamp((self.box.bottom - self.box.top) / self.page_height),
        }


RULES = {
    "annotation_over_value": "PDF-ANNOT-OVERLAP",
    "font_differs": "PDF-FONT-DIFF",
    "cover_over_text": "PDF-COVER-TEXT",
    "glyph_overlap": "PDF-GLYPH-OVERLAP",
}


@dataclass(eq=False)
class _Glyph:
    order: int
    ch: LTChar
    box: Box

    @property
    def text(self) -> str:
        return str(self.ch.get_text())


@dataclass(eq=False)
class _Value:
    text: str
    glyphs: list[_Glyph]

    @property
    def box(self) -> Box:
        box = self.glyphs[0].box
        for g in self.glyphs[1:]:
            box = box.union(g.box)
        return box


def _area(box: Box) -> float:
    return max(box.x1 - box.x0, 0.0) * max(box.bottom - box.top, 0.0)


def _overlap(a: Box, b: Box) -> float:
    w = min(a.x1, b.x1) - max(a.x0, b.x0)
    h = min(a.bottom, b.bottom) - max(a.top, b.top)
    return w * h if w > 0 and h > 0 else 0.0


def _family(fontname: str) -> str:
    name = fontname.split("+", 1)[-1]
    return STYLE_SUFFIX.sub("", name) or name


def _is_white(colour: Any, page_colour: Any) -> bool:
    def norm(c: Any) -> tuple[float, ...] | None:
        if c is None:
            return None
        if isinstance(c, (int, float)):
            return (float(c),)
        return tuple(float(x) for x in c)

    got, page = norm(colour), norm(page_colour)
    white = {(1.0,), (1.0, 1.0, 1.0), (0.0, 0.0, 0.0, 0.0)}
    return got is not None and (got in white or got == page)


def _flat(layout: Any) -> Iterator[Any]:
    """Page objects in drawing order, looking inside form XObjects (LTFigure)."""
    for obj in layout:
        if isinstance(obj, LTContainer):
            yield from _flat(obj)
        else:
            yield obj


def _glyphs(layout: Any, height: float) -> tuple[list[_Glyph], list[tuple[int, Box, Any]]]:
    """Glyphs and filled rectangles in drawing order (page space, origin top left)."""
    glyphs: list[_Glyph] = []
    rects: list[tuple[int, Box, Any]] = []
    for order, obj in enumerate(_flat(layout)):
        box = Box(obj.x0, height - obj.y1, obj.x1, height - obj.y0)
        if isinstance(obj, LTChar):
            glyphs.append(_Glyph(order, obj, box))
        elif isinstance(obj, LTRect) and getattr(obj, "fill", False):
            rects.append((order, box, obj.non_stroking_color))
    return glyphs, rects


def _lines(glyphs: list[_Glyph]) -> Iterator[list[_Glyph]]:
    """Glyphs grouped by baseline, left to right."""
    rows: list[list[_Glyph]] = []
    for g in sorted(glyphs, key=lambda g: (-g.ch.y0, g.ch.x0)):
        if rows and abs(rows[-1][0].ch.y0 - g.ch.y0) <= 0.5 * max(g.ch.size, 1.0):
            rows[-1].append(g)
        else:
            rows.append([g])
    for row in rows:
        yield sorted(row, key=lambda g: g.ch.x0)


def _values(line: list[_Glyph]) -> list[_Value]:
    text = ""
    owners: list[_Glyph] = []
    for g in line:
        if owners and g.ch.x0 - owners[-1].ch.x1 > 0.15 * max(g.ch.size, 1.0) and text[-1] != " ":
            text += " "
            owners.append(owners[-1])  # synthetic space keeps indexes aligned
        text += g.text
        owners.append(g)
    out = []
    for m in KEY_VALUE.finditer(text):
        glyphs = [g for g in owners[m.start() : m.end()] if g.text.strip()]
        if glyphs:
            out.append(_Value(m.group(0), list(dict.fromkeys(glyphs))))
    return out


def _annotations(page: Any) -> list[tuple[str, Box]]:
    out = []
    for annot in page.annots:
        subtype = (annot.get("data") or {}).get("Subtype")
        name = str(getattr(subtype, "name", subtype))
        if name in ANNOTATION_SUBTYPES:
            out.append((name, Box(annot["x0"], annot["top"], annot["x1"], annot["bottom"])))
    return out


def _page_colour(rects: list[tuple[int, Box, Any]], width: float, height: float) -> Any:
    for _, box, colour in rects:
        if _area(box) >= 0.9 * width * height:
            return colour
    return (1.0,)


def scan_page(page: Any, number: int) -> list[Indicator]:
    width, height = float(page.width), float(page.height)
    glyphs, rects = _glyphs(page.layout, height)
    colour = _page_colour(rects, width, height)
    values = [v for line in _lines(glyphs) for v in _values(line)]
    found: list[Indicator] = []

    def add(kind: str, box: Box, value: str, **detail: Any) -> None:
        found.append(Indicator(kind, RULES[kind], number, box, width, height, value, detail))

    for subtype, annot in _annotations(page):
        for v in values:
            if _overlap(annot, v.box) > 0:
                add("annotation_over_value", annot, v.text, annotation=subtype)
    for line in _lines(glyphs):
        for v in _values(line):
            others = [g for g in line if g not in v.glyphs and g.text.strip()]
            if len(others) >= 4:
                fams = [_family(g.ch.fontname) for g in others]
                dominant = max(set(fams), key=fams.count)
                sizes = sorted(round(g.ch.size, 1) for g in others)
                size = sizes[len(sizes) // 2]
                v_fam, v_size = _family(v.glyphs[0].ch.fontname), round(v.glyphs[0].ch.size, 1)
                if v_fam != dominant or abs(v_size - size) >= SIZE_TOLERANCE:
                    add(
                        "font_differs",
                        v.box,
                        v.text,
                        value_font=v_fam,
                        value_size=v_size,
                        line_font=dominant,
                        line_size=size,
                    )
    for order, rect, rect_colour in rects:
        if _area(rect) < MIN_COVER_AREA or not _is_white(rect_colour, colour):
            continue
        if _area(rect) >= 0.9 * width * height:
            continue  # the page background itself
        for v in values:
            if all(g.order < order for g in v.glyphs) and _overlap(rect, v.box) >= COVER_SHARE * (
                _area(v.box)
            ):
                add("cover_over_text", rect, v.text)
    boxes = [v.box for v in values]
    for line in _lines(glyphs):
        inked = [g for g in line if g.text.strip()]
        hits: list[Box] = []
        for i, g in enumerate(inked):
            for other in inked[i + 1 : i + 1 + LINE_WINDOW]:
                smaller = min(_area(g.box), _area(other.box))
                if smaller <= 0 or _overlap(g.box, other.box) < OVERLAP_SHARE * smaller:
                    continue
                if any(_overlap(g.box, b) > 0 for b in boxes) or (
                    g.text.isdigit() and other.text.isdigit()
                ):
                    hits.append(g.box.union(other.box))
        for box in _merge(hits):
            near = next((v.text for v in values if _overlap(box, v.box) > 0), "")
            add("glyph_overlap", box, near)
    return found


def _merge(boxes: list[Box]) -> list[Box]:
    """Join boxes that touch or nearly touch, so one value gives one indicator."""
    merged: list[Box] = []
    for box in sorted(boxes, key=lambda b: (b.top, b.x0)):
        last = merged[-1] if merged else None
        if (
            last
            and box.x0 <= last.x1 + 2.0
            and _overlap(Box(last.x0, last.top - 2, last.x1 + 2, last.bottom + 2), box)
        ):
            merged[-1] = last.union(box)
        else:
            merged.append(box)
    return merged


def scan_structure(pdf: bytes) -> list[Indicator]:
    """Indicators for every page; empty when the PDF cannot be opened (other checks say so)."""
    out: list[Indicator] = []
    try:
        with pdfplumber.open(io.BytesIO(pdf)) as doc:
            for number, page in enumerate(doc.pages, start=1):
                out += scan_page(page, number)
    except (
        PdfminerException,
        PSException,
        ValueError,
        OSError,
    ):  # unreadable: the signature checks say so
        return []
    return unique(out)


def unique(items: list[Indicator]) -> list[Indicator]:
    seen: set[tuple[str, int, int, int]] = set()
    out = []
    for item in items:
        key = (item.kind, item.page, round(item.box.x0), round(item.box.top))
        if key not in seen:
            seen.add(key)
            out.append(item)
    return sorted(out, key=lambda i: (i.page, i.box.top, i.box.x0, i.kind))


REASONS = {
    "annotation_over_value": "PDF_ANNOTATION_OVER_VALUE",
    "font_differs": "PDF_FONT_DIFFERS",
    "cover_over_text": "PDF_COVER_OVER_TEXT",
    "glyph_overlap": "PDF_GLYPH_OVERLAP",
}
CONFIDENCE = 0.55  # a commodity heuristic: always the low band


def _describe(ind: Indicator) -> str:
    d = ind.detail
    if ind.kind == "annotation_over_value":
        return f"{d['annotation']} annotation over the value"
    if ind.kind == "font_differs":
        return f"{d['value_font']} {d['value_size']} in a {d['line_font']} {d['line_size']} line"
    if ind.kind == "cover_over_text":
        return "opaque box over text that is still present"
    return "characters drawn on top of each other"


def structure_items(
    indicators: list[Indicator], factory: Any, ruleset: Any
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """(checks, flags) for the indicators; a rule the ruleset does not have is skipped (an older
    archived pack replays without these indicators)."""
    checks: list[dict[str, Any]] = []
    flags: list[dict[str, Any]] = []
    for ind in indicators:
        if ind.rule_id not in ruleset.rules:
            continue
        rule = ruleset[ind.rule_id]
        key = f"{ind.kind}:{ind.page}:{round(ind.box.x0)}:{round(ind.box.top)}"
        region = ind.region()
        flag = factory.make(
            rule.rule_id,
            key,
            page=ind.page,
            regions=[region],
            extracted=ind.value or None,
            expected=None,
            expected_label="no change to the printed value expected",
            confidence=CONFIDENCE,
        )
        flag["check_kind"] = CHECK_KIND
        flag["extracted_source"] = {**flag["extracted_source"], "row": _describe(ind)}
        flags.append(flag)
        checks.append(
            {
                "kind": "format",
                "outcome": rule.label,
                "reason_code": REASONS[ind.kind],
                "evidence": {"page": ind.page, "regions": [region]},
                "check_ref": flag["check_ref"],
            }
        )
    return checks, flags
