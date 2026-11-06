"""T6: heuristic PDF structure indicators. Fixtures are tiny synthetic PDFs built here."""

import io

import pikepdf
import pytest
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from satya_forensics.structure import CHECK_KIND, scan_structure

DATE = "14 Aug 2026"
LABEL = "Date of notarisation:"
TAIL = "recorded in the register."


def build(draw) -> bytes:  # type: ignore[no-untyped-def]
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    draw(c)
    c.showPage()
    c.save()
    return buf.getvalue()


def line(
    c: canvas.Canvas, y: float = 700, value_font=("Helvetica", 11), charspace: float = 0.0
) -> None:  # type: ignore[no-untyped-def]
    """'Date of notarisation: 14 Aug 2026 recorded in the register.' as three runs on one line."""
    c.setFont("Helvetica", 11)
    c.drawString(72, y, LABEL)
    x = 72 + c.stringWidth(LABEL + " ", "Helvetica", 11)
    c.setFont(*value_font)
    t = c.beginText(x, y)
    t.setFont(*value_font)
    t.setCharSpace(charspace)
    t.textOut(DATE)
    c.drawText(t)
    x2 = x + c.stringWidth(DATE + " ", *value_font) + charspace * (len(DATE) + 1)
    c.setFont("Helvetica", 11)
    c.drawString(x2, y, TAIL)


def clean(c: canvas.Canvas) -> None:
    line(c)
    c.drawString(72, 650, "Land area declared: 6.20 acres as per the registered deed.")


def annotate(pdf: bytes, subtype: str, rect: list[float]) -> bytes:
    with pikepdf.open(io.BytesIO(pdf)) as doc:
        annot = doc.make_indirect(
            pikepdf.Dictionary(
                Type=pikepdf.Name.Annot,
                Subtype=pikepdf.Name(f"/{subtype}"),
                Rect=rect,
                Contents=pikepdf.String("note"),
            )
        )
        doc.pages[0].Annots = doc.make_indirect(pikepdf.Array([annot]))
        out = io.BytesIO()
        doc.save(out)
        return out.getvalue()


def kinds(pdf: bytes) -> list[str]:
    return [i.kind for i in scan_structure(pdf)]


# rectangle over the date: x from about 160 to 225, y 696 to 712 (PDF space)
OVER_DATE = [150.0, 695.0, 260.0, 712.0]
ELSEWHERE = [300.0, 300.0, 340.0, 320.0]


def test_clean_control_gives_no_indicator() -> None:
    assert scan_structure(build(clean)) == []


@pytest.mark.parametrize("subtype", ["FreeText", "Square", "Highlight", "Stamp"])
def test_annotation_over_a_date_is_an_indicator(subtype: str) -> None:
    out = scan_structure(annotate(build(clean), subtype, OVER_DATE))
    hit = [i for i in out if i.kind == "annotation_over_value"]
    assert len(hit) == 1 and hit[0].value == DATE and hit[0].detail["annotation"] == subtype
    assert hit[0].rule_id == "PDF-ANNOT-OVERLAP" and hit[0].page == 1
    region = hit[0].region()
    assert 0 < region["w"] < 0.5 and 0 < region["y"] < 0.5


def test_annotations_that_do_not_trigger() -> None:
    assert scan_structure(annotate(build(clean), "FreeText", ELSEWHERE)) == []
    assert scan_structure(annotate(build(clean), "Link", OVER_DATE)) == []  # a link is not a note


def test_value_in_another_font_family_is_an_indicator() -> None:
    out = scan_structure(build(lambda c: line(c, value_font=("Times-Roman", 11))))
    hit = [i for i in out if i.kind == "font_differs"]
    assert len(hit) == 1 and hit[0].value == DATE
    assert hit[0].detail["value_font"] == "Times" and hit[0].detail["line_font"] == "Helvetica"


def test_value_in_another_size_is_an_indicator_and_bold_alone_is_not() -> None:
    out = scan_structure(build(lambda c: line(c, value_font=("Helvetica", 14))))
    assert [i.kind for i in out] == ["font_differs"]
    assert out[0].detail["value_size"] == 14.0 and out[0].detail["line_size"] == 11.0
    assert scan_structure(build(lambda c: line(c, value_font=("Helvetica-Bold", 11)))) == []


def white_box_after(c: canvas.Canvas) -> None:
    clean(c)
    c.setFillColorRGB(1, 1, 1)
    c.rect(150, 695, 110, 17, stroke=0, fill=1)


def test_white_box_drawn_over_text_that_is_still_there() -> None:
    out = scan_structure(build(white_box_after))
    hit = [i for i in out if i.kind == "cover_over_text"]
    assert len(hit) == 1 and hit[0].value == DATE and hit[0].rule_id == "PDF-COVER-TEXT"


def test_boxes_that_do_not_trigger() -> None:
    def white_box_before(c: canvas.Canvas) -> None:  # a background behind the text
        c.setFillColorRGB(1, 1, 1)
        c.rect(150, 695, 110, 17, stroke=0, fill=1)
        c.setFillColorRGB(0, 0, 0)
        clean(c)

    def yellow_box_after(c: canvas.Canvas) -> None:  # a highlighter box is not opaque white
        clean(c)
        c.setFillColorRGB(1, 1, 0)
        c.rect(150, 695, 110, 17, stroke=0, fill=1)

    def white_page_background(c: canvas.Canvas) -> None:
        c.setFillColorRGB(1, 1, 1)
        c.rect(0, 0, 595, 842, stroke=0, fill=1)
        c.setFillColorRGB(0, 0, 0)
        clean(c)

    for draw in (white_box_before, yellow_box_after, white_page_background):
        assert scan_structure(build(draw)) == [], draw.__name__


def test_page_colour_box_counts_as_a_cover() -> None:
    def cream(c: canvas.Canvas) -> None:
        c.setFillColorRGB(0.98, 0.96, 0.90)
        c.rect(0, 0, 595, 842, stroke=0, fill=1)
        c.setFillColorRGB(0, 0, 0)
        clean(c)
        c.setFillColorRGB(0.98, 0.96, 0.90)
        c.rect(150, 695, 110, 17, stroke=0, fill=1)

    assert [i.kind for i in scan_structure(build(cream))] == ["cover_over_text"]


def test_characters_drawn_on_top_of_each_other() -> None:
    out = scan_structure(build(lambda c: line(c, charspace=-5.0)))
    hit = [i for i in out if i.kind == "glyph_overlap"]
    assert len(hit) == 1 and hit[0].rule_id == "PDF-GLYPH-OVERLAP"
    assert scan_structure(build(lambda c: line(c, charspace=0.5))) == []  # wide spacing is fine


def test_the_same_digits_printed_twice_are_an_overlap() -> None:
    def twice(c: canvas.Canvas) -> None:
        clean(c)
        c.drawString(72, 600, "Application 1-90000004217")
        c.drawString(72.5, 600, "Application 1-90000004217")

    assert "glyph_overlap" in kinds(build(twice))


def test_unreadable_bytes_give_no_indicator_and_no_error() -> None:
    assert scan_structure(b"not a pdf") == []


def test_indicators_are_deterministic_and_marked_heuristic() -> None:
    pdf = annotate(build(white_box_after), "FreeText", OVER_DATE)
    first, second = scan_structure(pdf), scan_structure(pdf)
    assert [(i.kind, i.page, i.value, i.box) for i in first] == [
        (i.kind, i.page, i.value, i.box) for i in second
    ]
    assert CHECK_KIND == "heuristic"


# ---- through the M6 engine ----------------------------------------------------------------------
def test_engine_emits_heuristic_flags_that_only_route_to_manual_review() -> None:
    from dataclasses import replace

    from satya_forensics.engine import AFFIDAVIT_SLOT
    from satya_forensics.labels import document_label
    from satya_forensics.synth.variants import build_case
    from satya_shared_types import validator

    from .conftest import run_case

    case = build_case(7, "clean")
    clean_result = run_case(case)
    assert not [f for f in clean_result.flags if f["rule_id"].startswith("PDF-")]  # control

    affidavit = next(d for d in case.case["documents"] if d["slot"] == AFFIDAVIT_SLOT)
    original = case.files[affidavit["file"]]
    assert scan_structure(original) == []  # the synthetic copy itself raises nothing
    marked = annotate(original, "FreeText", [0.0, 0.0, 595.0, 842.0])
    case = replace(case, files={**case.files, affidavit["file"]: marked})
    result = run_case(case)
    flags = [f for f in result.flags if f["rule_id"].startswith("PDF-")]
    assert flags and all(f["check_kind"] == "heuristic" for f in flags)
    assert all(f["label"] == "manual_review_required" for f in flags)
    assert all(f["severity"] in ("warning", "info") and f["preliminary_indicator"] for f in flags)
    assert all(f["regions"] and f["page"] for f in flags)
    for f in flags:
        assert [e.message for e in validator("Flag").iter_errors(f)] == []
    doc = next(d for d in result.documents if d.slot == AFFIDAVIT_SLOT)
    structure_checks = [
        c for c in doc.verification["checks"] if c["reason_code"].startswith("PDF_")
    ]
    assert structure_checks and {c["outcome"] for c in structure_checks} == {
        "manual_review_required"
    }
    # the structure checks alone never produce mismatch_detected
    assert document_label(structure_checks) == "manual_review_required"
