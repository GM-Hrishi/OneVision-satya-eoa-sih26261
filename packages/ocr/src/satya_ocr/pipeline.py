"""Read a document: classify pages, OCR the image-only ones, decide whether it can be trusted.

Outcomes (`DocumentRead.status`):
- native    every page has a text layer or is blank: the existing extractors run as before;
- ocr_read  image-only pages were read by OCR above the confidence threshold: the extractors run on
            the OCR text, findings are advisory, and the document is still `manual_review_required`;
- blocked   nothing safe can be decided (reason code and why sentence say why).

OCR text never makes a document `verified` (that stays with signatures and source lookups).
"""

import logging
import time
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeout

import pypdfium2 as pdfium
from PIL import Image

from satya_ocr.config import OcrSettings
from satya_ocr.engine import OcrEngine, OcrWord
from satya_ocr.inspect import PDFIUM_LOCK, inspect_pdf
from satya_ocr.model import DocumentRead, OcrLayer, OcrWordPt, PageRead
from satya_ocr.reasons import reason_for, why_sentence

log = logging.getLogger("satya.ocr")


def render_page(
    data: bytes, index: int, width_pt: float, height_pt: float, s: OcrSettings
) -> Image.Image:
    """Page image at `render_dpi`, downscaled so the longest side is at most `max_render_px`."""
    scale = s.render_dpi / 72
    longest = max(width_pt, height_pt, 1.0) * scale
    if longest > s.max_render_px:
        scale *= s.max_render_px / longest
    with PDFIUM_LOCK:
        doc = pdfium.PdfDocument(data)
        try:
            image: Image.Image = doc[index].render(scale=scale).to_pil().convert("RGB")
            return image
        finally:
            doc.close()


def _layer(words: list[OcrWord], image: Image.Image, page: PageRead) -> OcrLayer:
    """Pixel boxes -> points (origin top left), so evidence regions scale to the page."""
    fx = page.width / image.width
    fy = page.height / image.height
    out = tuple(
        OcrWordPt(w.text, w.box[0] * fx, w.box[1] * fy, w.box[2] * fx, w.box[3] * fy, w.confidence)
        for w in words
        if w.text.strip()
    )
    mean = sum(w.confidence for w in out) / len(out) if out else 0.0
    return OcrLayer(page.width, page.height, out, mean)


def _blocked(
    pages: list[PageRead],
    count: int,
    variant: str,
    settings: OcrSettings | None = None,
    **values: object,
) -> DocumentRead:
    shown = dict(values)
    if settings is not None:
        shown.setdefault("max_pages", settings.max_pages)
    read = DocumentRead(
        "blocked", pages, variant, reason_for(variant), why_sentence(variant, **values), count
    )
    read.values = shown
    return read


def _percent(value: float) -> int:
    return round(value * 100)


def read_document(
    data: bytes, settings: OcrSettings | None = None, engine: OcrEngine | None = None
) -> DocumentRead:
    """Never raises: any failure ends as a blocked read with a reason code."""
    settings = settings or OcrSettings()
    try:
        return _read(data, settings, engine)
    except Exception:
        log.exception("document read failed")
        return _blocked([], 0, "corrupt")


def _read(data: bytes, settings: OcrSettings, engine: OcrEngine | None) -> DocumentRead:
    pages, problem, count = inspect_pdf(data, settings)
    if problem:
        return _blocked(
            pages, count, problem, settings, limit=f"more than {settings.max_pages} pages"
        )
    if all(p.kind == "blank" for p in pages):
        return _blocked(pages, count, "blank")
    scans = [p for p in pages if p.kind == "image_only"]
    if not scans:
        return DocumentRead("native", pages, page_count=count)
    if not settings.enabled:
        return _blocked(pages, count, "scan_not_attempted")
    if engine is None or not engine.available():
        return _blocked(pages, count, "unavailable")

    started = time.monotonic()
    executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="satya-ocr")
    try:
        for page in scans:
            if time.monotonic() - started > settings.doc_timeout_s:
                page.note = "document time limit reached"
                return _blocked(pages, count, "scan_timeout")
            image = render_page(data, page.number - 1, page.width, page.height, settings)
            future = executor.submit(engine.read, image, page_number=page.number)
            try:
                words = future.result(timeout=settings.page_timeout_s)
            except FutureTimeout:
                page.note = "OCR time limit reached"
                return _blocked(pages, count, "scan_timeout")
            except Exception:
                log.exception("OCR engine failed on page %d", page.number)
                page.note = "OCR engine error"
                return _blocked(pages, count, "unavailable")
            page.ocr = _layer(words, image, page)
            if not page.ocr.words:
                page.note = "no text found"
    finally:
        executor.shutdown(wait=False, cancel_futures=True)

    lowest = min(p.ocr.mean_confidence for p in scans if p.ocr)
    if lowest < settings.min_confidence:
        read = _blocked(
            pages,
            count,
            "low_confidence",
            settings,
            confidence=_percent(lowest),
            threshold=_percent(settings.min_confidence),
        )
        read.mean_confidence = lowest
        return read
    numbers = ", ".join(str(p.number) for p in scans)
    label = f"Page {numbers}" if len(scans) == 1 else f"Pages {numbers}"
    why = why_sentence("scan_read", pages=label, confidence=_percent(lowest))
    read = DocumentRead("ocr_read", pages, "scan_read", reason_for("scan_read"), why, count, lowest)
    read.values = {"count": len(scans), "pages": numbers, "confidence": _percent(lowest)}
    return read
