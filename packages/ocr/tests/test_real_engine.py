"""The real PaddleOCR engine. Skipped unless the package and the baked models are present."""

import os
from pathlib import Path

import pytest

from satya_ocr import read_document
from satya_ocr.engine import PaddleOcrEngine

engine = PaddleOcrEngine()
pytestmark = pytest.mark.skipif(
    not engine.available(),
    reason="PaddleOCR or its models are not installed here (build the image with WITH_OCR=1, "
    f"models in {os.environ.get('SATYA_OCR_MODEL_DIR', '/opt/ocr-models')}); "
    "see docs/DEMO-CHECKLIST.md",
)


AFFIDAVIT = (
    Path(__file__).resolve().parents[3] / "data/synthetic/cases/dce05-2026-27/affidavit-sworn.pdf"
)


def test_real_engine_reads_a_clean_synthetic_scan():
    from satya_ocr.synth import rasterise

    read = read_document(rasterise(AFFIDAVIT.read_bytes(), dpi=200, skew_deg=0.4), engine=engine)
    assert read.status in ("ocr_read", "blocked")  # confidence decides; never an exception
    first = read.pages[0].ocr
    assert first is not None and first.words
    assert "affidavit" in " ".join(w.text for w in first.words).lower()
