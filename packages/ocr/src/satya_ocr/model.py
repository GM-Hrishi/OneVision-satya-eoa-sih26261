"""Result types: per-page classification, the OCR text layer, the document read."""

from dataclasses import dataclass, field
from typing import Any, Literal

PageKind = Literal["text_layer", "image_only", "blank", "skipped"]
ReadStatus = Literal["native", "ocr_read", "blocked"]


@dataclass(frozen=True)
class OcrWordPt:
    """A word in PDF points, origin top left (same frame as pdfplumber)."""

    text: str
    x0: float
    top: float
    x1: float
    bottom: float
    confidence: float


@dataclass(frozen=True)
class OcrLayer:
    """The OCR text layer of one page."""

    width: float  # page size in points
    height: float
    words: tuple[OcrWordPt, ...]
    mean_confidence: float


@dataclass
class PageRead:
    number: int
    kind: PageKind
    chars: int = 0  # non-whitespace characters in the native text layer
    width: float = 0.0
    height: float = 0.0
    ocr: OcrLayer | None = None
    note: str | None = None  # skipped / timeout / no text found

    def summary(self) -> dict[str, Any]:
        out: dict[str, Any] = {"page": self.number, "kind": self.kind, "chars": self.chars}
        if self.ocr is not None:
            out["ocr_confidence"] = round(self.ocr.mean_confidence, 3)
            out["ocr_words"] = len(self.ocr.words)
        if self.note:
            out["note"] = self.note
        return out


@dataclass
class DocumentRead:
    status: ReadStatus
    pages: list[PageRead] = field(default_factory=list)
    variant: str | None = None  # key of the why sentence (reasons.WHY)
    reason_code: str | None = None
    why: str | None = None
    page_count: int = 0
    mean_confidence: float | None = None  # lowest page mean over the OCR pages
    values: dict[str, Any] = field(default_factory=dict)  # numbers for the translated sentence

    @property
    def blocked(self) -> bool:
        return self.status == "blocked"

    @property
    def needs_review(self) -> bool:
        """Scan or unreadable: the document label is `manual_review_required`."""
        return self.reason_code is not None

    def layers(self) -> dict[int, OcrLayer]:
        return {p.number: p.ocr for p in self.pages if p.ocr is not None}

    def summary(self) -> dict[str, Any]:
        """The record stored with the document (ledger) and shown in the case view."""
        return {
            "status": self.status,
            "reason_code": self.reason_code,
            "variant": self.variant,
            "why": self.why,
            "values": self.values,
            "page_count": self.page_count,
            "ocr_mean_confidence": None
            if self.mean_confidence is None
            else round(self.mean_confidence, 3),
            "pages": [p.summary() for p in self.pages],
        }


def to_dict(read: DocumentRead) -> dict[str, Any]:
    """Full record including the OCR words (the stored "OCR text layer")."""
    out = read.summary()
    out["pages"] = [
        {
            **p.summary(),
            "width": p.width,
            "height": p.height,
            "layer": None
            if p.ocr is None
            else {
                "width": p.ocr.width,
                "height": p.ocr.height,
                "mean_confidence": p.ocr.mean_confidence,
                "words": [[w.text, w.x0, w.top, w.x1, w.bottom, w.confidence] for w in p.ocr.words],
            },
        }
        for p in read.pages
    ]
    return out


def from_dict(data: dict[str, Any]) -> DocumentRead:
    pages = []
    for p in data["pages"]:
        layer = p.get("layer")
        pages.append(
            PageRead(
                p["page"],
                p["kind"],
                p.get("chars", 0),
                p.get("width", 0.0),
                p.get("height", 0.0),
                None
                if layer is None
                else OcrLayer(
                    layer["width"],
                    layer["height"],
                    tuple(OcrWordPt(*w) for w in layer["words"]),
                    layer["mean_confidence"],
                ),
                p.get("note"),
            )
        )
    return DocumentRead(
        data["status"],
        pages,
        data["variant"],
        data["reason_code"],
        data["why"],
        data["page_count"],
        data["ocr_mean_confidence"],
        data.get("values", {}),
    )
