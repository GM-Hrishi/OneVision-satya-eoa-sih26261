import io
import time

import pikepdf
import pytest
from conftest import blank_pdf, image_pdf, text_pdf, words

from satya_ocr import (
    DOC_UNREADABLE,
    OCR_LOW_CONFIDENCE,
    OCR_UNAVAILABLE,
    SCAN_IMAGE_ONLY,
    FakeOcrEngine,
    OcrSettings,
    read_document,
)
from satya_ocr.reasons import WHY, why_sentence
from satya_ocr.synth import rasterise


def kinds(read):
    return [p.kind for p in read.pages]


def test_text_pdf_is_native():
    read = read_document(text_pdf(3))
    assert read.status == "native" and kinds(read) == ["text_layer"] * 3
    assert read.reason_code is None and not read.needs_review


def test_image_only_pages_are_classified():
    read = read_document(image_pdf(2), engine=FakeOcrEngine([words(0.95)]))
    assert kinds(read) == ["image_only", "image_only"]


def test_scan_read_by_ocr_is_still_manual_review():
    engine = FakeOcrEngine([words(0.95)])
    read = read_document(image_pdf(2), engine=engine)
    assert read.status == "ocr_read" and read.reason_code == SCAN_IMAGE_ONLY
    assert read.mean_confidence == pytest.approx(0.95)
    assert read.needs_review and "read by OCR (confidence 95%)" in (read.why or "")
    assert read.values == {"count": 2, "pages": "1, 2", "confidence": 95}
    assert all(p.ocr and len(p.ocr.words) == 12 for p in read.pages)


def test_boxes_are_scaled_to_page_points():
    read = read_document(image_pdf(1), engine=FakeOcrEngine([words(0.9)]))
    page, layer = read.pages[0], read.pages[0].ocr
    assert layer is not None
    first = layer.words[0]
    assert 0 <= first.x0 < first.x1 <= page.width and 0 <= first.top < first.bottom <= page.height


def test_low_confidence_blocks():
    read = read_document(image_pdf(1), engine=FakeOcrEngine([words(0.55)]))
    assert read.blocked and read.reason_code == OCR_LOW_CONFIDENCE
    assert "55%" in (read.why or "") and "80%" in (read.why or "")
    assert read.values["confidence"] == 55 and read.values["threshold"] == 80
    assert read.pages[0].ocr is not None  # the confidence is kept for the case view


@pytest.mark.parametrize(("conf", "blocked"), [(0.79, True), (0.80, False), (0.81, False)])
def test_threshold_boundary(conf, blocked):
    read = read_document(image_pdf(1), engine=FakeOcrEngine([words(conf)]))
    assert read.blocked is blocked


def test_threshold_is_configurable():
    read = read_document(
        image_pdf(1), OcrSettings(min_confidence=0.5), FakeOcrEngine([words(0.55)])
    )
    assert read.status == "ocr_read"


def test_page_with_no_words_is_low_confidence():
    read = read_document(image_pdf(1), engine=FakeOcrEngine([[]]))
    assert read.reason_code == OCR_LOW_CONFIDENCE and read.pages[0].note == "no text found"


def test_worst_page_decides():
    read = read_document(image_pdf(2), engine=FakeOcrEngine([words(0.95), words(0.6)]))
    assert read.reason_code == OCR_LOW_CONFIDENCE


def test_no_engine_is_unavailable():
    assert read_document(image_pdf(1)).reason_code == OCR_UNAVAILABLE
    gone = FakeOcrEngine([], is_available=False)
    assert read_document(image_pdf(1), engine=gone).reason_code == OCR_UNAVAILABLE


def test_ocr_not_attempted_when_disabled():
    engine = FakeOcrEngine([words(0.95)])
    read = read_document(image_pdf(1), OcrSettings(enabled=False), engine)
    assert read.reason_code == SCAN_IMAGE_ONLY and read.variant == "scan_not_attempted"
    assert engine.calls == []


def test_engine_error_falls_back():
    read = read_document(image_pdf(1), engine=FakeOcrEngine([], error=RuntimeError("boom")))
    assert read.blocked and read.reason_code == OCR_UNAVAILABLE


def test_page_timeout_falls_back():
    engine = FakeOcrEngine([words(0.95)], delay_s=0.6)
    started = time.monotonic()
    read = read_document(image_pdf(1), OcrSettings(page_timeout_s=0.1), engine)
    assert time.monotonic() - started < 0.5
    assert read.blocked and read.variant == "scan_timeout" and read.reason_code == SCAN_IMAGE_ONLY


def test_document_timeout_falls_back():
    engine = FakeOcrEngine([words(0.95)], delay_s=0.2)
    read = read_document(image_pdf(3), OcrSettings(doc_timeout_s=0.1), engine)
    assert read.variant == "scan_timeout"


def test_mixed_pdf():
    mixed = rasterise(text_pdf(3), only_pages={2})
    engine = FakeOcrEngine([words(0.93)])
    read = read_document(mixed, engine=engine)
    assert kinds(read) == ["text_layer", "image_only", "text_layer"]
    assert read.status == "ocr_read" and len(engine.calls) == 1 and engine.calls[0][0] == 2
    assert sorted(read.layers()) == [2] and "Page 2 read" in (read.why or "")


def test_mixed_pdf_without_engine_never_skips_the_scanned_page():
    read = read_document(rasterise(text_pdf(2), only_pages={1}))
    assert read.blocked and read.reason_code == OCR_UNAVAILABLE


def test_encrypted_pdf():
    pdf = pikepdf.open(io.BytesIO(text_pdf(1)))
    buf = io.BytesIO()
    pdf.save(buf, encryption=pikepdf.Encryption(user="s3cret", owner="owner"))
    read = read_document(buf.getvalue())
    assert read.blocked and read.reason_code == DOC_UNREADABLE and read.variant == "encrypted"


@pytest.mark.parametrize(
    "data",
    [
        b"",
        b"%PDF-1.7\n%%EOF",
        b"not a pdf at all",
        text_pdf(1)[:300],
        b"%PDF-1.4\n" + b"\x00" * 500,
    ],
)
def test_corrupt_inputs_never_raise(data):
    read = read_document(data)
    assert read.blocked and read.reason_code == DOC_UNREADABLE


def test_zero_pages():
    pdf = pikepdf.new()
    buf = io.BytesIO()
    pdf.save(buf)
    read = read_document(buf.getvalue())
    assert read.blocked and read.variant == "no_pages"


def test_only_blank_pages():
    read = read_document(blank_pdf(3))
    assert read.blocked and read.variant == "blank" and kinds(read) == ["blank"] * 3


def test_blank_pages_in_a_text_document_are_fine():
    pdf = pikepdf.open(io.BytesIO(text_pdf(1)))
    pdf.add_blank_page(page_size=(595, 842))
    buf = io.BytesIO()
    pdf.save(buf)
    read = read_document(buf.getvalue())
    assert read.status == "native" and kinds(read) == ["text_layer", "blank"]


def test_page_cap_records_skipped_pages():
    read = read_document(text_pdf(5), OcrSettings(max_pages=3))
    assert read.blocked and read.reason_code == DOC_UNREADABLE and read.variant == "too_large"
    assert kinds(read) == ["text_layer"] * 3 + ["skipped"] * 2
    assert read.page_count == 5 and "3 pages" in (read.why or "")


def test_huge_page_is_downscaled_before_ocr():
    engine = FakeOcrEngine([words(0.95)])
    read = read_document(image_pdf(1, size=(9000, 12000)), engine=engine)
    assert read.status == "ocr_read"
    assert max(engine.calls[0][1]) <= OcrSettings().max_render_px


def test_ocr_never_yields_a_verified_state():
    for engine in (FakeOcrEngine([words(1.0)]), FakeOcrEngine([words(0.2)]), None):
        read = read_document(image_pdf(1), engine=engine)
        assert read.needs_review and read.reason_code in {
            SCAN_IMAGE_ONLY,
            OCR_LOW_CONFIDENCE,
            OCR_UNAVAILABLE,
        }


def test_every_variant_has_a_sentence_without_unfilled_placeholders():
    values = {"pages": "Page 1", "confidence": 90, "threshold": 80, "limit": "more than 50 pages"}
    for variant in WHY:
        sentence = why_sentence(variant, **values)
        assert "{" not in sentence and "—" not in sentence and sentence.endswith(".")


def test_summary_is_json_ready():
    import json

    read = read_document(image_pdf(1), engine=FakeOcrEngine([words(0.9)]))
    assert json.loads(json.dumps(read.summary()))["pages"][0]["ocr_confidence"] == 0.9
