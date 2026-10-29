"""M3 OCR with scan fallback (B-28): classify pages, never crash, read scans, else manual review."""

from satya_ocr.config import OcrSettings
from satya_ocr.engine import FakeOcrEngine, OcrEngine, OcrWord
from satya_ocr.model import DocumentRead, OcrLayer, PageRead
from satya_ocr.pipeline import read_document
from satya_ocr.reasons import (
    DOC_UNREADABLE,
    OCR_LOW_CONFIDENCE,
    OCR_UNAVAILABLE,
    REASON_CODES,
    SCAN_IMAGE_ONLY,
    why_sentence,
)

__all__ = [
    "DOC_UNREADABLE",
    "OCR_LOW_CONFIDENCE",
    "OCR_UNAVAILABLE",
    "REASON_CODES",
    "SCAN_IMAGE_ONLY",
    "DocumentRead",
    "FakeOcrEngine",
    "OcrEngine",
    "OcrLayer",
    "OcrSettings",
    "OcrWord",
    "PageRead",
    "read_document",
    "why_sentence",
]
