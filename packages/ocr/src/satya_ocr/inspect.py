"""Open a PDF defensively and classify every page as text_layer, image_only, blank or skipped.

Never raises for a bad file: the answer is a variant key (reasons.WHY) saying why it cannot be read.
pdfium is not thread safe, so every pdfium call goes through `PDFIUM_LOCK`.
"""

import io
import logging
import threading

import pikepdf
import pypdfium2 as pdfium

from satya_ocr.config import OcrSettings
from satya_ocr.model import PageKind, PageRead

log = logging.getLogger("satya.ocr")

PDFIUM_LOCK = threading.RLock()
MAX_RECORDED = 1000  # skipped pages recorded one by one; beyond this only the count is kept


def _has_images(page: pikepdf.Page) -> bool:
    try:
        return len(page.get_images()) > 0
    except Exception:
        return False


def inspect_pdf(data: bytes, settings: OcrSettings) -> tuple[list[PageRead], str | None, int]:
    """(pages, problem variant or None, page count). Pages past the cap are `skipped`."""
    try:
        with pikepdf.open(io.BytesIO(data)) as structure:
            count = len(structure.pages)
            images = [_has_images(p) for p in list(structure.pages)[: settings.max_pages]]
    except pikepdf.PasswordError:
        return [], "encrypted", 0
    except Exception:  # pikepdf raises PdfError and several others on broken files
        return [], "corrupt", 0
    if count == 0:
        return [], "no_pages", 0
    pages: list[PageRead] = []
    with PDFIUM_LOCK:
        try:
            doc = pdfium.PdfDocument(data)
        except pdfium.PdfiumError as exc:
            return [], ("encrypted" if "assword" in str(exc) else "corrupt"), count
        except Exception:
            return [], "corrupt", count
        try:
            for index in range(min(count, settings.max_pages)):
                try:
                    page = doc[index]
                    width, height = page.get_size()
                    text = page.get_textpage().get_text_range()
                except Exception:
                    log.warning("page %d unreadable", index + 1)
                    return pages, "corrupt", count
                chars = sum(1 for c in text if not c.isspace())
                kind: PageKind
                if chars >= settings.min_text_chars:
                    kind = "text_layer"
                elif images[index]:
                    kind = "image_only"
                else:
                    kind = "blank"
                pages.append(PageRead(index + 1, kind, chars, float(width), float(height)))
        finally:
            doc.close()
    for number in range(settings.max_pages + 1, min(count, MAX_RECORDED) + 1):
        pages.append(PageRead(number, "skipped", note="beyond the page limit"))
    if count > settings.max_pages:
        return pages, "too_large", count
    return pages, None, count
