"""Text-layer extraction (pdfplumber): words with strike-through state, lines, ruled tables.

Slice 1 reads the PDF text layer only; scanned pages (no text layer) are reported, and OCR
arrives with M3 (P-2). Positions are kept so every finding can point at its page region (Portal
spec §2.6.4).
"""

import io
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

import pdfplumber

from satya_ocr.model import OcrLayer

STRIKE_MIN = 0.3  # a strike line crosses a glyph between 30 % and 80 % of its height (from the top)
STRIKE_MAX = 0.8
LINE_TOLERANCE = 2.0
TABLE_SETTINGS = {
    "vertical_strategy": "lines",
    "horizontal_strategy": "lines",
    "snap_tolerance": 3,
    "intersection_tolerance": 3,
}


class ExtractionError(ValueError):
    """The bytes are not a readable PDF (DOC_UNREADABLE)."""


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

    def contains_point(self, x: float, y: float) -> bool:
        return self.x0 - 0.5 <= x <= self.x1 + 0.5 and self.top - 0.5 <= y <= self.bottom + 0.5


@dataclass(frozen=True)
class Word:
    text: str  # characters that are not struck through
    raw: str  # every character
    box: Box
    struck_chars: int

    @property
    def fully_struck(self) -> bool:
        return self.struck_chars >= len(self.raw)


@dataclass
class Line:
    page: int
    words: list[Word]

    @property
    def box(self) -> Box:
        box = self.words[0].box
        for w in self.words[1:]:
            box = box.union(w.box)
        return box

    @property
    def text(self) -> str:
        """Kept text: struck-through characters removed."""
        return " ".join(w.text for w in self.words if w.text)

    @property
    def raw(self) -> str:
        return " ".join(w.raw for w in self.words)

    @property
    def struck(self) -> int:
        return sum(1 for w in self.words if w.struck_chars)


@dataclass
class Table:
    page: int
    box: Box
    rows: list[list[str | None]]
    row_boxes: list[Box]


@dataclass
class Page:
    number: int
    width: float
    height: float
    lines: list[Line] = field(default_factory=list)
    tables: list[Table] = field(default_factory=list)

    def region(self, box: Box) -> dict[str, float]:
        """Region normalised to 0..1 (Portal spec §2.6.4)."""

        def clamp(v: float) -> float:
            return round(min(max(v, 0.0), 1.0), 4)

        return {
            "x": clamp(box.x0 / self.width),
            "y": clamp(box.top / self.height),
            "w": clamp((box.x1 - box.x0) / self.width),
            "h": clamp((box.bottom - box.top) / self.height),
        }


@dataclass
class Extracted:
    pages: list[Page]
    text_layer_pages: int
    ocr_pages: dict[int, float] = field(default_factory=dict)  # page number -> mean OCR confidence

    @property
    def page_count(self) -> int:
        return len(self.pages)


def _strike_lines(page: Any, tables: list[Box]) -> list[Box]:
    candidates = [*page.lines, *(r for r in page.rects if r["height"] < 1.2)]
    found = []
    for item in candidates:
        if abs(item["bottom"] - item["top"]) > 1.2 or item["x1"] - item["x0"] < 2:
            continue
        box = Box(item["x0"], item["top"], item["x1"], item["bottom"])
        mid_y = (box.top + box.bottom) / 2
        if any(
            t.contains_point(box.x0 + 1, mid_y) and t.contains_point(box.x1 - 1, mid_y)
            for t in tables
        ):
            continue  # table rule
        found.append(box)
    return found


def _is_struck(char: dict[str, Any], strikes: list[Box]) -> bool:
    cx = (char["x0"] + char["x1"]) / 2
    height = char["bottom"] - char["top"]
    for s in strikes:
        y = (s.top + s.bottom) / 2
        if s.x0 - 0.5 <= cx <= s.x1 + 0.5 and (
            char["top"] + STRIKE_MIN * height <= y <= char["top"] + STRIKE_MAX * height
        ):
            return True
    return False


def _lines(page_no: int, words: list[Word]) -> list[Line]:
    lines: list[Line] = []
    for word in sorted(words, key=lambda w: (round(w.box.top, 1), w.box.x0)):
        if lines and abs(lines[-1].words[0].box.top - word.box.top) <= LINE_TOLERANCE:
            lines[-1].words.append(word)
        else:
            lines.append(Line(page_no, [word]))
    for line in lines:
        line.words.sort(key=lambda w: w.box.x0)
    return lines


def _ocr_words(layer: OcrLayer) -> list[Word]:
    """OCR words as extractor words (no strike-through information on a scan)."""
    return [
        Word(w.text, w.text, Box(w.x0, w.top, w.x1, w.bottom), 0)
        for w in layer.words
        if w.text.strip()
    ]


def extract(data: bytes, ocr: Mapping[int, OcrLayer] | None = None) -> Extracted:
    """Words, lines and ruled tables per page. Pages with no text layer take their words from the
    OCR layer when one is given; tables are not read from OCR pages (no ruled-line geometry)."""
    try:
        pdf = pdfplumber.open(io.BytesIO(data))
    except Exception as exc:  # pdfminer raises several types for broken files
        raise ExtractionError("not a readable PDF") from exc
    pages: list[Page] = []
    text_pages = 0
    ocr_pages: dict[int, float] = {}
    with pdf:
        for number, page in enumerate(pdf.pages, start=1):
            found = page.find_tables(table_settings=TABLE_SETTINGS)
            table_boxes = [Box(*t.bbox) for t in found]
            strikes = _strike_lines(page, table_boxes)
            words: list[Word] = []
            for w in page.extract_words(
                x_tolerance=1.5, y_tolerance=2, keep_blank_chars=False, return_chars=True
            ):
                box = Box(w["x0"], w["top"], w["x1"], w["bottom"])
                cx, cy = (box.x0 + box.x1) / 2, (box.top + box.bottom) / 2
                if any(t.contains_point(cx, cy) for t in table_boxes):
                    continue
                chars = w["chars"]
                struck = [_is_struck(c, strikes) for c in chars]
                kept = "".join(c["text"] for c, s in zip(chars, struck, strict=True) if not s)
                words.append(Word(kept, w["text"], box, sum(struck)))
            if not words and not found and ocr and number in ocr:
                words = _ocr_words(ocr[number])
                if words:
                    ocr_pages[number] = ocr[number].mean_confidence
            if words or found:
                text_pages += 1
            tables = [
                Table(number, Box(*t.bbox), t.extract(), [Box(*r.bbox) for r in t.rows])
                for t in found
            ]
            pages.append(
                Page(number, float(page.width), float(page.height), _lines(number, words), tables)
            )
    return Extracted(pages=pages, text_layer_pages=text_pages, ocr_pages=ocr_pages)
