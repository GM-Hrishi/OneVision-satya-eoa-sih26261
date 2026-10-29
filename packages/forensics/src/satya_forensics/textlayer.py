"""Text-layer reading for M6: printed signature marks, the stamp page, the notary block, UDINs.

Text layer only (pdfplumber), like M5. Raster marks and scanned stamp pages need OCR (M3, P-2);
until then such a page yields nothing and the checks that depend on it say so instead of guessing.
"""

import io
import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any

import pdfplumber

from satya_ocr.model import OcrLayer

MARK_PHRASES = (
    re.compile(r"digitally\s+signed\s+by", re.I),
    re.compile(r"signature\s+valid", re.I),
)
# Adobe-style appearance date: "Date: 2026.11.24 10:15:02 +05'30'"
MARK_DATE = re.compile(
    r"Date:\s*(\d{4})\.(\d{2})\.(\d{2})\s+(\d{2}):(\d{2}):(\d{2})\s*([+-])(\d{2})'?(\d{2})'?"
)
MARK_SIGNER = re.compile(r"Digitally\s+signed\s+by\s+(.+)", re.I)
MARK_GAP = 48.0  # points: lines closer than this belong to one mark


@dataclass(frozen=True)
class Box:
    x0: float
    top: float
    x1: float
    bottom: float

    def union(self, other: "Box") -> "Box":
        return Box(
            min(self.x0, other.x0),
            min(self.top, other.top),
            max(self.x1, other.x1),
            max(self.bottom, other.bottom),
        )

    def intersects(self, other: "Box") -> bool:
        return not (
            self.x1 <= other.x0
            or other.x1 <= self.x0
            or self.bottom <= other.top
            or other.bottom <= self.top
        )


@dataclass
class Page:
    number: int
    width: float
    height: float
    text: str
    lines: list[tuple[str, Box]] = field(default_factory=list)
    from_ocr: bool = False  # the lines were read by OCR, not taken from a text layer

    def region(self, box: Box) -> dict[str, float]:
        def clamp(v: float) -> float:
            return round(min(max(v, 0.0), 1.0), 4)

        return {
            "x": clamp(box.x0 / self.width),
            "y": clamp(box.top / self.height),
            "w": clamp((box.x1 - box.x0) / self.width),
            "h": clamp((box.bottom - box.top) / self.height),
        }

    def find(self, pattern: re.Pattern[str]) -> list[tuple[re.Match[str], Box]]:
        return [(m, box) for text, box in self.lines for m in [pattern.search(text)] if m]


@dataclass(frozen=True)
class Mark:
    """A printed signature mark found in the text layer."""

    page: int
    box: Box
    text: str
    signer: str | None
    signed_at: datetime | None


def _ocr_lines(layer: OcrLayer) -> list[tuple[str, Box]]:
    """Group OCR words into lines (same row within a few points), left to right."""
    rows: list[list[Any]] = []
    for w in sorted(layer.words, key=lambda w: (w.top, w.x0)):
        if rows and abs(rows[-1][0].top - w.top) <= 3.0:
            rows[-1].append(w)
        else:
            rows.append([w])
    out = []
    for row in rows:
        row.sort(key=lambda w: w.x0)
        box = Box(
            min(w.x0 for w in row),
            min(w.top for w in row),
            max(w.x1 for w in row),
            max(w.bottom for w in row),
        )
        out.append((" ".join(w.text for w in row), box))
    return out


def read_pages(pdf: bytes, ocr: Mapping[int, OcrLayer] | None = None) -> list[Page]:
    """Lines per page from the text layer; pages with none take the OCR layer when one is given."""
    pages = []
    with pdfplumber.open(io.BytesIO(pdf)) as doc:
        for number, p in enumerate(doc.pages, start=1):
            lines = []
            for line in p.extract_text_lines(return_chars=False):
                box = Box(line["x0"], line["top"], line["x1"], line["bottom"])
                lines.append((" ".join(line["text"].split()), box))
            from_ocr = False
            if not lines and ocr and number in ocr:
                lines = _ocr_lines(ocr[number])
                from_ocr = True
            text = "\n".join(t for t, _ in lines)
            pages.append(Page(number, float(p.width), float(p.height), text, lines, from_ocr))
    return pages


def _mark_date(text: str) -> datetime | None:
    m = MARK_DATE.search(text)
    if not m:
        return None
    y, mo, d, hh, mm, ss, sign, oh, om = m.groups()
    offset = timedelta(hours=int(oh), minutes=int(om)) * (1 if sign == "+" else -1)
    try:
        return datetime(int(y), int(mo), int(d), int(hh), int(mm), int(ss), tzinfo=timezone(offset))
    except ValueError:
        return None


def find_marks(pages: list[Page]) -> list[Mark]:
    """Group lines that carry a mark phrase (and the date line next to them) into marks."""
    marks: list[Mark] = []
    for page in pages:
        hits = [
            (text, box)
            for text, box in page.lines
            if any(p.search(text) for p in MARK_PHRASES) or MARK_DATE.search(text)
        ]
        groups: list[list[tuple[str, Box]]] = []
        for text, box in sorted(hits, key=lambda h: h[1].top):
            if groups and box.top - groups[-1][-1][1].bottom < MARK_GAP:
                groups[-1].append((text, box))
            else:
                groups.append([(text, box)])
        for group in groups:
            joined = "\n".join(t for t, _ in group)
            if not any(p.search(joined) for p in MARK_PHRASES):
                continue  # a lone date line is not a mark
            box = group[0][1]
            for _, other in group[1:]:
                box = box.union(other)
            signer_match = MARK_SIGNER.search(joined)
            marks.append(
                Mark(
                    page=page.number,
                    box=box,
                    text=joined,
                    signer=signer_match.group(1).strip() if signer_match else None,
                    signed_at=_mark_date(joined),
                )
            )
    return marks
