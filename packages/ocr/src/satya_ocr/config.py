"""OCR limits, all settable from the environment (SATYA_OCR_*); the defaults are the safe ones."""

import os
from dataclasses import dataclass


def _num(name: str, default: float) -> float:
    try:
        return float(os.environ.get(name, default))
    except ValueError:
        return default


@dataclass(frozen=True)
class OcrSettings:
    max_pages: int = 50  # pages beyond this are recorded as skipped, never read
    min_text_chars: int = 20  # fewer non-whitespace characters on a page: no usable text layer
    min_confidence: float = 0.80  # mean OCR confidence of a page below this: OCR_LOW_CONFIDENCE
    page_timeout_s: float = 30.0  # per page OCR time limit
    doc_timeout_s: float = 300.0  # per document OCR time limit
    max_render_px: int = 3000  # longest side of a page image sent to the engine (downscaled)
    render_dpi: int = 200
    enabled: bool = True  # False: OCR is not attempted (SCAN_IMAGE_ONLY)

    @classmethod
    def from_env(cls) -> "OcrSettings":
        return cls(
            max_pages=int(_num("SATYA_OCR_MAX_PAGES", cls.max_pages)),
            min_text_chars=int(_num("SATYA_OCR_MIN_TEXT_CHARS", cls.min_text_chars)),
            min_confidence=_num("SATYA_OCR_MIN_CONFIDENCE", cls.min_confidence),
            page_timeout_s=_num("SATYA_OCR_PAGE_TIMEOUT_S", cls.page_timeout_s),
            doc_timeout_s=_num("SATYA_OCR_DOC_TIMEOUT_S", cls.doc_timeout_s),
            max_render_px=int(_num("SATYA_OCR_MAX_RENDER_PX", cls.max_render_px)),
            render_dpi=int(_num("SATYA_OCR_RENDER_DPI", cls.render_dpi)),
            enabled=os.environ.get("SATYA_OCR_ENABLED", "1") not in ("0", "false", "no"),
        )
