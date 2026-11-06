"""Text addressed to automated readers (T7): the `ai_reader_text` indicator.

Finds lines in the text layer (including white, tiny or off-page text) that address an AI or other
automated reader, with page, box and a short HTML-escaped snippet. The same lines are dropped by
every reading path (satya_ocr.aimask), so a planted line adds this indicator and changes nothing
else. SATYA ignores the text; it is never passed to any model or classifier.
"""

import io
from typing import Any

import pdfplumber
from pdfminer.psparser import PSException
from pdfplumber.utils.exceptions import PdfminerException

from satya_forensics.structure import CHECK_KIND, Indicator, _glyphs, _lines, scan_page, unique
from satya_forensics.textlayer import Box
from satya_ocr.aimask import ai_line_flags, snippet

RULE_ID = "AI-READER-TEXT"
REASON = "AI_READER_TEXT"
CONFIDENCE = 0.9  # the phrase match is exact; what it means is for a person to judge


def scan_ai_page(page: Any, number: int) -> list[Indicator]:
    width, height = float(page.width), float(page.height)
    glyphs, _ = _glyphs(page.layout, height)
    rows = [row for row in _lines(glyphs) if any(g.text.strip() for g in row)]
    texts = ["".join(g.text for g in row) for row in rows]
    out: list[Indicator] = []
    for row, text, bad in zip(rows, texts, ai_line_flags(texts), strict=True):
        if not bad:
            continue
        box: Box = row[0].box
        for g in row[1:]:
            box = box.union(g.box)
        out.append(Indicator("ai_reader_text", RULE_ID, number, box, width, height, snippet(text)))
    return out


def scan_pdf(pdf: bytes, with_structure: bool) -> tuple[list[Indicator], list[Indicator]]:
    """(structure indicators, text-for-readers indicators), reading the PDF once. Both are empty
    when the file cannot be opened; the signature checks report that."""
    structure: list[Indicator] = []
    ai: list[Indicator] = []
    try:
        with pdfplumber.open(io.BytesIO(pdf)) as doc:
            for number, page in enumerate(doc.pages, start=1):
                if with_structure:
                    structure += scan_page(page, number)
                ai += scan_ai_page(page, number)
    except (PdfminerException, PSException, ValueError, OSError):
        return [], []
    return unique(structure), ai


def scan_ai_text(pdf: bytes) -> list[Indicator]:
    return scan_pdf(pdf, with_structure=False)[1]


def ai_text_items(
    indicators: list[Indicator], factory: Any, ruleset: Any
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """(checks, flags); skipped when the ruleset (an older archived pack) has no such rule."""
    if RULE_ID not in ruleset.rules:
        return [], []
    rule = ruleset[RULE_ID]
    checks: list[dict[str, Any]] = []
    flags: list[dict[str, Any]] = []
    for ind in indicators:
        key = f"ai_reader_text:{ind.page}:{round(ind.box.x0)}:{round(ind.box.top)}"
        region = ind.region()
        flag = factory.make(
            RULE_ID,
            key,
            page=ind.page,
            regions=[region],
            extracted=ind.value,
            expected=None,
            expected_label="no text addressed to automated readers expected",
            confidence=CONFIDENCE,
        )
        flag["check_kind"] = CHECK_KIND
        flags.append(flag)
        checks.append(
            {
                "kind": "format",
                "outcome": rule.label,
                "reason_code": REASON,
                "evidence": {"page": ind.page, "regions": [region]},
                "check_ref": flag["check_ref"],
            }
        )
    return checks, flags
