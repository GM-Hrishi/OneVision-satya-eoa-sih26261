"""Test support: a FakeOcrEngine that "reads" a scan back from the PDF it was rasterised from."""

import io

import pdfplumber

from satya_ocr.engine import FakeOcrEngine, OcrWord


def fake_from_source_pdf(source: bytes, confidence: float = 0.93) -> FakeOcrEngine:
    """Known text and boxes: the words of `source`, scaled to whatever image size is asked for."""
    pages = []
    with pdfplumber.open(io.BytesIO(source)) as pdf:
        for page in pdf.pages:
            words = page.extract_words(x_tolerance=1.5, y_tolerance=2)
            pages.append((float(page.width), float(page.height), words))

    def read(image, number):  # type: ignore[no-untyped-def]
        width, height, words = pages[number - 1]
        fx, fy = image.width / width, image.height / height
        return [
            OcrWord(
                w["text"], (w["x0"] * fx, w["top"] * fy, w["x1"] * fx, w["bottom"] * fy), confidence
            )
            for w in words
        ]

    return FakeOcrEngine(read)
